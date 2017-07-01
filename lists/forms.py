from django import forms
from lists.models import Item, List
from django.core.exceptions import ValidationError
import shlex

EMPTY_ITEM_ERROR = "You can't have an empty list item"
DUPLICATE_ITEM_ERROR = "You've already got this in your list"
NEED_TO_LOGIN_ERROR = "别着急，先登录再下单！"
ORDER_FORMAT_ERROR = "下单格式很简单，只要编码和数量，用空格分开就可以了"
BILL_FORMAT_ERROR = "记账格式很简单，只要名称、数量和单价，用空格分开就可以了"
ITEMCD_NOT_VALID_ERROR = "“{}”是什么编码啊亲！选{}啊！"

class ItemForm(forms.models.ModelForm):

    class Meta:
        model = Item
        fields = ('text',)
        widgets = {
            'text': forms.fields.TextInput(attrs={
                'placeholder': '下单格式：编号 数量；示例：A 1.5',
                'class': 'form-control input-lg',
            }),
        }
        error_messages = {
            'text': {'required': EMPTY_ITEM_ERROR }
        }
    def parse_item(self, item_text):
        units = shlex.split(item_text)
        self.item_name = None
        self.qty = None
        self.price = None
        try:
            self.item_name = units[0]
            self.qty = float(units[1])
            self.price = float(units[2])
        except (ValueError,IndexError) as e:
            if not self.item_name:
                return 'empty'
            if not self.qty:
                return 'text'
            if not self.price:
                return 'order'
        return 'bill'


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
        format_type = self.parse_item(item_text)
        ju = self.instance.list.ju

        # ju list need to check input item cd/name if exists in Ju
        if ju:
            if not ju.items[self.item_name]:
                self.add_error('text', ITEMCD_NOT_VALID_ERROR.format(self.item_name,','.join(ju.items.keys())))
                return

        items_to_delete = Item.objects.filter(list=self.instance.list, text__istartswith=self.item_name)
        for i in items_to_delete:
            i.delete()
        super().save()

class NewListForm(ItemForm):
    def save(self, owner=None, ju=None):
        item_text=self.cleaned_data['text']
        format_type = self.parse_item(item_text)
        if ju:
            if owner:
                if format_type == 'order':
                    if ju.items[self.item_name]:
                        return List.create_new(first_item_text=item_text, owner=owner, ju=ju)
                    else:
                        self.add_error('text', ITEMCD_NOT_VALID_ERROR.format(self.item_name,','.join(ju.items.keys())))
                else:
                    self.add_error('text',ORDER_FORMAT_ERROR)
            else:
                self.add_error('text',NEED_TO_LOGIN_ERROR)
        elif owner:
            return List.create_new(first_item_text=item_text, owner=owner)
        else:
            return List.create_new(first_item_text=item_text)

