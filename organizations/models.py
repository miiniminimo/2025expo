# backend/organizations/models.py
import uuid
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

bizno_validator = RegexValidator(
    r"^\d{10}$", "사업자등록번호는 숫자 10자리여야 합니다."
)

class Company(models.Model):
    """
    회사 자체가 '계정' 역할을 수행.
    - biz_no(10자리) + password(해시)로 로그인
    - User 테이블 의존 없음
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    biz_no = models.CharField(max_length=10, unique=True, validators=[bizno_validator])
    domain = models.CharField(max_length=120, blank=True)

    # 회사 로그인용 비밀번호(해시)
    password = models.CharField(max_length=128, blank=True, default="")

    # 기존 데이터가 있어도 마이그레이션 쉽게 하도록 일단 null 허용
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.biz_no})"

    # 편의 메서드
    def set_password(self, raw_password: str):
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        if not self.password:
            return False
        return check_password(raw_password, self.password)


class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="employees")

    # 이제 NOT NULL
    emp_no = models.CharField(max_length=50)

    name = models.CharField(max_length=120)
    dept = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        # 회사+사번 유니크 보장
        constraints = [
            models.UniqueConstraint(fields=["company", "emp_no"], name="uq_employee_company_empno")
        ]

