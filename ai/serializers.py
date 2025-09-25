# ai/serializers.py

from rest_framework import serializers
from .models import UserRecording, MotionRecording, MotionType, SensorDevice

class MotionTypeSerializer(serializers.ModelSerializer):
    """MotionType 모델 관리를 위한 serializer"""
    motionType = serializers.CharField(source='motion_name', max_length=100)

    class Meta:
        model = MotionType
        fields = ['id', 'motionType', 'description', 'max_dtw_distance']
        read_only_fields = ['id', 'max_dtw_distance']

class SensorDeviceSerializer(serializers.ModelSerializer):
    """SensorDevice 모델 관리를 위한 serializer"""
    class Meta:
        model = SensorDevice
        # API를 통해 다룰 필드 목록
        fields = ['id', 'company', 'device_uid', 'name', 'api_key', 'is_active', 'created_at']
        # 서버에서 자동으로 생성/결정되어야 하므로, 클라이언트가 직접 쓸 수 없는 필드
        read_only_fields = ['id', 'company', 'api_key', 'created_at']

class UserRecordingSerializer(serializers.ModelSerializer):
    """UserRecording 모델 관리를 위한 serializer"""
    class Meta:
        model = UserRecording
        fields = ["id", "user", "motion_type", "score", "sensor_data_json", "recorded_at"]
        read_only_fields = ["id", "recorded_at"]

class EvaluationRequestSerializer(serializers.Serializer):
    """Unity로부터 평가 요청을 받을 때의 전체 데이터 형식"""
    motionName = serializers.CharField()
    empNo = serializers.CharField()
    # sensorData가 '딕셔셔너리들의 리스트' 형태인지만 검증.
    sensorData = serializers.ListField(child=serializers.DictField())

class MotionSerializer(serializers.ModelSerializer):
    """ 모델 관리를 위한 serializer"""
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
            "motionName",
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
