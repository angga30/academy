# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-17 15:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20180214_1519'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='blog',
            field=models.URLField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='profile',
            name='git_repo',
            field=models.URLField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='profile',
            name='youtube',
            field=models.URLField(blank=True, max_length=255),
        ),
    ]
