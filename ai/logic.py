# ai/logic.py

import numpy as np
from sklearn.decomposition import PCA
from dtaidistance import dtw_ndim

from .evaluator_cache import get_evaluator, clear_evaluator_cache
from .models import MotionType, MotionRecording, UserRecording
from organizations.models import Employee
from enrollments.models import Enrollment
from .serializers import UserRecordingSerializer
from .safty_training_ai import preprocess_sensor_data

def _run_pca_on_preprocessed_data(preprocessed_data_json: list):
    """ 이미 전처리된 JSON 데이터를 받아 PCA를 적용하고 1차원 데이터를 반환하는 헬퍼 함수 """
    if not preprocessed_data_json:
        return []
    
    import pandas as pd
    df = pd.DataFrame(preprocessed_data_json)
    
    if df.empty:
        return []

    pca = PCA(n_components=1)
    principal_component = pca.fit_transform(df.values)
    
    return principal_component.flatten().tolist()

def get_evaluation_graph_data(enrollment_id: int) -> dict:
    """ 특정 수강생의 최근 평가와 모범 동작을 그래프용 데이터로 가공하여 반환 """
    try:
        enrollment = Enrollment.objects.select_related('employee', 'course__motion_type').get(id=enrollment_id)
    except Enrollment.DoesNotExist:
        return {"error": "해당 수강 정보를 찾을 수 없습니다."}

    employee = enrollment.employee
    motion_type = enrollment.course.motion_type

    if not motion_type:
        return {"error": "해당 교육 과정에 연결된 평가 동작이 없습니다."}

    # 1. 사용자의 가장 최근 평가 기록 찾기
    latest_user_recording = UserRecording.objects.filter(user=employee, motion_type=motion_type).order_by('-recorded_at').first()
    if not latest_user_recording or not latest_user_recording.sensor_data_json:
        return {"error": "사용자의 평가 기록을 찾을 수 없습니다."}

    # 2. 대표적인 모범 동작 기록 찾기
    reference_recording = MotionRecording.objects.filter(motion_type=motion_type, score_category='reference').order_by('-recorded_at').first()
    if not reference_recording or not reference_recording.sensor_data_json:
        return {"error": "모범 동작 데이터를 찾을 수 없습니다."}

    # 3. 데이터 가져오기 및 변환
    # 사용자 데이터는 이미 PCA 변환된 결과가 저장되어 있으므로 그대로 사용
    user_graph_data = latest_user_recording.sensor_data_json
    # 모범 동작 데이터는 전처리된 2D 데이터이므로, PCA 변환을 수행
    ref_graph_data = _run_pca_on_preprocessed_data(reference_recording.sensor_data_json)

    return {
        "motionName": motion_type.motion_name,
        "userName": employee.name,
        "score": latest_user_recording.score,
        "userMotionGraphData": user_graph_data,
        "referenceMotionGraphData": ref_graph_data,
    }


def run_evaluation(motion_name: str, employee: Employee, raw_sensor_data: list) -> dict:
    """ 센서 데이터 리스트를 받아 평가하고, PCA결과를 저장하는 함수 """
    try:
        motion_type = MotionType.objects.get(motion_name=motion_name)
    except MotionType.DoesNotExist:
        return {"error": f"'{motion_name}' 동작을 찾을 수 없습니다."}

    try:
        evaluator = get_evaluator(motion_name)
        result = evaluator.evaluator_user_motion(raw_sensor_data, motion_type.max_dtw_distance)
        
        if "error" in result:
            return result

        # PCA 결과 저장 로직
        # 1. 평가에 사용된 데이터를 먼저 전처리
        preprocessed_data = preprocess_sensor_data(raw_sensor_data)
        
        # 2. 전처리된 데이터에 PCA를 적용하여 1차원 요약 데이터 생성
        pca_result_data = _run_pca_on_preprocessed_data(preprocessed_data.tolist())

        recording_data = {
            "user": employee.id,
            "motion_type": motion_type.id,
            "score": result.get("score"),
            "sensor_data_json": pca_result_data # 원본 대신 PCA 결과를 저장
        }
        
        serializer = UserRecordingSerializer(data=recording_data)
        if serializer.is_valid():
            serializer.save()
        else:
            print(f"사용자 평가 기록 저장 실패: {serializer.errors}")

        return result

    except Exception as e:
        print(f"[Error] Evaluation failed for {motion_name}: {e}")
        return {"error": f"평가 중 오류 발생: {str(e)}"}


def update_max_dtw_for_motion(motion_type: MotionType):
    """ 특정 MotionType에 대해 max_dtw_distance를 재계산하고 저장함. """
    reference_recordings = MotionRecording.objects.filter(motion_type=motion_type, score_category="reference")
    zero_score_recordings = MotionRecording.objects.filter(motion_type=motion_type, score_category="zero_score")

    if not reference_recordings.exists() or not zero_score_recordings.exists():
        print(f"'{motion_type.motion_name}'의 max_dtw_distance 계산을 위한 데이터 부족")
        return

    ref_motions = [rec.get_sensor_data_numpy() for rec in reference_recordings]
    zero_motions = [rec.get_sensor_data_numpy() for rec in zero_score_recordings]

    max_distances = []
    for ref_motion in ref_motions:
        for zero_motion in zero_motions:
            if ref_motion.size == 0 or zero_motion.size == 0:
                continue
            try:
                distance = dtw_ndim.distance(ref_motion, zero_motion, window=10)
                max_distances.append(distance)
            except Exception as e:
                print(f"DTW 거리 계산 중 오류 발생: {e}")

    if max_distances:
        new_max_dtw = max(max_distances) * 1.1
        motion_type.max_dtw_distance = new_max_dtw
        motion_type.save()
        print(f"'{motion_type.motion_name}'의 max_dtw_distance 업데이트: {new_max_dtw}")
        clear_evaluator_cache(motion_type.motion_name)
