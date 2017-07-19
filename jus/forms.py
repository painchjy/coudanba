from django import forms
from lists.models import Item as ListItem, List
from jus.models import Ju, Item
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
        fields = ('content','stop_date_time')
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': '#@!@#$$%%#',
                'class': 'form-control input-lg',
            }),
            'stop_date_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'input_formats':["%Y-%M-%D %H:%M%"],
                'class': 'input-group date',
            }),
        }
        labels = {
            'content': '活动内容：',
            'stop_date_time': '截止时间：',
        }
        error_messages = {
            'content': {'required': EMPTY_ITEM_ERROR },
            'stop_date_time':{'invalid': '日期格式:YYYY-MM-DD HH:MM'}
        }

    def save(self, owner=None, ju=None):
        item_text=self.cleaned_data['content']
        stop_date_time = self.cleaned_data['stop_date_time']
        if ju:
            ju.content = item_text
            ju.stop_date_time = stop_date_time
        else:
            ju =Ju(content=item_text, owner=owner, stop_date_time=stop_date_time)    
        if ju.parse_content():
            ju.save()
            for k, v in ju.sorted_items_:
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
                item.save()
            return ju
        self.add_error('content', JU_FORMAT_ERROR)

    def load_users(self):

        f = self.cleaned_data['content']
        for line in f.splitlines():
            row = line.split(';')
            user, created = User.objects.update_or_create(
                email=row[0],
                defaults={'depart_name': row[1]},
            )

