from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.main.views import VideoViewSet, UploadedVideoViewSet, TranscribeResultViewSet

router = DefaultRouter()
router.register(r'videos', VideoViewSet)
router.register(r'uploaded-videos', UploadedVideoViewSet)
router.register(r'transcribe-results', TranscribeResultViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),


    path('', include(router.urls)),
]
