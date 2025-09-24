# ai/logic.py

from dtaidistance import dtw_ndim
from .evaluator_cache import get_evaluator, clear_evaluator_cache
from .models import MotionType, MotionRecording
from organizations.models import Employee
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
        evaluator = get_evaluator(motion_name)

        result = evaluator.evaluator_user_motion(raw_sensor_data, motion_type.max_dtw_distance)
        
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


def update_max_dtw_for_motion(motion_type: MotionType):
    """
    특정 MotionType에 대해 max_dtw_distance를 재계산하고 저장함.
    """
    print(f"'{motion_type.motion_name}'의 max_dtw_distance 재계산을 시작합니다.")

    reference_recordings = MotionRecording.objects.filter(motion_type=motion_type, score_category="reference")
    zero_score_recordings = MotionRecording.objects.filter(motion_type=motion_type, score_category="zero_score")

    if not reference_recordings.exists() or not zero_score_recordings.exists():
        print("모범 동작 또는 0점 동작 데이터가 부족하여 max_dtw_distance를 계산할 수 없습니다.")
        return

    # numpy 배열로 변환
    # 리스트 내포 문법
    ref_motions = [rec.get_sensor_data_to_numpy() for rec in reference_recordings] # db에서 가져온 모범 동작 센서 데이터
    zero_motions = [rec.get_sensor_data_to_numpy() for rec in zero_score_recordings] # db에서 가져온 빵점 동작 센서 데이터

    max_distances = [] # 최대 dtw 거리를 담을 배열

    for ref_motion in ref_motions:
        for zero_motion in zero_motions:
            if ref_motion.size == 0 or zero_motion.size == 0:
                continue
            try:
                distance = dtw_ndim.distance(ref_motion, zero_motion, window=10)
                max_distances.append(distance)
            except Exception as e:
                print(f"DTW 거리 계산 중 오류 발생: {e}")
                continue

    if max_distances:
        new_max_dtw = max(max_distances)
        
        # 약간의 여유(10%)를 추가하여 최대값을 설정하면, 0점 동작보다 약간 나은 동작이 0점이 되는 것을 방지할 수 있음
        new_max_dtw *= 1.1 
        motion_type.max_dtw_distance = new_max_dtw
        motion_type.save()
        print(f"'{motion_type.motion_name}'의 새로운 max_dtw_distance: {new_max_dtw}")

        # 이 동작 유형에 대한 평가기 캐시를 지워서 다음 평가 시 새로운 max_dtw 값을 반영하도록 함
        clear_evaluator_cache(motion_type.motion_name)
    else:
        print("유효한 DTW 거리를 계산하지 못했습니다.")
