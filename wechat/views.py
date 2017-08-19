from django.shortcuts import render
from datetime import datetime
import hashlib
import json
import xmltodict
from django.core.cache import caches
from django.conf import settings
from django.http import HttpResponse
from wechatpy.replies import TextReply
from wechatpy.utils import to_text


WECHAT_TOKEN = 'testwechatbyzjh'
def check(request):
    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    echostr = request.args.get('echostr', '')

    try:
        check_signature(WECHAT_TOKEN, signature, timestamp, nonce)
    except InvalidSignatureException:
        # 处理异常情况或忽略
        print('>>> {},{}'.format(request.args, '验证异常'))
        # return '验证异常'
        return 'Shutting down...'
    else:
        print('>>> {},{}'.format(request.args, '验证ok'))
        return echostr
