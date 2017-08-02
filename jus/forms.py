from django import forms
from lists.models import Item as ListItem, List
from jus.models import Ju, Item, STATUS_CHOICES, Location, LocationDepart
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
class LocationForm(forms.models.ModelForm):

    class Meta:
        model = Location 
        fields = ('name',)
        widgets = {
            'name': forms.fields.TextInput(attrs={
                'placeholder': '输入地点的说明',
                'class': 'form-control input-md',
            }),
        }
        error_messages = {
            'name': {'required': EMPTY_ITEM_ERROR },
        }
    def __init__(self, location=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if location:
            self.instance = location
            self.fields['name'].initial = location.name

    def save(self, location = None, depart_names = None):
        if not location:
            location = Location()
        location.name = self.cleaned_data['name']
        location.save()

        if depart_names:
            for ld in location.locationdepart_set.all():
                ld.delete()

            for dn in depart_names:
                LocationDepart.objects.create(location=location, depart_name=dn)

        return location

class LocationDepartForm(forms.models.ModelForm):
    depart_names = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(
            attrs={
                'class': 'form-control input-md'
            }
        ),
    )
    class Meta:
        model = LocationDepart
        fields = ('depart_name',)

    def __init__(self,location=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['depart_names'].choices = User.objects.all().values_list(
            'depart_name','depart_name').distinct()
        self.fields['depart_names'].label =  '选择需要包含的群组：'
        if location:
            selecteddepart = [d.depart_name for d in location.locationdepart_set.all()]
            self.fields['depart_names'].initial =  [d.depart_name for d in location.locationdepart_set.all()]

class LocationModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class JuItemForm(forms.models.ModelForm):

    class Meta:
        model = Ju
        fields = ( 'items','stop_date_time','status','address','ju_type','location')
        widgets = {
            'address': forms.fields.TextInput(attrs={
                'placeholder': '可以输入活动地点和要求',
                'class': 'form-control input-md',
            }),
            'items': forms.Textarea(attrs={
                'placeholder': '#@!@#$$%%#',
                'class': 'form-control input-md',
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
    
    location = LocationModelChoiceField(
        queryset= Location.objects.none(),
        empty_label="选择范围",
        widget=forms.Select(attrs={'class':'form-control input-md'}),
        label = '活动范围(如不选，则所有用户都可参加)：',
        required = False,
    )

    def save(self, owner=None, ju=None, parent=None):
        if not ju:
            ju =Ju(owner=owner)    
        ju.address = self.cleaned_data['address']
        ju.items = self.cleaned_data['items']
        ju.stop_date_time = self.cleaned_data['stop_date_time']
        ju.status = self.cleaned_data['status']
        ju.ju_type = self.cleaned_data['ju_type']
        ju.location = self.cleaned_data['location']
        if parent:
            ju.parent = parent
        if ju.parent:
            err_item_keys = [key for key in ju.items.keys() if key not in ju.parent.items.keys()]
            if err_item_keys:
                self.add_error('items', '代号{}在主活动中没有，请修改项目定义'.format('、'.join(err_item_keys)))
                return
        if owner:
            ju.owner = owner
        try:
            ju.save()
            ju.db_triggers()
        except Exception as e:
            print('-----------Exception for updating JuItem:{}'.format(e))
            self.add_error('items', 'Update Item Error:{}'.format(e))
            return
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
            if len(row) == 3:
                display_name = row[2]
            else:
                display_name = row[0].split('@')[0]
            user, created = User.objects.update_or_create(
                email=row[0],
                defaults={'depart_name': row[1], 'display_name': display_name},
            )

