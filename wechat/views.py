import logging
log = logging.getLogger('django')
from django.shortcuts import render
from datetime import datetime
import hashlib
import json
import xmltodict
from django.core.cache import caches
from django.conf import settings
from django.http import HttpResponse
import os
from wechatpy import parse_message
from wechatpy.utils import check_signature
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.replies import TextReply
from django.views.decorators.csrf import csrf_exempt
from wechatpy import WeChatClient

WECHAT_TOKEN = os.environ.get('WECHAT_TOKEN')
AES_KEY = os.environ.get('WECHAT_AES_KEY')
APPID = os.environ.get('WECHAT_APPID')
SECRET = os.environ.get('WECHAT_SECRET')
@csrf_exempt
def interface(request):
    signature = request.GET.get('signature', '')
    timestamp = request.GET.get('timestamp', '')
    nonce = request.GET.get('nonce', '')
    echostr = request.GET.get('echostr', '')
    try:
        check_signature(WECHAT_TOKEN, signature, timestamp, nonce)
    except InvalidSignatureException:
        # 处理异常情况或忽略
        log.error('>>> get:{},body:{}'.format(request.GET, request.body))
        return HttpResponse('')
    if request.method == 'GET':
        return HttpResponse(echostr)


    # 处理POST请求
    msg_signature = request.GET.get('msg_signature', '')
    encrypt_type = request.GET.get('encrypt_type', '')
    if encrypt_type == 'aes':
        # 密文请求
        crypto = WeChatCrypto(WECHAT_TOKEN, AES_KEY, APPID)
        try:
            decrypted_xml = crypto.decrypt_message(
                request.body,
                msg_signature,
                timestamp,
                nonce
            )
        except (InvalidAppIdException, InvalidSignatureException):
            # to-do: 处理异常或忽略
            log.error('>>> Decrypt message exception,get:{},body:{}'.format(request.GET, request.body))
            return HttpResponse('Decrypt message exception')

        xml = response_message(decrypted_xml)
        encrypted_xml = crypto.encrypt_message(xml, nonce, timestamp)
        response = HttpResponse(encrypted_xml, content_type="application/xml")
        return response
    else:
        # 明文请求
        xml = response_message(request.body)
        response = HttpResponse(xml, content_type="application/xml")
        return response

def response_message(xml):
    msg = parse_message(xml)
    client = WeChatClient(APPID, SERET)
    user = client.user.get('opj8uwus6Flhf5G-KujGPNDHNbJI')
    client.message.send_text('opj8uwus6Flhf5G-KujGPNDHNbJI', 'user:{}'.format(user))
    log.debug('>>> user:{}'.format(user))
    reply = TextReply(content=msg.content, message=msg)
    # response = HttpResponse(reply.render(), content_type="application/xml")
    
    # log.debug('>>> response:{}'.format(response))
    return reply.render()

