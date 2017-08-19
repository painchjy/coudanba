from django.shortcuts import render
from datetime import datetime
import hashlib
import json
import xmltodict
from django.core.cache import caches
from django.conf import settings
from django.http import HttpResponse
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException

WECHAT_TOKEN = 'testwechatbyzjh'
def check(request):
    signature = request.GET.get('signature', '')
    timestamp = request.GET.get('timestamp', '')
    nonce = request.GET.get('nonce', '')
    echostr = request.GET.get('echostr', '')

    try:
        check_signature(WECHAT_TOKEN, signature, timestamp, nonce)
    except InvalidSignatureException:
        # 处理异常情况或忽略
        print('>>> {},{}'.format(request.GET, '验证异常'))
        # return '验证异常'
        return 'Shutting down...'
    else:
        print('>>> {},{}'.format(request.GET, '验证ok'))
        return HttpResponse(echostr)
