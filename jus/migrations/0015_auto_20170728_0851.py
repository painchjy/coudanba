# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-28 00:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jus', '0014_auto_20170727_0825'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=300)),
            ],
        ),
        migrations.AlterField(
            model_name='ju',
            name='ju_type',
            field=models.CharField(choices=[('order', '凑单'), ('didi', '拼车'), ('plan', '预算'), ('vote', '投票')], default='', max_length=30),
        ),
        migrations.AddField(
            model_name='ju',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jus.Location'),
        ),
    ]
