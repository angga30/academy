# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from PIL import Image, ImageOps
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models import When, Case, Count, IntegerField, Q
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36
from django.template.loader import render_to_string
from django.utils.six import StringIO

from academy.core.utils import image_upload_path
from academy.core.validators import validate_mobile_phone
from academy.apps.students.models import Student, TrainingStatus
from academy.apps.logs.models import LogTrainingStatus

from model_utils import Choices
from post_office import mail


class CustomUserManager(UserManager):
    def create_user(self, username, email, password, is_active=False, **extra_fields):
        user = super().create_user(username, email, password, is_active=False, **extra_fields)
        return user

    def registered(self):
        registered = self.exclude(Q(is_superuser=True) | Q(is_staff=True))
        return registered

    def actived(self):
        actived = self.registered().filter(is_active=True)
        return actived


class User(AbstractUser):
    email = models.EmailField(unique=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True, default=None,
                             validators=[validate_mobile_phone])
    ROLE = Choices(
        (1, 'student', 'Student'),
        (2, 'trainer', 'Trainer'),
        (2, 'company', 'Company'),
    )
    role = models.PositiveIntegerField(choices=ROLE, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    objects = CustomUserManager()

    @property
    def name(self):
        name = self.get_full_name()
        if not name:
            name = self.username
        return name

    def get_student(self):
        return self.students.select_related('training').last()

    def notification_register(self):
        data = {
            'token': default_token_generator.make_token(self),
            'uid': int_to_base36(self.id),
            'host': settings.HOST,
            'user': self,
            'email_title': 'Aktivasi Akun'
        }

        send = mail.send(
            [self.email],
            settings.DEFAULT_FROM_EMAIL,
            subject='Aktivasi Akun',
            html_message=render_to_string('emails/register.html', context=data)
        )
        return send

    def notification_status_training(self, training_materials):
        data = {
            'host': settings.HOST,
            'user': self,
            'training_materials': training_materials,
            'email_title': 'Status Pelatihan'
        }

        send = mail.send(
            [self.email],
            settings.DEFAULT_FROM_EMAIL,
            subject='Status Pelatihan',
            html_message=render_to_string('emails/training-status.html', context=data)
        )
        return send

    def get_count_training_status(self):
        count_status = self.training_status.aggregate(
            graduate=Count(
                Case(When(status=TrainingStatus.STATUS.graduate, then=1),
                     output_field=IntegerField())
            ),
            not_yet=Count(
                Case(When(status=TrainingStatus.STATUS.not_yet, then=1),
                     output_field=IntegerField())
            ),
            repeat=Count(
                Case(When(status=TrainingStatus.STATUS.repeat, then=1),
                     output_field=IntegerField())
            )
        )
        return count_status

    def indicator_reached(self, status):
        if status['graduate'] >= settings.INDICATOR_GRADUATED and status['not_yet'] == 0:
            return True
        return False

    def save_training_status_to_log(self):
        LogTrainingStatus.objects.bulk_create([
            LogTrainingStatus(
                code=training.training_material.code,
                title=training.training_material.title,
                status=training.status,
                user=self,
                student=self.get_student()
            ) for training in self.training_status.select_related('training_material')
        ])

    def delete_training_status(self):
        self.training_status.all().delete()


class Profile(models.Model):
    user = models.OneToOneField('accounts.User', related_name='profile',
                                on_delete=models.CASCADE)
    address = models.TextField()
    GENDER = Choices(
        (1, 'male', 'Male'),
        (2, 'female', 'Female'),
    )
    gender = models.PositiveIntegerField(choices=GENDER, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    avatar = models.ImageField(upload_to=image_upload_path('avatar'), blank=True, null=True)

    # Social fields
    linkedin = models.URLField(blank=True, max_length=255)
    git_repo = models.URLField(blank=True, max_length=255)
    blog = models.URLField(blank=True, max_length=255)
    facebook = models.URLField(blank=True, max_length=255)
    youtube = models.URLField(blank=True, max_length=255)
    twitter = models.CharField(blank=True, max_length=30)
    instagram = models.CharField(blank=True, max_length=30)
    telegram_id = models.CharField(blank=True, max_length=50)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.avatar:
            # Fit avatar to 200px x 200px
            img = Image.open(self.avatar)
            img = ImageOps.fit(img, (200, 200))
            img.save(self.avatar.path)


class Instructor(models.Model):
    user = models.OneToOneField('accounts.User', related_name='instructor',
                                on_delete=models.CASCADE)
    order = models.IntegerField()

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        # increment order manually because django din't let us have multiple auto field
        if not self.order:
            last_order = Instructor.objects.order_by('-order').first()
            self.order = 1
            if last_order is not None:
                self.order = last_order.order + 1

        super().save(*args, **kwargs)
