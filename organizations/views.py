# backend/organizations/views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, AllowAny

from .models import Company, Employee
from .serializers import (
    CompanyCreateSerializer, CompanySerializer,
    EmployeeSerializer
)

# 세션에 company_id가 있어야 접근 허용 (회사 로그인 필수)
class IsCompanySession(BasePermission):
    def has_permission(self, request, view):
        return bool(request.session.get("company_id"))

class CompanyViewSet(ModelViewSet):
    """
    회사 회원가입/조회
    POST /api/org/companies  (또는 /api/companies - 라우팅에 따라)
    """
    queryset = Company.objects.all().order_by("-created_at", "-id")
    serializer_class = CompanySerializer

    def get_permissions(self):
        if self.action in ["create"]:  # 회원가입은 공개
            return [AllowAny()]
        return [IsCompanySession()]

    def get_serializer_class(self):
        return CompanyCreateSerializer if self.action == "create" else CompanySerializer


class EmployeeViewSet(ModelViewSet):
    """
    직원 CRUD + 엑셀 대량 업로드
    - 회사 로그인 세션 필수
    """
    permission_classes = [IsCompanySession]
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        # 세션의 회사만 접근
        cid = self.request.session.get("company_id")
        return Employee.objects.select_related("company").filter(company_id=cid)

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk(self, request):
        """
        엑셀 업로드 바디 예:
        {
          "employees": [
            {"emp_no":"E001","name":"홍길동","dept":"개발","phone":"010-...","email":"a@b.com"},
            ...
          ]
        }
        - (company, emp_no) 기준 upsert
        """
        cid = request.session.get("company_id")
        if not cid:
            return Response({"detail": "Unauthorized"}, status=401)

        rows = request.data.get("employees", [])
        if not isinstance(rows, list):
            return Response({"detail": "employees must be a list"}, status=400)

        created, updated = 0, 0
        for r in rows:
            emp_no = (r.get("emp_no") or "").strip()
            if not emp_no:
                continue
            defaults = {
                "name":  r.get("name", "") or "",
                "dept":  r.get("dept", "") or "",
                "phone": r.get("phone", "") or "",
                "email": r.get("email", "") or "",
            }
            obj, was_created = Employee.objects.update_or_create(
                company_id=cid, emp_no=emp_no, defaults=defaults
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        return Response({"ok": True, "created": created, "updated": updated, "count": len(rows)})
