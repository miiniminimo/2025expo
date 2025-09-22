# backend/organizations/serializers.py
from rest_framework import serializers
from .models import Company, Employee

class CompanyCreateSerializer(serializers.ModelSerializer):
    # 평문 비밀번호 입력 → 저장 시 해시 처리
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = Company
        fields = ["id", "name", "biz_no", "domain", "password", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        raw_pw = validated_data.pop("password")
        company = Company(**validated_data)
        company.set_password(raw_pw)
        company.save()
        return company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "biz_no", "domain", "created_at"]


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id", "company", "emp_no", "name", "dept", "phone", "email", "created_at"]
        read_only_fields = ["id", "created_at"]
