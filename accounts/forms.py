from django import forms
from django.core.mail import send_mail
from django.contrib import auth, messages
from accounts.models import Token
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
import re
User = get_user_model()
EMPTY_ITEM_ERROR = "户名和部门都不可为空"
TOO_LONG_ERROR = "输入太多了"
EMPTY_EMAIL_LIST_ERROR = '请输入有效的邮箱列表'
EMPTY_GROUP_NAME_ERROR = '请输入群组名称'
EMPTY_MEMO_ERROR = '请输入邀请函正文'
EMPTY_ERROR = '输入文本不可为空'
class EmailInputForm(forms.Form):
    email = forms.EmailField(
        widget = forms.TextInput(attrs={
            'placeholder': '输入邮箱',
            'class': 'form-control input-sm',
            }),
        error_messages = {
            'required': EMPTY_EMAIL_LIST_ERROR
            }
        )
    def regist_email(self,request):
        email = self.cleaned_data['email']
        try:
            if email not in ['13916341082@qq.com','13916341082@163.com','painchjy@gmail.com','yyt030@163.com']:
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
        message_body = f'请使用以下链接登录凑单吧：\n\n Click Login URL below:\n\n{url}'
        send_mail(
            'Login URL from www.coudanba.cn',
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
            'class': 'form-control input-sm',
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
            'class': 'form-control input-sm',
            }),
        )
    def invite(self,request):
        email = self.cleaned_data['email']
        memo = self.cleaned_data['memo']
        group_name = self.cleaned_data['group_name']
        if group_name == request.user.depart_name:
            memo = memo + '作为{}的成员，{}将可以代你在凑单吧下单，如对此邮件有疑问，请联系您的邀请人。'.format(group_name,request.user.display_name)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            if re.findall('@bankcomm.com', email):
                user = User.objects.create(email=email, display_name=email.split('@')[0])
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

class WeChatRegistForm(forms.Form):
    openid = forms.CharField(
        required = True, 
        max_length = 120,
        label = "微信openid",
        widget = forms.TextInput(attrs={
            'placeholder': '输入openid',
            'class': 'form-control input-sm',
            }),
        error_messages = {
            'required': EMPTY_ERROR
            }
        )
    depart_name = forms.CharField(
        required = True, 
        max_length = 20,
        label = "所属部门",
        widget = forms.TextInput(attrs={
            'placeholder': '输入部门名称',
            'class': 'form-control input-sm',
            }),
        error_messages = {
            'required': EMPTY_ERROR
            }
        )
    group_name = forms.CharField(
        required = True, 
        max_length = 20,
        label = "公众号名称",
        widget = forms.TextInput(attrs={
            'placeholder': '输入公众号名称',
            'class': 'form-control input-sm',
            }),
        error_messages = {
            'required': EMPTY_ERROR
            }
        )
    display_name = forms.CharField(
        required = True, 
        max_length = 220,
        label = "群内备注或昵称",
        widget = forms.TextInput(attrs={
            'placeholder': '输入群内备注或昵称',
            'class': 'form-control input-sm',
            }),
        error_messages = {
            'required': EMPTY_ERROR
            }
        )
    def regist_wechat(self,request):
        openid = self.cleaned_data['openid']
        display_name = self.cleaned_data['display_name']
        group_name = self.cleaned_data['group_name']
        depart_name = self.cleaned_data['depart_name']
       
        user, created = User.objects.update_or_create(
                email=openid, 
                defaults={
                    'display_name': display_name, 
                    'depart_name': depart_name,
                    'group_name': group_name
                }
            )
        token = Token.objects.create(email=openid)
        url = request.build_absolute_uri(
            reverse('login') + '?token=' + str(token.uid)
        )
        messages.success(
            request,
            "登录链接已返回。"
        )
        return {'login_url': url, 'openid': openid, 'group_name': group_name }


class UserForm(forms.models.ModelForm):
    class Meta:
        model = User
        fields = ['display_name','depart_name']
        widgets = {
            'display_name': forms.fields.TextInput(attrs={
                'placeholder': '输入格式建议：昵称（移动短号）',
                'class': 'form-control input-md', 
            }),
            'depart_name': forms.fields.TextInput(attrs={
                'placeholder': '可以输入所属部门名称或自建群组名称',
                'class': 'form-control input-md', 
            }),
        }
        error_messages = {
                'depart_name': {'required': EMPTY_ITEM_ERROR,'max_length': TOO_LONG_ERROR },
                'display_name': {'required': EMPTY_ITEM_ERROR,'max_length': TOO_LONG_ERROR }
        }
        labels = {
                'depart_name': '群组名称(缺省为部门名称，可以新建群组)',
                'display_name': '账户名称',
        }
    
#    def __init__(self, *args, **kwargs):
#        user = kwargs.pop('user', None)
#        self.instance = user
#        super().__init__(*args, **kwargs)



