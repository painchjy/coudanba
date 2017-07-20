from django.shortcuts import render, redirect
from django.contrib import auth, messages
from accounts.forms import EmailInputForm, UserInviteForm
from django.contrib.auth import get_user_model
User = get_user_model()



def login(request):
    user = auth.authenticate(uid=request.GET.get('token'))
    if user:
        auth.login(request, user)

    return redirect('/')


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
