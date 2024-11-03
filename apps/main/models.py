# Python
import uuid
import datetime

# Django
from django.db import models
from django.contrib.auth.models import User


def user_directory_path(instance, filename):
    file_type = filename.split('.')[-1]
    today = str(datetime.datetime.today())[0:7]
    return f'file/{today}/{uuid.uuid4()}.{file_type}'


class Video(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    filepath = models.FileField(upload_to=user_directory_path)


class UploadedVideo(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    bucket = models.CharField(max_length=500)
    obj_key = models.CharField(max_length=1000, unique=True)


class TranscribeResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uri = models.CharField(max_length=1000)
    redacted = models.BooleanField(default=False)
