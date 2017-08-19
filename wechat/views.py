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
WECHAT_TOKEN = os.environ.get('WECHAT_TOKEN')
#AES_KEY = os.environ.get('AES_KEY')
#APPID = os.environ.get('APPID')
def interface(request):
    if request.method='GET':
        return get(request)
    else:
        return post(request)
def post(request):
    signature = request.POST.get('signature', '')
    timestamp = request.POST.get('timestamp', '')
    nonce = request.POST.get('nonce', '')

    msg_signature = request.POST.get('msg_signature', '')
    encrypt_type = request.POST.get('encrypt_type', '')
    try:
        check_signature(WECHAT_TOKEN, signature, timestamp, nonce)
    except InvalidSignatureException:
        # 处理异常情况或忽略
        #print('>>> {},{}'.format(request.args, '验证异常'))
        # return '验证异常'
        return 'Shutting down...'
    request_msg = parse_message(request.POST)
    reply = TextReply(content='{}'.format(request_msg.content), message=request_msg)
    return reply.render()

def get(request):
    signature = request.GET.get('signature', '')
    timestamp = request.GET.get('timestamp', '')
    nonce = request.GET.get('nonce', '')
    echostr = request.GET.get('echostr', '')

    try:
        check_signature(WECHAT_TOKEN, signature, timestamp, nonce)
    except InvalidSignatureException:
        # 处理异常情况或忽略
        return 'Shutting down...'
    else:
        return HttpResponse(echostr)
