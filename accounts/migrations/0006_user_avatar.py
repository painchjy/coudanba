# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-26 23:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_user_group_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.TextField(default=''),
        ),
    ]
