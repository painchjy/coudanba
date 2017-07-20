from django import forms
from lists.models import Item as ListItem, List
from jus.models import Ju, Item, STATUS_CHOICES
from django.core.exceptions import ValidationError
import shlex
import re
import json
from django.contrib.auth import get_user_model
import csv
User = get_user_model()

EMPTY_ITEM_ERROR = "You can't have an empty list item"
JU_FORMAT_ERROR = "管理凑单活动太复杂了"
TOO_LONG_ERROR = "输入太多了"

class JuItemForm(forms.models.ModelForm):

    class Meta:
        model = Ju
        fields = ('items','stop_date_time','status','address','ju_type')
        widgets = {
            'address': forms.fields.TextInput(attrs={
                'placeholder': '可以输入活动地点和要求',
                'class': 'form-control input-lg',
            }),
            'items': forms.Textarea(attrs={
                'placeholder': '#@!@#$$%%#',
                'class': 'form-control input-lg',
            }),
            'stop_date_time': forms.DateTimeInput(attrs={
                'input_formats':["%Y-%m-%d %H:%M","%Y-%m-%dT%H:%M","%Y-%m-%d %H:%M:%S"],
                'class': 'form-control',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
            'ju_type': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        labels = {
            'address': '活动说明：',
            'items': '活动项目：',
            'stop_date_time': '截止时间：',
            'status': '状态：',
            'ju_type': '活动类型：',
        }
        error_messages = {
            'address': {'required': EMPTY_ITEM_ERROR },
            'items': {'required': EMPTY_ITEM_ERROR , 'invalid': JU_FORMAT_ERROR},
            'stop_date_time':{'invalid': '日期格式:YYYY-MM-DD HH:MM'}
        }

    def save(self, owner=None, ju=None):
        if not ju:
            ju =Ju(owner=owner)    
        ju.address = self.cleaned_data['address']
        ju.items = self.cleaned_data['items']
        ju.stop_date_time = self.cleaned_data['stop_date_time']
        ju.status = self.cleaned_data['status']
        ju.ju_type = self.cleaned_data['ju_type']
        if owner:
            ju.owner = owner
        ju.save()
        for k, v in ju.sorted_items:
            item = ju.item_set.filter(key=k).first()
            if item:
                if item.price != float(v['price']):
                    item.price = float(v['price'])
                    ListItem.objects.filter(list__ju=ju, text__istartswith=k).update(price=item.price)
            else:
                item = Item(ju=ju, key=k)

            try:
                item.__dict__.update(v)
            except Exception as e:
                print('-----------Exception for updating JuItem:{}'.format(e))
                self.add_error('items', 'Update Item Error:{}'.format(e))
                return
            item.save()
        return ju

class UsersForm(forms.models.ModelForm):
    class Meta:
        model = Ju
        fields = ['content',]
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': '#@!@#$$%%#',
                'class': 'form-control input-lg',
            }),
        }
    def load_users(self):

        f = self.cleaned_data['content']
        for line in f.splitlines():
            row = line.split(';')
            user, created = User.objects.update_or_create(
                email=row[0],
                defaults={'depart_name': row[1]},
            )

