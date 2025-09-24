# courses/views.py

from rest_framework.viewsets import ModelViewSet
from organizations.views import IsCompanySession
from .models import Course
from .serializers import CourseSerializer

class CourseViewSet(ModelViewSet):
    """
    교육 과정(Course)을 관리하는 API
    - GET /api/courses/
    - POST /api/courses/
    """
    queryset = Course.objects.select_related('motion_type').all().order_by('-created_at')
    serializer_class = CourseSerializer
    permission_classes = [IsCompanySession] # 로그인한 회사 관리자만 접근 가능