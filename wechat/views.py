import logging
log = logging.getLogger('django')
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib import auth
from datetime import datetime
from accounts.models import Token, User
from wechat.models import Requirement, Location, LocationHis
import hashlib
import json
import xmltodict
from django.core.cache import caches
from django.conf import settings
from django.http import HttpResponse
import os, re
from wechatpy.utils import check_signature, WeChatSigner
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.replies import TextReply
from wechatpy import create_reply
from django.views.decorators.csrf import csrf_exempt
from wechatpy.enterprise import WeChatClient,parse_message
from wechatpy.enterprise.exceptions import InvalidCorpIdException
import geopy.distance
from wechat.utils import timesince
import functools

WECHAT_TOKEN = os.environ.get('WECHAT_TOKEN')
AES_KEY = os.environ.get('WECHAT_AES_KEY')
APPID = os.environ.get('WECHAT_APPID')
SECRET = os.environ.get('WECHAT_SECRET')
AGENTID = os.environ.get('AGENTID')
def oauth(method):
    @functools.wraps(method)
    def warpper(request, *args, **kwargs):
        client = WeChatClient(APPID, SECRET)
        code = request.GET.get('code', None)
        url = client.oauth.authorize_url(request.build_absolute_uri())
        if not code:
            return method(request, *args, **kwargs)
        try:
            user_info = client.oauth.get_user_info(code)
            userid = user_info.get('UserId')
            user_dict = client.user.get(userid)
            userpk = user_dict.get('email') or user_dict.get('userid')
            # user = User.objects.filter(email=userpk).first()
        except Exception as e:
            log.error('>>>Exception of oauth,errmsg:{},errcode:{}'.format(e.errmsg, e.errcode))
            # 这里需要处理请求里包含的 code 无效的情况
            return method(request, *args, **kwargs)
        if not userpk:
            return method(request, *args, **kwargs)
        
        if request.user.is_authenticated and request.user.email == userpk:
            log.debug('>>>auth logged in already, user.email:{}'.format(userpk))
            return method(request, *args, **kwargs)
        else:
            log.debug('>>>auth not login user_info:{}'.format(userpk))
            user, created = User.objects.update_or_create(
                email=userpk, 
                defaults=weixin_user_to_model(user_dict, client)
            )
            token = Token.objects.filter(email=userpk).first()
            if not token:
                token = Token.objects.create(email=userpk)
            user = auth.authenticate(uid=token)
            if user:
                auth.login(request, user)
                return redirect(url)

        return method(request, *args, **kwargs)

    return warpper

@csrf_exempt
def interface(request):
    msg_signature = request.GET.get('msg_signature', '')
    signature = request.GET.get('signature', msg_signature)
    timestamp = request.GET.get('timestamp', '')
    nonce = request.GET.get('nonce', '')
    echostr = request.GET.get('echostr', '')
    crypto = WeChatCrypto(WECHAT_TOKEN, AES_KEY, APPID)
    if request.method == 'GET':
        signer = WeChatSigner()
        signer.add_data(WECHAT_TOKEN, timestamp, nonce)
        log.debug('>>> Signatrue:{},get:{},body:{}'.format(signer.signature, request.GET, request.body))
        try:
            echostr = crypto.check_signature(
                signature,
                timestamp,
                nonce,
                echostr
            )
        except InvalidSignatureException as e:
            log.error('>>> SignatrueException:{},get:{},body:{}'.format(e, request.GET, request.body))
            return HttpResponse('')
        return HttpResponse(echostr)


    # 处理POST请求
    try:
        decrypted_xml = crypto.decrypt_message(
            request.body,
            msg_signature,
            timestamp,
            nonce
        )
    except (InvalidCorpIdException, InvalidSignatureException):
        # to-do: 处理异常或忽略
        log.error('>>> Decrypt message exception,get:{},body:{}'.format(request.GET, request.body))
        return HttpResponse('Decrypt message exception')

    xml = response_message(decrypted_xml, request)
    encrypted_xml = crypto.encrypt_message(xml, nonce, timestamp)
    response = HttpResponse(encrypted_xml, content_type="application/xml")
    return response
    # 明文请求
    # xml = response_message(request.body, request)
    # response = HttpResponse(xml, content_type="application/xml")
    # return response

def response_message(xml, request=None):
    msg = parse_message(xml)
    log.debug('>>> source:{},target:{}, msg.type:{}'.format(msg.source, msg.target, msg.type))
    client = WeChatClient(APPID, SECRET)
    user_dict = client.user.get(msg.source)
    userpk = user_dict.get('email') or user_dict.get('userid')
    user = User.objects.filter(email=userpk).first()
    # client.message.send_text( msg.agent ,msg.source, 'user:{}'.format(user))
    # log.debug('>>> user:{}'.format(user))
    if msg.type == 'text':
        if re.match(r'.*(想)|(建议)',msg.content):
            Requirement.objects.get_or_create(email=userpk,content=msg.content)
            req_counts = Requirement.objects.filter(email=userpk).count()
            reply = TextReply(content='您的想法和建议我们已经收到（{}）'.format(req_counts), message=msg)
            return reply.render()
        content = '''现在我还不会聊天
但我会记录您提出的想法和建议
试着输入“...想...”或“...建议...” '''

        reply = TextReply(content=content, message=msg)
        return reply.render()
        # log.debug('>>> response:{}'.format(response))
    elif msg.type == 'event':
        log.debug('>>> msg.event:{}'.format( msg.event))
        if msg.event == 'subscribe': 
            return login_url(request, user_dict, client, userpk)
        if msg.event == 'location':
            log.debug('>>> msg:{}'.format( msg))
            return add_location(user, msg.id, msg.latitude, msg.longitude, msg.precision )
        if msg.event == 'click':
            log.debug('>>> msg.key:{}'.format( msg.key))
            if msg.key == 'login':
                return login_url(request, user_dict, client, userpk)
            elif msg.key == 'get_available_cars':
                return get_available_cars(user)
            elif msg.key == 'my_location_his':
                return get_location_his(user)
    elif msg.type == 'location':
        return add_location(user, msg.id, msg.location_x, msg.location_y, msg.scale, msg.label)

    reply = create_reply('')
    return reply.render()

def add_location(user, msgid, location_x, location_y, scale, label=''):
    if user:
        location = { 
            'msgid': msgid,
            'user': user,
            'latitude': location_x,
            'longitude': location_y,
            'precision': scale,
            'label': label,
        }
        Location.objects.update_or_create(user=user, defaults=location)
        if msgid:
            LocationHis.objects.get_or_create(msgid=msgid, defaults=location)
        log.debug('>>> add location')
        log.debug('>>> msgid:{},label_len:{},x:{},y{},s{}'.format(msgid, len(label), location_x, location_y,scale))
    reply = create_reply('')
    return reply.render()

def get_location_his(user):
    if user:
        my_location = Location.objects.filter(user=user).order_by('-updated_at').first()
        content = ''
        coords_me = ( my_location.latitude, my_location.longitude)
        for l in LocationHis.objects.filter(user=user).order_by('-created_at')[:5]:
            content += '\n{}您在{:.3f}km{}'.format(
                timesince(l.created_at),
                geopy.distance.vincenty(coords_me,(l.latitude, l.longitude)).km,
                l.label,
            ) 
        log.debug('>>> get_location_his')
        log.debug(content)

        reply = create_reply(content)
        return reply.render()
    reply = create_reply('')
    return reply.render()


def get_available_cars(user):
    if user:
        my_location = Location.objects.filter(user=user).order_by('-updated_at').first()
        content = ''
        coords_me = ( my_location.latitude, my_location.longitude)
        for l in Location.objects.filter(user__car_seats_left__gt=0).order_by('-updated_at'):
            content += '\n{}{}距您{:.3f}km{}，车牌尾号:{}有{:.1f}个座位可用，联系电话{}'.format(
                l.user.display_name,
                timesince(l.updated_at),
                geopy.distance.vincenty(coords_me,(l.latitude, l.longitude)).km,
                l.label,
                l.user.car_no[-4:],
                l.user.car_seats_left,
                l.user.telephone
            ) 
        log.debug('>>> available cars')
        log.debug(content)

        if not content:
            content = '没有找到任何可用车辆信息'
        reply = create_reply(
            '周围车辆：'+content
        )
        return reply.render()
    reply = create_reply('')
    return reply.render()


def weixin_user_to_model(user_dict, client):
    defaults={
        'display_name': user_dict.get('name'),
        'avatar': user_dict.get('avatar'),
    }
    user_depts = user_dict.get('department')
    log.debug('>>> user_depts:{}'.format(user_depts))
    if user_depts:
        departments = client.department.get()
        log.debug('>>> departments_number:{}'.format(len(departments)))
        if departments:
            department = next((d for d in departments if d.get('id') in user_depts))
            if department:
                defaults.update({'depart_name': department.get('name')})
    return defaults

def login_url(request, user_dict, client, userpk):
    User.objects.update_or_create(email=userpk, defaults=weixin_user_to_model(user_dict, client))
    token = Token.objects.filter(email=userpk).first()
    if not token:
        token = Token.objects.create(email=userpk)
    url = request.build_absolute_uri(
        reverse('login') + '?token=' + str(token.uid)
    )
    reply = create_reply(
        '如果尚未登录凑单吧，请点击下面的链接登录（在页面顶部将显示您的姓名和头像）\n{}'.format(url)
    )
    return reply.render()
 
