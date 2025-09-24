# backend/backend/api_extra_urls.py
from django.urls import path, include

# ViewSet: 하나의 모델에 대한 여러 기능(목록 조회, 상세 조회, 수정, 삭제 등)을 하나의 클래스로 묶어놓은 것
# drf 라우터(DefaultRouter): ViewSet을 받아서, RESTful API의 표준적인 url들을 자동으로 생성함
from rest_framework.routers import DefaultRouter
from organizations.views import CompanyViewSet, EmployeeViewSet
from .api_extra_views import login_api, logout_api, csrf_probe, me_api
router = DefaultRouter()

"""
url 구조 요약

인증 관련

- get: /auth/csrf
- get: /auth/me
- post: /auth/login
- post /auth/logout

회사 및 직원 관련(router로 인한 자동생성)

- get, post: /companies
- get, put, patch, delete: /companies/{id}

...직원 또한 동일
"""

# 만약 주소가 companies/ 로 시작하면, CompanyViewSet 클래스를 호출함. basename: url패턴의 내부적인 별명을 만들어주는 옵션
"""
router를 사용했을 때 자동으로 생성되는 url들
/companies/ (get: 목록 조회, post: 생성)
/companies/{id} (get: 상세 조회, put: 전체 수정: patch: 부분 수정, delete: 삭제)
...(employees도 마찬가지)
"""
router.register(r'companies', CompanyViewSet, basename='company')  # 회사 회원가입
router.register(r'employees', EmployeeViewSet, basename='employee')  # 직원 CRUD/업로드

urlpatterns = [
    path('auth/csrf', csrf_probe),
    path('auth/login', login_api),
    path('auth/logout', logout_api),
    path('auth/me', me_api),
    # 아무것도 없는 기본 경로에서는 router로 등록한 주소가 합쳐짐
    path('', include(router.urls)),
    path("ai/", include("ai.urls"))
]