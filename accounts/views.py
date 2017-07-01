from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import auth, messages
from accounts.models import Token
from django.core.urlresolvers import reverse

def login(request):
    user = auth.authenticate(uid=request.GET.get('token'))
    if user:
        auth.login(request, user)

    return redirect('/')

def send_login_email(request):
    email = request.POST['email']
    token = Token.objects.create(email=email)
    url = request.build_absolute_uri(
        reverse('login') + '?token=' + str(token.uid)
    )
    message_body = f'请使用以下链接登录聚一聚：\n\n{url}'
    send_mail(
            '聚一聚的登录链接',
            message_body,
            'painchjy@gmail.com',
            [email],
    )
    messages.success(
        request,
        "登录链接已发送，请检查你的邮箱。"
    )
    return redirect('/')
