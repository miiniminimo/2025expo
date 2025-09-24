# backend/backend/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/', include('backend.api_extra_urls')),
    path('api/org/', include('organizations.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/enrollments/', include('enrollments.urls')),
    path('admin/', admin.site.urls),
]
