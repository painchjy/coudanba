import logging
log = logging.getLogger('django')
from django.shortcuts import render
from django.core.urlresolvers import reverse
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
from django.views.decorators.csrf import csrf_exempt
from wechatpy.enterprise import WeChatClient,parse_message
from wechatpy.enterprise.exceptions import InvalidCorpIdException
import geopy.distance
from wechat.utils import timesince

WECHAT_TOKEN = os.environ.get('WECHAT_TOKEN')
AES_KEY = os.environ.get('WECHAT_AES_KEY')
APPID = os.environ.get('WECHAT_APPID')
SECRET = os.environ.get('WECHAT_SECRET')
AGENTID = os.environ.get('AGENTID')
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
    log.debug('>>> source:{},target:{}, msg:{}'.format(msg.source, msg.target, msg))
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
        reply = TextReply(content=msg.content, message=msg)
        # log.debug('>>> response:{}'.format(response))
    elif msg.type == 'event':
        if msg.event == 'subscribe' or (msg.event == 'click' and msg.key == 'login'):
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

            User.objects.update_or_create(email=userpk, defaults=defaults)
            token = Token.objects.filter(email=userpk).first()
            if not token:
                token = Token.objects.create(email=userpk)
            url = request.build_absolute_uri(
                reverse('login') + '?token=' + str(token.uid)
            )
            reply = TextReply(
                content='如果尚未登录凑单吧，请点击下面的链接登录（在页面顶部将显示您的姓名和头像）\n{}'.format(url), 
                message=msg
            )
    elif msg.type == 'location':
        if user:
            location = { 
                'msgid': msg.id,
                'user': user,
                'latitude': msg.location_x,
                'longitude': msg.location_y,
                'precision': msg.scale,
                'label': msg.label,
            }
            Location.objects.update_or_create(user=user, defaults=location)
            LocationHis.objects.update_or_create(msgid=msg.id, defaults=location)
            content = ''
            coords_me = ( msg.location_x, msg.location_y)
            for l in Location.objects.all().order_by('-created_at'):
                content += '\n{}{}在{},距离{:.3f}km'.format(
                    l.user.display_name,
                    timesince(l.create_at),
                    l.label,
                    geopy.distance.vincenty(coords_me,(l.latitude, l.longitude)).km,
                ) 
            log.debug('>>> source:{},target:{}, msg:{}'.format(msg.source, msg.target, content))

            reply = TextReply(
                content='周围同事：'+content,
                message=msg
            )


    return reply.render()

