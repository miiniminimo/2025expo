# enrollments/views.py

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status, serializers

from organizations.views import IsCompanySession
from organizations.models import Employee
from .models import Enrollment
from .serializers import EnrollmentSerializer, EnrollmentDetailSerializer

class EnrollmentViewSet(ModelViewSet):
    """
    수강(Enrollment) 정보를 관리하는 API
    - GET /api/enrollments/
    - POST /api/enrollments/
    """
    queryset = Enrollment.objects.all()
    permission_classes = [IsCompanySession]

    def get_serializer_class(self):
        """ 액션에 따라 다른 Serializer를 반환 """
        if self.action in ['list', 'retrieve']:
            return EnrollmentDetailSerializer
        return EnrollmentSerializer

    def get_queryset(self):
        """ 로그인한 회사의 직원들에게 해당하는 수강 정보만 필터링 """
        company_id = self.request.session.get("company_id")
        return self.queryset.select_related('employee', 'course', 'employee__company').filter(employee__company_id=company_id)

    def perform_create(self, serializer):
        """ 수강 등록 시, 해당 직원이 로그인한 회사 소속인지 검증 """
        company_id = self.request.session.get("company_id")
        employee_id = serializer.validated_data.get('employee').id

        # 우리 회사 소속의 직원이 맞는지 확인
        if not Employee.objects.filter(id=employee_id, company_id=company_id).exists():
            # 추후에 403 에러로 바꿀 것
            raise serializers.ValidationError({"employee": "해당 직원은 귀사의 소속이 아닙니다."})

        serializer.save()