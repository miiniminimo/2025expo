# ai/permissions.py
from rest_framework.permissions import BasePermission
from .models import SensorDevice

class HasValidAPIKey(BasePermission):
    """
    요청 헤더의 X-API-Key 값이 유효한 SensorDevice의 키인지 확인하는 권한
    """
    message = "유효하지 않은 API 키입니다."

    def has_permission(self, request, view):
        # HTTP 헤더에서 'X-API-Key' 값을 가져옴
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            self.message = "X-API-Key 헤더가 필요합니다."
            return False

        # 해당 API 키를 가진 활성화된 SensorDevice가 존재하는지 확인
        try:
            # select_related: SensorDevice를 찾을 건데, 연결된 company 정보도 바로 쓸 거니까, 한 번에 두 테이블을 합쳐서 달라고 하는 것과 같음
            # SensorDevice 객체에 접근하는 것은 O(1)이나, company(외래키)를 사용할 때는 O(N)만큼의 시간 복잡도가 발생함(조인)
            device = SensorDevice.objects.select_related('company').get(api_key=api_key, is_active=True)
            # view나 request 객체에 device와 company 정보를 추가해두면 다음 단계에서 유용하게 사용 가능
            request.device = device
            request.company = device.company
        except SensorDevice.DoesNotExist:
            return False
        
        return True
