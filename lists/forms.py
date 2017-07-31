from django import forms
from lists.models import Item, List
from django.core.exceptions import ValidationError
import shlex
import re
import json
from django.contrib.auth import get_user_model
import csv
from decimal import Decimal
User = get_user_model()

EMPTY_ITEM_ERROR = "You can't have an empty list item"
DUPLICATE_ITEM_ERROR = "重复内容就不要提交给凑单吧了！"
ORDER_FORMAT_ERROR = "代号和数量，用空格分开就可以了"
BILL_FORMAT_ERROR = "名称、数量和单价，用空格分开就可以了"
ITEMCD_NOT_VALID_ERROR = "“{}”是什么代号啊亲！选{}啊！"
JU_FORMAT_ERROR = "管理凑单活动太复杂了"
TOO_LONG_ERROR = "输入太多了"
class MyModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.display_name

class ListForm(forms.models.ModelForm):
    class Meta:
        model = List
        fields = ['owner']

    owner = MyModelChoiceField(
        queryset= User.objects.filter(email=''),
        empty_label="可代理群内其他账户下单",
        widget=forms.Select(attrs={'class':'form-control input-md'}),
        label="选择账户：",
        required = False,
    )
    
    def __init__(self, *args, **kwargs):
        depart_name = kwargs.pop('depart_name', None)
        super(ListForm, self).__init__(*args, **kwargs)

        if depart_name:
            self.fields['owner'].queryset = User.objects.filter(depart_name=depart_name)

class ItemForm(forms.models.ModelForm):

    class Meta:
        model = Item
        fields = ['text']
        widgets = {
            'text': forms.fields.TextInput(attrs={
                'placeholder': '输入：代号 数量；示例：A 1.5',
                'class': 'form-control input-md', 
            }),
        }
        error_messages = {
                'text': {'required': EMPTY_ITEM_ERROR,'max_length': TOO_LONG_ERROR }
        }

    def parse_text(self,ju, list_=None):
        item_text=self.cleaned_data['text']
        units = shlex.split(item_text)
        last_index = len(units) - 1
        last_n = None
        prior_n = None
        try:
            if last_index >= 1:
                last_n = Decimal(units[last_index])
            if last_index >= 2:
                prior_n = Decimal(units[last_index - 1])
        except Exception as e:
            print('----units:{},exception:{}'.format(units,e))
            pass
        if ju:
            if last_n != None:
                self_name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', item_text).upper()
                self_qty = last_n
                # check rules of Ju items 
                # should be moved to an help function
                ju_item = ju.item_set.filter(key=self_name).first()
                if ju_item:
                    total_qty = ju_item.total_qty()
                    old_qty = 0
                    if list_:
                        old_item = Item.objects.filter(list=list_, name=self_name).first()
                        if old_item:
                            old_qty = old_item.qty
                    if ju_item.max_total_qty !=None and self_qty + total_qty - old_qty > ju_item.max_total_qty:
                        return '凑单总量为{}份，已经达到了，请换一个品种凑单'.format(ju_item.max_total_qty)
                    if ju_item.max_qty !=None and self_qty > ju_item.max_qty:
                        return '最大下单数量为{}份，请修改数量后重新提交'.format(ju_item.max_qty)
                    if ju_item.min_qty !=None and self_qty < ju_item.min_qty:
                        return '最小下单数量为{}份，请修改数量后重新提交'.format(ju_item.min_qty)
                    if ju_item.unit !=None and ((self_qty) % (ju_item.unit)) != 0:
                        return '下单数量必须为{}的倍数，请修改数量后重新提交{}%{}={}'.format(ju_item.unit,self_qty,ju_item.unit,self_qty%ju_item.unit)
                self_name = item_text.upper()
            try:
                self_price = ju.items[self_name]['price']
            except:
                self_price = 0
        elif last_n != None:
            if prior_n!=None:
                self_price = last_n
                self_qty = prior_n
                self_name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', item_text).upper()
            else:
                self_qty = last_n
                self_name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', item_text).upper()
        else:
            self_name = item_text.upper()


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
    def save(self, agent=None):
        item_text=self.cleaned_data['text']
        ju = self.instance.list.ju
        err_text = self.parse_text(ju, self.instance.list)
        if err_text:
            self.add_error('text', err_text)
            return

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
        if agent:
            self.instance.list.agent = agent
            self.instance.list.save()
        return True

class NewListForm(ItemForm):
    def save(self, owner=None):
        item_text=self.cleaned_data['text']
        if owner:
            return List.create_new(first_item_text=item_text, owner=owner)
        else:
            return List.create_new(first_item_text=item_text)
    
class NewOrderForm(ItemForm):
    def save(self, owner=None, agent=None, ju=None):
        item_text=self.cleaned_data['text']
        err_text = self.parse_text(ju)
        if err_text:
            self.add_error('text', err_text)
            return
        if ju:
            item_name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', item_text)
            if re.search(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$',item_text):
                if item_name.upper() in ju.items.keys():
                    return List.create_new(first_item_text=item_text, owner=owner,agent=agent, ju=ju)
                else:
                    self.add_error('text', ITEMCD_NOT_VALID_ERROR.format(item_name,','.join(ju.items.keys())))
            else:
                self.add_error('text',ORDER_FORMAT_ERROR)

