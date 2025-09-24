# enrollments/serializers.py

from rest_framework import serializers
from organizations.serializers import EmployeeSerializer
from courses.serializers import CourseSerializer
from .models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    """ 수강 등록 생성/수정을 위한 Serializer """
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'employee', # ID로 받음
            'course',   # ID로 받음
            'status',
            'completion_rate',
            'last_session_at',
        ]
        read_only_fields = ['id']

class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """ 수강 등록 정보 조회를 위한 Serializer (nested details 포함) """
    employee = EmployeeSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id',
            'employee',
            'course',
            'status',
            'completion_rate',
            'last_session_at',
        ]
