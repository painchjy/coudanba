# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-03 13:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lists', '0009_auto_20170703_0934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='text',
            field=models.CharField(default='', max_length=140),
        ),
    ]