# sensor/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ingest  # <- 추가

router = DefaultRouter()
# (기존) router.register('devices', SensorDeviceViewSet, basename='sensor-device')

urlpatterns = [
    path('', include(router.urls)),
    path('ingest/', ingest, name='sensor-ingest'),  # 슬래시 버전
    path('ingest', ingest),                         # 무슬래시도 허용
]