# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-27 16:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wechat', '0003_locationhis'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
