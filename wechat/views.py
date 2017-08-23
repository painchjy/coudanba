import logging
log = logging.getLogger('django')
from django.shortcuts import render
from django.core.urlresolvers import reverse
from datetime import datetime
from accounts.models import Token
import hashlib
import json
import xmltodict
from django.core.cache import caches
from django.conf import settings
from django.http import HttpResponse
import os
from wechatpy.utils import check_signature, WeChatSigner
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.replies import TextReply
from django.views.decorators.csrf import csrf_exempt
from wechatpy.enterprise import WeChatClient,parse_message
from wechatpy.enterprise.exceptions import InvalidCorpIdException

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
    try:
        signer = WeChatSigner()
        signer.add_data(WECHAT_TOKEN, timestamp, nonce)
        log.debug('>>> Signatrue:{},get:{},body:{}'.format(signer.signature, request.GET, request.body))
        if echostr:
            echostr = crypto.check_signature(
                signature,
                timestamp,
                nonce,
                echostr
            )
        else:
            pass
            # check_signature(
            #     WECHAT_TOKEN,
            #     signature,
            #     timestamp,
            #     nonce
            # )

    except InvalidSignatureException as e:
        log.error('>>> SignatrueException:{},get:{},body:{}'.format(e, request.GET, request.body))
        return HttpResponse('')
    if request.method == 'GET':
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
    fromUserName = msg.source
    toUserName = msg.target
    log.debug('>>> source:{},target:{},openid:{}, msg:{}'.format(fromUserName, toUserName,request.GET.get('openid'), msg))
    client = WeChatClient(APPID, SECRET)
    user = client.user.get(msg.source)
    # client.message.send_text( msg.agent ,msg.source, 'user:{}'.format(user))
    # log.debug('>>> user:{}'.format(user))
    if msg.type == 'text':
        reply = TextReply(content=msg.content, message=msg)
        # log.debug('>>> response:{}'.format(response))
    elif msg.type == 'event':
        if msg.event == 'click' and msg.key == 'login':
            email = user.get('email')
            if email:
                token = Token.objects.create(email=user.email)
                url = request.build_absolute_uri(
                    reverse('login') + '?token=' + str(token.uid)
                )
            else:
                url = '请让管理员设置号您的email后再登'
            reply = TextReply(content=url, message=msg)
    return reply.render()

