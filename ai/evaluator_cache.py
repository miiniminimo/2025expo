# ai/evaluator_cache.py
from .safty_training_ai import MotionEvaluator

# 동작 이름(motion_name)을 키로, MotionEvaluator 객체를 값으로 저장하는 캐시
evaluator_cache = {}

# 타입힌트 문법: motion_name 인자는 문자열(str)이고, 반환 값은 MotionEvaluator 객체임을 명시!
def get_evaluator(motion_name: str) -> MotionEvaluator:
    """
    캐시에서 평가기(Evaluator)를 가져오거나, 없으면 새로 생성하여 캐시에 저장 후 반환하는 함수.
    """
    # 1. 캐시에 해당 동작의 평가기가 있는지 확인
    if motion_name in evaluator_cache:
        # print(f"'{motion_name}' 평가기를 캐시에서 로드합니다.") # 디버깅용
        return evaluator_cache[motion_name]

    # 2. 캐시에 없으면, 새로 생성 (이때 DB 조회 발생)
    evaluator = MotionEvaluator(motion_name)
    evaluator_cache[motion_name] = evaluator  # 캐시에 저장
    return evaluator

# 인자 값 필수X(= None)
def clear_evaluator_cache(motion_name: str = None):
    """
    특정 동작 또는 전체 평가기 캐시를 비움
    모범/0점 동작 데이터가 변경되었을 때 호출해야 함
    """
    global evaluator_cache

    if motion_name:
        if motion_name in evaluator_cache:
            del evaluator_cache[motion_name]
            print(f"'{motion_name}' 평가기 캐시가 삭제되었습니다.")
    else:
        evaluator_cache = {}
        print("전체 평가기 캐시가 삭제되었습니다.")
