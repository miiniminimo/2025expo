# backend/organizations/serializers.py
from rest_framework import serializers
from .models import Company, Employee

# 회사 회원가입 시
class CompanyCreateSerializer(serializers.ModelSerializer):
    # 평문 비밀번호 입력 -> 저장 시 해시 처리
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = Company
        fields = ["id", "name", "biz_no", "domain", "password", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        # db에 저장할 때 검증된 데이터로부터 password 필드만 따로 뺀 후 나머지 필드는 바로 저장하고 password만 암호화해서 따로 저장
        raw_pw = validated_data.pop("password")
        company = Company(**validated_data)
        company.set_password(raw_pw)
        company.save()
        return company

# 이미 생성된 회사의 정보를 조회할 때
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "biz_no", "domain", "created_at"]

# 직원의 정보를 생성/수정/조회할 때
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id", "company", "emp_no", "name", "dept", "phone", "email", "created_at"]
        read_only_fields = ["id", "created_at"]
