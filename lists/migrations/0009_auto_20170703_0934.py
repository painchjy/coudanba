# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-03 01:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lists', '0008_list_created_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ju',
            options={'ordering': ('-updated_at',)},
        ),
        migrations.AddField(
            model_name='ju',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ju',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ju',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
