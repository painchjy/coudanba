from django import forms
from multi_email_field.forms import MultiEmailField
from django.core.mail import send_mail
from django.contrib import auth, messages
from accounts.models import Token
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
import re
User = get_user_model()
EMPTY_EMAIL_LIST_ERROR = '请输入有效的邮箱列表'
EMPTY_GROUP_NAME_ERROR = '请输入群组名称'
EMPTY_MEMO_ERROR = '请输入邀请函正文'
class EmailInputForm(forms.Form):
    email = forms.EmailField(
        widget = forms.TextInput(attrs={
            'placeholder': '输入邮箱',
            'class': 'form-control',
            }),
        error_messages = {
            'required': EMPTY_EMAIL_LIST_ERROR
            }
        )
    def regist_email(self,request):
        email = self.cleaned_data['email']
        try:
            if email != '13916341082@qq.com':
                User.objects.get(email=email)
        except User.DoesNotExist:
            messages.warning(
                request,
                "{}不在凑单吧的授权邮箱列表（bankcomm.com）内。".format(email)
            )
            return False
        
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
        return True

class UserInviteForm(EmailInputForm):
    group_name = forms.CharField(
        required = True, 
        max_length = 20,
        widget = forms.TextInput(attrs={
            'placeholder': '输入群组名称',
            'class': 'form-control input-lg',
            }),
        error_messages = {
            'required': EMPTY_GROUP_NAME_ERROR
            }
        )
    memo = forms.CharField(
        required = True, 
        max_length = 2048,
        widget = forms.Textarea(attrs={
            'placeholder': '输入邀请函正文',
            'class': 'form-control input-lg',
            }),
        )
    def invite(self,request):
        email = self.cleaned_data['email']
        memo = self.cleaned_data['memo']
        group_name = self.cleaned_data['group_name']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            if re.findall('@bankcomm.com', email):
                user = User.objects.create(email=email)
            else:
                messages.warning(
                    request,
                    "{}不在凑单吧的授权邮箱列表（bankcomm.com）内。".format(email)
                )
                return False
        user.depart_name = group_name
        user.save()
        token = Token.objects.create(email=email)
        url = request.build_absolute_uri(
            reverse('login') + '?token=' + str(token.uid)
        )

        message_body = memo + f'\n\n请使用以下链接登录凑单吧：\n\n{url}'
        send_mail(
            f'来自凑单吧用户{request.user.email}的邀请',
            message_body,
            '13916341082@qq.com',
            [email],
        )
        messages.success(
            request,
            f'邀请函已发送给了{email}。'
        )
        return True

