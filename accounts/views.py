from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import auth, messages
from accounts.models import Token
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
User = get_user_model()

def login(request):
    user = auth.authenticate(uid=request.GET.get('token'))
    if user:
        auth.login(request, user)

    return redirect('/')

def send_login_email(request):
    email = request.POST['email']
    try:
        User.objects.get(email=email)
    except User.DoesNotExist:
        messages.success(
            request,
            "{}不在凑单吧的授权邮箱列表（bankcomm.com）内。".format(email)
        )
        return redirect('/')

        
    token = Token.objects.create(email=email)
    url = request.build_absolute_uri(
        reverse('login') + '?token=' + str(token.uid)
    )
    message_body = f'请使用以下链接登录凑单吧：\n\n{url}'
    send_mail(
            '凑单吧的登录链接',
            message_body,
            '13916341082@qq.com',
            [email],
    )
    messages.success(
        request,
        "登录链接已发送，请检查你的邮箱。"
    )
    return redirect('/')
