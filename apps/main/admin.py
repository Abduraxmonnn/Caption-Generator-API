from django.contrib import admin

# Register your models here.
from apps.main.models import Video, UploadedVideo, TranscribeResult


admin.site.register(Video)
admin.site.register(UploadedVideo)
admin.site.register(TranscribeResult)