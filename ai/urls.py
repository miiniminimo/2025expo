# ai/urls.py

from django.urls import path
from .views import MotionRecordingView, UnifiedEvaluationView 

urlpatterns = [
    path('recordings/', MotionRecordingView.as_view(), name='motion-recording'),
    path('evaluate/', UnifiedEvaluationView.as_view(), name='unified-evaluation'),
]