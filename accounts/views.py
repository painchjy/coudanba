from django.shortcuts import render, redirect
from django.contrib import auth, messages
from accounts.forms import EmailInputForm, UserInviteForm, UserForm, WeChatRegistForm
from jus.models import Location
from django.contrib.auth import get_user_model
from django.http import JsonResponse
User = get_user_model()


def login(request):
    user = auth.authenticate(uid=request.GET.get('token'))
    if user:
        auth.login(request, user)

    return redirect('/')

def wechat_regist(request):
    if not request.user.is_authenticated:
        return redirect('/')
    if not request.user.is_admin():
        return redirect('/')
    form = WeChatRegistForm()
    if request.method == 'POST':
        form = WeChatRegistForm(data=request.POST)
        if form.is_valid():
            json = form.regist_wechat(request)
            if json:
                return JsonResponse(json)
    if form.errors:
        messages.warning(
            request,
            form.errors['openid']
        )
    return render(request, 'wechat_regist.html', { 'form': form })

def send_login_email(request):
    form = EmailInputForm()
    if request.method == 'POST':
        form = EmailInputForm(data=request.POST)
        if form.is_valid():
            form.regist_email(request)
    if form.errors:
        messages.warning(
            request,
            form.errors['email']
        )
    return redirect('/')

def user_invite(request):
    form = UserInviteForm()
    memo = '凑单吧用户{}邀请您加入{}一起凑单，活动内容可以用下面的链接登录查看。\n\n'
    form.fields['memo'].initial = memo.format(request.user.email, request.user.depart_name)
    form.fields['group_name'].initial = request.user.depart_name
    if request.method == 'POST':
        form = UserInviteForm(data=request.POST)
        if form.is_valid():
            form.invite(request)
    return render(request, 'user_invite.html', { 'form': form, 'owner': request.user})

def profile(request):
    form = UserForm(instance=request.user)
    if request.method == 'POST':
        form = UserForm(instance=request.user, data=request.POST)
        if form.is_valid():
            form.save()
    return render(request, 'profile.html', { 'form': form, 'locations': Location.objects.all()})
