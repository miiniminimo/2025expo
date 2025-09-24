# ai/serializers.py

from rest_framework import serializers
# SensorDevice 모델을 추가로 임포트
from .models import UserRecording, MotionRecording, MotionType, SensorDevice


# --- 신규: MotionType 관리를 위한 Serializer ---
class MotionTypeSerializer(serializers.ModelSerializer):
    motionType = serializers.CharField(source='motion_name', max_length=100)

    class Meta:
        model = MotionType
        fields = ['id', 'motionType', 'description', 'max_dtw_distance']
        read_only_fields = ['id', 'max_dtw_distance']


# --- 신규: SensorDevice 관리를 위한 Serializer ---
class SensorDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorDevice
        # API를 통해 다룰 필드 목록
        fields = ['id', 'company', 'device_uid', 'name', 'api_key', 'is_active', 'created_at']
        # 서버에서 자동으로 생성/결정되어야 하므로, 클라이언트가 직접 쓸 수 없는 필드
        read_only_fields = ['id', 'company', 'api_key', 'created_at']


# --- 기존 Serializer들 ---

class EvaluationRequestSerializer(serializers.Serializer):
    """Unity로부터 평가 요청을 받을 때의 전체 데이터 형식"""
    motionName = serializers.CharField()
    empNo = serializers.CharField()
    # sensorData가 '딕셔셔너리들의 리스트' 형태인지만 검증.
    sensorData = serializers.ListField(child=serializers.DictField())


class UserRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRecording
        fields = ["id", "user", "motion_type", "score", "recorded_at"]
        # sensor_data_json은 용량이 크므로, 목록 조회 시에는 제외하는 것이 좋음
        # 상세 조회 시 별도로 내려주거나, 다른 Serializer를 만드는 것을 고려
        read_only_fields = ["id", "recorded_at"]

class MotionSerializer(serializers.ModelSerializer):
    motionName = serializers.SlugRelatedField(source="motion_type",
                                                  slug_field="motion_name",
                                                  queryset=MotionType.objects.all(),
                                                  write_only=True)
    
    scoreCategory = serializers.CharField(
        source="score_category",
        max_length=20,
    )

    sensorData = serializers.JSONField(write_only=True)

    class Meta:
        model = MotionRecording
        fields = [
            "id",
            "motionName", # motionTypeName -> motionName 으로 수정
            "scoreCategory",
            "sensorData",
            "data_frames",
            "recorded_at"
        ]
        read_only_fields = ["id", "data_frames", "recorded_at"]
    
    def create(self, validated_data):
        from .safty_training_ai import preprocess_sensor_data
        raw_sensor_data = validated_data.pop("sensorData")
        preprocessed_numpy = preprocess_sensor_data(raw_sensor_data)
        validated_data["sensor_data_json"] = preprocessed_numpy.tolist()
        validated_data["data_frames"] = preprocessed_numpy.shape[0]
        return super().create(validated_data)
