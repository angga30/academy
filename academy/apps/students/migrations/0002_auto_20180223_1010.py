# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-23 10:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='training',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='training',
            name='batch',
            field=models.PositiveIntegerField(unique=True),
        ),
    ]
