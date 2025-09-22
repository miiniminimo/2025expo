# sensor/serializers.py
from rest_framework import serializers
from .models import SensorDevice, SensorData

# 기존(레거시) 포맷 검증용 키
REQUIRED_KEYS = ["thumb", "indexf", "middle", "ring", "little", "gx", "gy", "gz"]


# --- 신규: 손 데이터 포맷 지원 ---
class HandRotationSerializer(serializers.Serializer):
    x = serializers.FloatField()
    y = serializers.FloatField()
    z = serializers.FloatField()
    w = serializers.FloatField()


class HandSerializer(serializers.Serializer):
    rotation = HandRotationSerializer()
    # 항상 5개(엄지~소지) 값
    fingers = serializers.ListField(
        child=serializers.FloatField(), min_length=5, max_length=5
    )


# --- 기존: 단일 프레임(thumb..gz) 전용 Serializer (레거시) ---
class SingleFrameSerializer(serializers.Serializer):
    """단일 프레임: 손가락/자이로 값을 한 번에 보냄 (레거시 포맷)."""
    thumb = serializers.IntegerField()
    indexf = serializers.IntegerField()
    middle = serializers.IntegerField()
    ring = serializers.IntegerField()
    little = serializers.IntegerField()
    gx = serializers.FloatField()
    gy = serializers.FloatField()
    gz = serializers.FloatField()
    ts = serializers.DateTimeField(required=False, allow_null=True)
    frame = serializers.IntegerField(required=False)


class SensorIngestSerializer(serializers.Serializer):
    """
    지원 포맷:
      A) 단일 프레임(레거시): thumb..gz (+ ts, frame)
      B) 배치: readings = [ {...A 혹은 C 포맷...}, ... ]
      C) 손 포맷(신규): left_hand, right_hand (+ ts, frame)

    공통:
      - metric 기본값 'hand_pose'
      - ts, frame은 선택
    """
    metric = serializers.CharField(required=False, allow_blank=True, default="hand_pose")

    # B) 배치 업로드: 각 요소는 dict(레거시/손 포맷 모두 허용)
    readings = serializers.ListField(
        child=serializers.DictField(), required=False
    )

    # A) 레거시 단일 프레임 필드 (옵션)
    thumb = serializers.IntegerField(required=False)
    indexf = serializers.IntegerField(required=False)
    middle = serializers.IntegerField(required=False)
    ring = serializers.IntegerField(required=False)
    little = serializers.IntegerField(required=False)
    gx = serializers.FloatField(required=False)
    gy = serializers.FloatField(required=False)
    gz = serializers.FloatField(required=False)

    # 공통 메타
    ts = serializers.DateTimeField(required=False, allow_null=True)
    frame = serializers.IntegerField(required=False)

    # C) 손 포맷(신규)
    left_hand = HandSerializer(required=False)
    right_hand = HandSerializer(required=False)

    def validate(self, attrs):
        # B) 배치면 그대로 통과 (각 요소는 뷰에서 raw로 저장)
        if attrs.get("readings"):
            return attrs

        # C) 손 포맷: 항상 양손이 온다고 했으므로 둘 다 필수
        if "left_hand" in attrs or "right_hand" in attrs:
            if not attrs.get("left_hand") or not attrs.get("right_hand"):
                raise serializers.ValidationError("Both left_hand and right_hand are required.")
            return attrs

        # A) 레거시 단일 프레임: 필수 키 검사
        missing = [k for k in REQUIRED_KEYS if attrs.get(k, None) is None]
        if missing:
            raise serializers.ValidationError(f"Missing keys: {', '.join(missing)}")
        return attrs


class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = ["id", "device", "ts", "metric", "value", "raw", "idempotency_key", "created_at"]
        read_only_fields = ["id", "created_at"]
