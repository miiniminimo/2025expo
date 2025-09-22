# sensor/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import SensorDevice, SensorData
from .serializers import SensorIngestSerializer, SensorDataSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def ingest(request):
    """
    단말 업로드: 헤더 X-API-Key 필요.
    - 단일 프레임(레거시 또는 손 포맷) 또는 readings 배열(배치) 지원
    - payload 전체를 SensorData.raw(JSON)로 저장
    - metric 기본값 'hand_pose'
    - 헤더 Idempotency-Key 지원(단일 프레임일 때)
    """
    # 0) API 키 검증
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return Response({"detail": "Missing X-API-Key"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        device = SensorDevice.objects.get(api_key=api_key, is_active=True)
    except SensorDevice.DoesNotExist:
        return Response({"detail": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

    # 1) 페이로드 검증
    serializer = SensorIngestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    metric = serializer.validated_data.get("metric") or "hand_pose"

    with transaction.atomic():
        # 2) readings(배치) 방식
        readings = serializer.validated_data.get("readings")
        if readings:
            created_ids = []
            for frame in readings:
                # ts 정규화: 문자열이면 파싱, 없으면 now()
                ts = frame.get("ts") or timezone.now()
                if isinstance(ts, str):
                    dt = parse_datetime(ts)
                    ts = dt or timezone.now()

                # ✅ raw(JSON)에 들어갈 ts는 ISO 문자열로
                frame["ts"] = ts.isoformat()

                obj = SensorData.objects.create(
                    device=device, ts=ts, metric=metric, value=None, raw=frame
                )
                created_ids.append(str(obj.id))

            return Response(
                {"ok": True, "count": len(created_ids), "ids": created_ids},
                status=status.HTTP_201_CREATED,
            )

        # 3) 단일 프레임 방식 (레거시 or 손 포맷)
        keys = [
            # 레거시 포맷 키들
            "thumb", "indexf", "middle", "ring", "little", "gx", "gy", "gz",
            # 공통 메타
            "ts", "frame",
            # 손 포맷 키들
            "left_hand", "right_hand",
        ]
        frame = {k: serializer.validated_data.get(k) for k in keys if k in serializer.validated_data}

        # ts 정규화
        ts = frame.get("ts") or timezone.now()
        if isinstance(ts, str):
            dt = parse_datetime(ts)
            ts = dt or timezone.now()

        # ✅ raw(JSON)에 들어갈 ts는 ISO 문자열로
        frame["ts"] = ts.isoformat()

        # 멱등 처리
        idem = (request.headers.get("Idempotency-Key") or "").strip()
        if idem:
            obj, created = SensorData.objects.get_or_create(
                device=device,
                idempotency_key=idem,
                defaults={"ts": ts, "metric": metric, "value": None, "raw": frame},
            )
            code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        else:
            obj = SensorData.objects.create(
                device=device, ts=ts, metric=metric, value=None, raw=frame
            )
            code = status.HTTP_201_CREATED

    return Response(
        {"ok": True, "id": str(obj.id), "metric": metric, "device": device.device_uid},
        status=code,
    )
