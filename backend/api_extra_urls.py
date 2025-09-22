# backend/backend/api_extra_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from organizations.views import CompanyViewSet, EmployeeViewSet
from .api_extra_views import login_api, logout_api, csrf_probe, me_api

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')  # 회사 회원가입
router.register(r'employees', EmployeeViewSet, basename='employee')  # 직원 CRUD/업로드

urlpatterns = [
    path('auth/csrf', csrf_probe),
    path('auth/login', login_api),
    path('auth/logout', logout_api),
    path('auth/me', me_api),
    path('', include(router.urls)),
]
