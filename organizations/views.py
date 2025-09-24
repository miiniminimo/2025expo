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

# ModelViewSet: get, post, put, delete 등 모델에 대한 거의 모든 crud 기능을 자동으로 제공하는 클래스
class CompanyViewSet(ModelViewSet):
    """
    회사 회원가입/조회
    POST /api/org/companies  (또는 /api/companies - 라우팅에 따라)
    """
    # 데이터를 최신순으로 정렬하여 가져옴(기본적으로는 오름차순이나 필드 이름 앞에 "-"가 붙으면 내림차순)
    queryset = Company.objects.all().order_by("-created_at", "-id")
    serializer_class = CompanySerializer

    # 동적 권한 설정
    # 요청된 작업의 종류에 따라서 다른 권한을 적용하는 메서드
    def get_permissions(self):
        if self.action in ["create"]:  # 회원가입은 공개
            return [AllowAny()] # AllpwAny: 누구나 허용 권한 적용
        return [IsCompanySession()] # 그 외 모든 작업에 대해서는 회사 로그인 필수 권한을 적용

    # 동적 시리얼라이저 설정
    # 작업의 종류에 따라 다른 시리얼라이저 사용하도록 하는 메서드
    def get_serializer_class(self):
        # 회원가입 작업일 때는 비밀번호 해싱 기능이 포함된 시리얼라이저 반환, 그 외 작업은 비밀번호 필드가 없는 시리얼라이저 반환
        return CompanyCreateSerializer if self.action == "create" else CompanySerializer

class EmployeeViewSet(ModelViewSet):
    """
    직원 CRUD + 엑셀 대량 업로드
    - 회사 로그인 세션 필수
    """
    permission_classes = [IsCompanySession]
    serializer_class = EmployeeSerializer

    # 데이터 접근 범위 제한(데이터 범위를 동적으로 결정)
    def get_queryset(self):
        # 세션의 회사만 접근
        # 현재 로그인한 회사에 소속된 직원들만 조회하도록 범위를 제한함
        cid = self.request.session.get("company_id")
        # select_related: 직원 정보를 가져올 때 관련된 회사 정보도 함께 가져옴(추가 조회를 막아서 성능 최적화)
        return Employee.objects.select_related("company").filter(company_id=cid)
    
    # @action: crud 기능 외에, 특별한 기능을 가진 api 엔드포인트를 추가할 때 사용함
    # detail: 특정 하나가 아닌 전체 목록에 대해 동작
    # methods: post 요청만 받음
    # url_path: url 경로의 마지막 부분을 bulk 라고 지정함
    @action(detail=False, methods=["post"], url_path="bulk")
    # 엑셀에서 추출한 여러 명의 직원 정보를 json 배열 형태로 받아 한 번에 처리하는 메서드
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

            # was_created: 새로운 직원이 생성되었으면 True, 업데이트 되었으면 False
            obj, was_created = Employee.objects.update_or_create(
                company_id=cid, emp_no=emp_no, defaults=defaults
            )

            # 결과 집계
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        return Response({"ok": True, "created": created, "updated": updated, "count": len(rows)})
