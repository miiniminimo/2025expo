# backend/backend/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/', include('backend.api_extra_urls')),   # ← 중요
    path('api/org/', include('organizations.urls')),   # (기존 라우트 유지 필요 없으면 제거 가능)
    path('admin/', admin.site.urls),
    path('api/sensor/', include('sensor.urls')),
]
