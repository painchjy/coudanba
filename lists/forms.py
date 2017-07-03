from django import forms
from lists.models import Item, List, Ju
from django.core.exceptions import ValidationError
import shlex
import re
import json
from django.contrib.auth import get_user_model
import csv
User = get_user_model()

EMPTY_ITEM_ERROR = "You can't have an empty list item"
DUPLICATE_ITEM_ERROR = "重复内容就不要提交给凑单吧了！"
NEED_TO_LOGIN_ERROR = "别着急，先登录再凑单！"
ORDER_FORMAT_ERROR = "代号和数量，用空格分开就可以了"
BILL_FORMAT_ERROR = "名称、数量和单价，用空格分开就可以了"
ITEMCD_NOT_VALID_ERROR = "“{}”是什么代号啊亲！选{}啊！"
JU_FORMAT_ERROR = "管理凑单活动太复杂了"
TOO_LONG_ERROR = "输入太多了"

class ItemForm(forms.models.ModelForm):

    class Meta:
        model = Item
        fields = ('text',)
        widgets = {
            'text': forms.fields.TextInput(attrs={
                'placeholder': '输入：代号 数量；示例：A 1.5',
                'class': 'form-control input-lg',
            }),
        }
        error_messages = {
                'text': {'required': EMPTY_ITEM_ERROR,'max_length': TOO_LONG_ERROR }
        }

class JuItemForm(forms.models.ModelForm):

    class Meta:
        model = Ju
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': '#@!@#$$%%#',
                'class': 'form-control input-lg',
            }),
        }
        error_messages = {
            'content': {'required': EMPTY_ITEM_ERROR }
        }

    def save(self, owner=None, ju=None):
        item_text=self.cleaned_data['content']
        if ju:
            ju.content = item_text
        else:
            ju =Ju(content=item_text, owner=owner)    
        if ju.parse_content():
            ju.save()
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

class ExistingListItemForm(ItemForm):
    def __init__(self, for_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.list = for_list

    def validate_unique(self):
        try:
            self.instance.validate_unique()
        except ValidationError as e:
            e.error_dict = {'text':[DUPLICATE_ITEM_ERROR]}
            self._update_errors(e)
    def save(self):
        item_text=self.cleaned_data['text']
        ju = self.instance.list.ju

        # ju list need to check input item cd/name if exists in Ju
        if ju:
            item_name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', item_text)
            if item_name.upper() not in ju.items.keys():
                self.add_error('text', ITEMCD_NOT_VALID_ERROR.format(item_name,','.join(ju.items.keys())))
                return

        item_name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', item_text)
        item_name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', item_name)
        items_to_delete = Item.objects.filter(list=self.instance.list, text__istartswith=item_name)
        for i in items_to_delete:
            i.delete()
        super().save()
        return True

class NewListForm(ItemForm):
    def save(self, owner=None, ju=None):
        item_text=self.cleaned_data['text']
        if ju:
            item_name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', item_text)
            if owner:
                if re.search(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$',item_text):
                    if item_name.upper() in ju.items.keys():
                        return List.create_new(first_item_text=item_text, owner=owner, ju=ju)
                    else:
                        self.add_error('text', ITEMCD_NOT_VALID_ERROR.format(item_name,','.join(ju.items.keys())))
                else:
                    self.add_error('text',ORDER_FORMAT_ERROR)
            else:
                self.add_error('text',NEED_TO_LOGIN_ERROR)
        elif owner:
            return List.create_new(first_item_text=item_text, owner=owner)
        else:
            return List.create_new(first_item_text=item_text)

