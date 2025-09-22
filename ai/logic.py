# ai/logic.py

from .safty_training_ai import MotionEvaluator
from .models import MotionType, UserRecording, Employee
from .serializers import UserRecordingSerializer

def run_evaluation(motion_name: str, employee: Employee, raw_sensor_data: list) -> dict:
    """
    센서 데이터 리스트를 받아 평가를 수행하고 결과를 반환하는 핵심 함수
    """
    try:
        motion_type = MotionType.objects.get(motion_name=motion_name)
    except MotionType.DoesNotExist:
        return {"error": f"'{motion_name}' 동작을 찾을 수 없습니다."}

    try:
        evaluator = MotionEvaluator(motion_name)
        result = evaluator.evaluator_user_motion(raw_sensor_data)
        
        if "error" in result:
            return result

        recording_data = {
            "user": employee.id,
            "motion_type": motion_type.id,
            "score": result.get("score"),
            "sensor_data_json": raw_sensor_data
        }
        
        serializer = UserRecordingSerializer(data=recording_data)
        if serializer.is_valid():
            serializer.save()
        else:
            print(f"[Critical] 사용자 평가 기록 저장 실패: {serializer.errors}")

        return result

    except Exception as e:
        print(f"[Error] Evaluation failed for {motion_name}: {e}")
        return {"error": f"평가 중 오류 발생: {str(e)}"}
