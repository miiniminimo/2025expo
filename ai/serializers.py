# ai/serializers.py

from rest_framework import serializers
from .models import UserRecording, MotionRecording, MotionType

# --- 신규: 단순화된 평가 요청 Serializer ---

class EvaluationRequestSerializer(serializers.Serializer):
    """Unity로부터 평가 요청을 받을 때의 전체 데이터 형식"""
    motionName = serializers.CharField()
    empNo = serializers.CharField()
    # sensorData가 '딕셔셔너리들의 리스트' 형태인지만 검증.
    sensorData = serializers.ListField(child=serializers.DictField())

# --- 기존 Serializer들 --- 

class UserRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRecording
        fields = ["id", "user", "motion_type", "score", "sensor_data_json", "recorded_at"]
        read_only_fields = ["id", "recorded_at"]

class MotionSerializer(serializers.ModelSerializer):
    motionTypeName = serializers.SlugRelatedField(source="motion_type",
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
            "motionTypeName",
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
