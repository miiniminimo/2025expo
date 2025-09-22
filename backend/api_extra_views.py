# backend/backend/api_extra_views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.hashers import check_password
import json

from organizations.models import Company

@ensure_csrf_cookie
def csrf_probe(request):
    # csrftoken 쿠키를 내려주기 위한 엔드포인트
    return JsonResponse({"ok": True})

@require_POST
@csrf_protect
def login_api(request):
    # JSON 또는 x-www-form-urlencoded 모두 지원
    try:
        if request.content_type and "application/json" in request.content_type:
            payload = json.loads((request.body or b"").decode() or "{}")
        else:
            payload = request.POST
    except Exception:
        return JsonResponse({"detail": "invalid JSON"}, status=400)

    biz_no = (payload.get("biz_no") or "").strip()
    password = payload.get("password") or ""
    if not biz_no or not password:
        return JsonResponse({"detail": "biz_no and password required"}, status=400)
    if len(biz_no) != 10 or not biz_no.isdigit():
        return JsonResponse({"detail": "biz_no must be 10 digits"}, status=400)

    company = Company.objects.filter(biz_no=biz_no).first()
    if not company:
        return JsonResponse({"detail": "invalid credentials"}, status=401)

    try:
        ok = check_password(password, company.password)
    except Exception:
        ok = (password == company.password)
    if not ok:
        return JsonResponse({"detail": "invalid credentials"}, status=401)

    request.session["company_id"] = str(company.id)           # UUID → 문자열
    request.session["company_biz_no"] = str(company.biz_no)   # 혹시 int/Decimal 대비
    request.session.modified = True
    return JsonResponse({"ok": True, "company": {"id": company.id, "biz_no": company.biz_no}})

@require_POST
@csrf_protect
def logout_api(request):
    request.session.flush()
    return JsonResponse({"ok": True})

def me_api(request):
    cid = request.session.get("company_id")
    if not cid:
        return JsonResponse({"detail": "unauthenticated"}, status=401)
    return JsonResponse({"company_id": cid, "biz_no": request.session.get("company_biz_no")})
