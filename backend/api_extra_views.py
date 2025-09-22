# backend/api_extra_views.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.hashers import check_password
import json

from organizations.models import Company

# csrf 토큰을 클라이언트에게 발급해줌 (ensure_csrf_cookie 데코레이터에 의한)
# 프론트엔드에서 로그인 같은 csrf 보호가 필요한 요청을 보내기 전에 해당 api를 먼저 호출해서 토큰을 받아가야 함
@ensure_csrf_cookie
def csrf_probe(request):
    # csrftoken 쿠키를 내려주기 위한 엔드포인트
    return JsonResponse({"ok": True})

# @require_POST: post 요청만 허용함
# @csrf_protect: csrf 토큰을 검증함
@require_POST
@csrf_protect
def login_api(request):
    # JSON 또는 x-www-form-urlencoded 모두 지원
    try:
        # 요청이 json 형식으로 왔는지 여부
        if request.content_type and "application/json" in request.content_type:
            # 원본 데이터(바이트 b""")를 문자열로 변환(decode())하고, loads를 통해 파이썬 딕셔너리 형태로 변환
            payload = json.loads((request.body or b"").decode() or "{}")
        else:
            payload = request.POST
    # json 형식이 깨져있으면 오류 발생
    except Exception:
        return JsonResponse({"detail": "invalid JSON"}, status=400)

    # get("biz_no")가 None이면 빈 문자열 "" 반환 후 양 끝 공백 제거
    biz_no = (payload.get("biz_no") or "").strip()
    password = payload.get("password") or ""

    if not biz_no or not password:
        return JsonResponse({"detail": "biz_no and password required"}, status=400)
    # 10자가 아니거나 숫자로만 구성되어 있지 않으면(isdigit)
    if len(biz_no) != 10 or not biz_no.isdigit():
        return JsonResponse({"detail": "biz_no must be 10 digits"}, status=400)

    # filter로 찾은 데이터 중 첫 번째 데이터만 반환. 하나도 없는 경우 None 반환
    company = Company.objects.filter(biz_no=biz_no).first()

    if not company:
        return JsonResponse({"detail": "invalid credentials"}, status=401)

    try:
        ok = check_password(password, company.password)
    except Exception:
        ok = (password == company.password)
    if not ok:
        return JsonResponse({"detail": "invalid credentials"}, status=401)

    # request는 객체의 메모리 주소를 공유하고 있기 때문에(객체 참조) 명시적으로 request 객체를 명시적으로 return 하지 않아도 다른 미들웨어가 참조 가능
    # 응답하기 전 SessionMiddleware가 request.session의 내용을 확인 후 변경 사항이 있으면 django_session 테이블에 저장함
    request.session["company_id"] = str(company.id)           # UUID -> 문자열
    request.session["company_biz_no"] = str(company.biz_no)   # 혹시 int/Decimal 대비
    request.session.modified = True

    # return 되면 각 미들웨어로 전달 후 모두 통과가 되면 최종적으로 클라이언트에게 응답 데이터를 제공
    return JsonResponse({"ok": True, "company": {"id": company.id, "biz_no": company.biz_no}})

@require_POST
@csrf_protect
def logout_api(request):
    # 세션 데이터를 서버에서 모두 삭제하고, 브라우저의 session id 쿠키도 만료시켜 무효화함
    request.session.flush()
    return JsonResponse({"ok": True})

# 로그인 상태 확인
# 보통 get 요청으로 상태만 확인
def me_api(request):
    cid = request.session.get("company_id")

    if not cid:
        return JsonResponse({"detail": "unauthenticated"}, status=401)
    return JsonResponse({"company_id": cid, "biz_no": request.session.get("company_biz_no")})
