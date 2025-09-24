# ai/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# MotionTypeViewSet을 추가로 임포트
from .views import MotionRecordingView, UnifiedEvaluationView, SensorDeviceViewSet, MotionTypeViewSet

# 라우터 생성
router = DefaultRouter()
# /devices/ 경로에 SensorDeviceViewSet을 등록
router.register(r'devices', SensorDeviceViewSet, basename='sensordevice')
# /motion-types/ 경로에 MotionTypeViewSet을 등록
router.register(r'motion-types', MotionTypeViewSet, basename='motiontype')

urlpatterns = [
    # 기존 URL
    path('recordings/', MotionRecordingView.as_view(), name='motion-recording'),
    path('evaluate/', UnifiedEvaluationView.as_view(), name='unified-evaluation'),
    
    # 라우터에 등록된 URL들을 포함 (/api/ai/devices/, /api/ai/motion-types/ 등)
    path('', include(router.urls)),
]