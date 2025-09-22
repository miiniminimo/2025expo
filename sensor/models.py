from django.db import models
from django.utils import timezone
import uuid
import secrets

from organizations.models import Company  # 회사 모델

class SensorDevice(models.Model):
    """
    회사가 등록하는 센서 디바이스
    - company: 어느 회사 소속인지
    - device_uid: 회사 내부에서 고유한 디바이스 식별자
    - api_key: 단말 업로드 인증 키 (X-API-Key)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sensor_devices")

    device_uid = models.CharField(max_length=120)
    name = models.CharField(max_length=200, blank=True)

    api_key = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "device_uid"], name="uq_sensor_device_company_uid")
        ]
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"[{self.company.name}] {self.device_uid}"

    @staticmethod
    def generate_api_key() -> str:
        # 64 hex(=32 bytes)
        return secrets.token_hex(32)


class SensorData(models.Model):
    """
    센서 업로드 데이터 (시계열)
    - metric/value: 단일 수치
    - raw: 원본 JSON 보관(선택)
    - idempotency_key: 중복 업로드 방지용(선택)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(SensorDevice, on_delete=models.CASCADE, related_name="data")

    ts = models.DateTimeField(default=timezone.now, db_index=True)
    metric = models.CharField(max_length=120, db_index=True)
    value = models.FloatField(null=True, blank=True)

    raw = models.JSONField(null=True, blank=True)  # MySQL 5.7+ 필요 (낮으면 TextField로 변경)

    idempotency_key = models.CharField(max_length=64, blank=True, default="", db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["device", "ts"]),
            models.Index(fields=["device", "metric", "ts"]),
        ]
        constraints = [
            # 같은 device에서 동일 idempotency_key는 중복 허용 안 함 (빈 문자열 제외)
            models.UniqueConstraint(
                fields=["device", "idempotency_key"],
                name="uq_sensor_data_device_idem",
                condition=~models.Q(idempotency_key="")
            )
        ]
        ordering = ["-ts", "-created_at"]

    def __str__(self):
        return f"{self.device.device_uid} {self.metric}={self.value} @ {self.ts}"
