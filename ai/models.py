# ai/models.py

from django.db import models
import uuid
import secrets
from organizations.models import Company, Employee # organizations 앱에서 Company와 Employee 모델을 가져옴

# 인증 담당 모델
class SensorDevice(models.Model):
    """
    Unity 디바이스 인증을 담당.
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
            models.UniqueConstraint(fields=["company", "device_uid"], name="uq_ai_sensor_device_company_uid")
        ]
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"[{self.company.name}] {self.device_uid}"

    @staticmethod
    def generate_api_key() -> str:
        return secrets.token_hex(32)

# --- 2. AI 평가 기준 데이터 모델 ---
class MotionType(models.Model):
    """
    '소화기 들기' 등 동작의 종류를 정의하고, 평가에 필요한 요약 정보를 저장.
    """
    motion_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # 개선 사항: 미리 계산된 max_dtw_distance 값을 저장할 필드
    max_dtw_distance = models.FloatField(default=1000.0, help_text="점수 정규화를 위한 최대 DTW 거리")

    def __str__(self):
        return self.motion_name

class MotionRecording(models.Model):
    """
    모범(reference) 또는 0점(zero_score) 동작의 실제 센서 데이터를 저장하는 '데이터 원본 창고'.
    """
    motion_type = models.ForeignKey(MotionType, on_delete=models.CASCADE, related_name="recordings")
    recorded_at = models.DateTimeField(auto_now_add=True)
    data_frames = models.IntegerField()
    score_category = models.CharField(max_length=20, choices=[("reference", "모범 동작"), ("zero_score", "0점 동작")])
    sensor_data_json = models.JSONField()

    def get_sensor_data_numpy(self):
        import numpy as np
        import pandas as pd
        if self.sensor_data_json:
            df = pd.DataFrame(self.sensor_data_json)
            return df.values
        return np.array([])

# 사용자 평가 결과 저장 모델
class UserRecording(models.Model):
    """
    사용자의 최종 평가 결과를 기록.
    """
    # 개선 사항: user 필드를 Django 기본 User가 아닌 Employee 모델로 변경
    user = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="motion_recordings")
    motion_type = models.ForeignKey(MotionType, on_delete=models.CASCADE)
    score = models.FloatField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.motion_type.motion_name} ({self.score})"