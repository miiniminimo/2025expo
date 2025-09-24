# courses/serializers.py

from rest_framework import serializers
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    # motion_type의 motion_name을 직접 보여주기 위한 필드 (읽기 전용)
    motion_type_name = serializers.CharField(source='motion_type.motion_name', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'motion_type', # 쓸 때는 ID, 읽을 때는 ID
            'motion_type_name', # 읽을 때 사용
            'code',
            'title',
            'description',
            'duration_min',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

        # 쓰기 전용 필드 설정: motion_type은 ID로만 받도록 함
        extra_kwargs = {
            'motion_type': {'write_only': True, 'required': False, 'allow_null': True}
        }
