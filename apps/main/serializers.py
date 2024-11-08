# Django
from django.utils.translation import gettext_lazy as _

# Rest-Framework
from rest_framework import serializers
from rest_framework.fields import FileField


def validate_video_file(value):
    import os
    from django.core.exceptions import ValidationError

    ext = os.path.splitext(value.name)[1]  # Get the file extension
    valid_extensions = ['.mp4', '.avi', '.mkv', '.mov']  # Add or modify the list based on allowed video file extensions

    if not ext.lower() in valid_extensions:
        raise ValidationError(_('File type not supported. Please upload a valid video file.'))


class UploadFileSerializer(serializers.Serializer):
    uploaded_file = serializers.FileField(validators=[validate_video_file])


class SubmitTranscribeJobSerializer(serializers.Serializer):
    input_video = serializers.CharField(max_length=2000)
    redacted = serializers.CharField(max_length=20)


# serializers.py
from rest_framework import serializers
from .models import Video, UploadedVideo, TranscribeResult


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'


class UploadedVideoSerializer(serializers.ModelSerializer):
    file = FileField(validators=[validate_video_file])

    class Meta:
        model = UploadedVideo
        fields = ['user', 'bucket', 'obj_key', 'file']


class TranscribeResultSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(required=True)

    class Meta:
        model = TranscribeResult
        fields = ['user', 'filename']
