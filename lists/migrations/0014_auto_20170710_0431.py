# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-09 20:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lists', '0013_auto_20170709_0950'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ju',
            name='owner',
        ),
        migrations.AlterModelOptions(
            name='item',
            options={'ordering': ('name',)},
        ),
        migrations.AddField(
            model_name='list',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.DeleteModel(
            name='Ju',
        ),
    ]
