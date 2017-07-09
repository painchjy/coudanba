from django import forms
from lists.models import Item, List
from jus.models import Ju
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

