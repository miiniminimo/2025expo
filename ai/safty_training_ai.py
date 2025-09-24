import numpy as np
from .models import MotionRecording
# df: pandas의 data frame 줄임말
import pandas as pd
import matplotlib.pyplot as plt
# dtw 계산
from dtaidistance import dtw_ndim
# 잡음 제거 필터
from scipy.signal import savgol_filter

# 각 센서의 값 변화를 그래프로 그려서 보여주는 함수
def graph_sensor_data(data_df, title="Sensor Data", show_plot=True):
    if data_df.empty:
        print(f"{title}을 그릴 데이터가 없습니다!")
        return
    
    # 센서의 갯수
    num_sensors = len(data_df.columns)

    # 그래프를 그릴 공간
    # 가로 15인치, 세로: 센서 갯수 * 2.5
    plt.figure(figsize=(15, num_sensors * 2.5))
    plt.suptitle(title, fontsize=16)

    # 각 칼럼별로 반복하면서 개별 그래프 그리기
    for i, col in enumerate(data_df.columns):
        plt.subplot(num_sensors, 1, i + 1)

        # 실제 그래프 그리기
        # index: 시간 흐름, data_df[col]: 해당 센서의 값
        plt.plot(data_df.index, data_df[col], label=col)

        # 각 센서 그래프의 작은 제목
        plt.title(f"{col}", loc="left", fontsize=12)

        # y축 이름
        plt.ylabel("value")

        # 그래프에 격자무늬 표시
        plt.grid(True, linestyle="--", alpha=0.6)

        # 각 선이 어떤 센서를 나타내는지 범례 표시
        plt.legend()
    
    plt.xlabel("frame")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    if show_plot:
        plt.show()

# 센서 데이터 다듬기(전처리)
# 클라이언트로부터 받은 센서 데이터(딕셔너리)를 전처리해서 numpy 배열(다차원 배열)로 반환하는 함수
def preprocess_sensor_data(raw_data_dicts) -> np.ndarray:
    # 처리할 데이터가 없으면 빈 배열 반환
    if not raw_data_dicts:
        return np.array([])
    
    df = pd.DataFrame(raw_data_dicts)

    # window_length: 데이터를 얼마나 넓게(몇 프레임) 보고 부드럽게 할지 결정 (홀수여야 함)
    # 데이터 길이가 필터 윈도우 길이보다 짧으면 오류가 나므로, 최소값을 보장
    window_length = min(df.shape[0] - (df.shape[0] % 2 == 0), 11)

    if window_length < 3:
        window_length = 3

    # 모든 센서에 대해서 잡음 제거 필터 적용
    # 일반적으로 다항식 차수 3을 사용
    smoothed_data = df.apply(lambda col: savgol_filter(col, window_length, 3))

    # 값의 크기 통일(정규화): 0에서 1사이의 값으로 만들기
    # 정규화된 데이터를 저장할 빈 DataFrame 만들기
    normalized_data = pd.DataFrame(index=smoothed_data.index, columns=smoothed_data.columns)

    # 각 센서 별로 예상되는 최소/최대 값을 정해서 정규화
    for col in smoothed_data.columns:
        # 아래 if문들은 모두 가정 값들임. 실제 센서 값들의 범위를 쓸 것
        if "flex" in col:
            # flex 센서가 가지는 실제 데이터 범위
            s_min = 0
            s_max = 100
        elif "gyro" in col:
            s_min = -30
            s_max = 30
        # 다른 센서가 있다면 elif나 else를 추가하여 센서 추가!
    
        range_sensor = s_max - s_min # 센서 값의 전체 범위
        
        # (현재 센서 값 - 센서의 최소 값) / 센서의 전체 범위
        # 해당 과정을 거치면 모든 센서 값이 0에서 1사이로 맞추어짐
        normalized_data[col] = (smoothed_data[col] - s_min) / range_sensor
    
    # dtw 라이브러리는 numpy 배열을 더 선호하므로, DataFrame을 numpy 배열로 변환하여 반환하기
    return normalized_data.values

# 동작을 평가하는 실질적인 함수(해당 클래스가 처음 만들어질 때 실행되는 부분)
class MotionEvaluator:
    def __init__(self, reference_motion_name):
        # 동작 이름
        self.reference_motion_name = reference_motion_name
        # 모델에서 모범 동작만 가져오도록 수정
        self.reference_motion_preprocessed = self.load_reference_move(score_category="reference")
    
    # db로부터 모범 동작 데이터를 불러와서 전처리된 numpy 배열 리스트로 반환하는 메서드
    def load_reference_move(self, score_category):
        reference_records = MotionRecording.objects.filter(
            motion_type__motion_name=self.reference_motion_name,
            score_category=score_category
        )
        preprocessed_motion = []
        for record in reference_records:
            numpy_data = record.get_sensor_data_to_numpy()
            if numpy_data.size > 0:
                preprocessed_motion.append(numpy_data)
        return preprocessed_motion
    
    # 사용자의 데이터를 전처리하는 메서드
    def preprocess_user_data(self, user_raw_data):
        return preprocess_sensor_data(user_raw_data)

    # 사용자의 동작을 실제로 평가하는 메인 함수
    def evaluator_user_motion(self, user_raw_data, max_dtw_distance: float):
        # 사용자의 원본 데이터(user_raw_data_df) 전처리
        preprocessed_user_data = self.preprocess_user_data(user_raw_data)

        if not self.reference_motion_preprocessed:
            return {"error": "모범 동작 데이터가 없습니다ㅜㅠ"}

        dtw_distances = []
        for ref_data in self.reference_motion_preprocessed:
            try:
                dtw_distance = dtw_ndim.distance(preprocessed_user_data, ref_data, window=10)
                dtw_distances.append(dtw_distance)
            except Exception as e:
                print(f"dtw 거리 계산 중 오류 발생: {e}")
                continue

        if not dtw_distances:
            return {"error": "모든 모범 동작과 비교 중 오류가 발생하여 dtw 거리를 계산할 수 없습니다."}

        average_dtw_distance = sum(dtw_distances) / len(dtw_distances)

        # 정규화 시, 외부에서 받은 max_dtw_distance 값을 사용
        if max_dtw_distance <= 0:
            # 0으로 나누는 것을 방지
            return {"error": "max_dtw_distance가 0보다 커야 합니다."}
        
        normalized_distance = min(average_dtw_distance / max_dtw_distance, 1.0)

        accuracy_percentage = max(0, (1 - normalized_distance)) * 100
        accuracy_percentage = min(100, accuracy_percentage)

        return {
            "evaluator_motion_name": self.reference_motion_name,
            "score": accuracy_percentage,
            "avg_dtw_distance": average_dtw_distance, # 디버깅 및 분석을 위해 추가 정보 반환
            "normalized_distance": normalized_distance,
        }
        
if __name__ == "__main__":
    print("센서 데이터 기반 평가 시스템 시작")

    # --------------------------------------

    # 예시 데이터
    """
    {
        "motionType": "fire_exit",
        "category": "reference",
        "sensorData": [
            {"flex1": 0.1, "flex2": 0.2, ... "flex5": 0.4, "gyro_x": 0.4 ... "gyro_z": 0.3},
            {"flex1": 0.4, "flex2": 0.6, ... "flex5": 0.3, "gyro_x": 0.2 ... "gyro_z": 0.1},
            ...
            {"flex1": 0.1, "flex2": 0.2, ... "flex5": 0.4, "gyro_x": 0.4 ... "gyro_z": 0.3},
        ],
        "ts": "2025-09-22T10:30:00.123Z"
    }
    """