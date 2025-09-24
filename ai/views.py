# ai/views.py

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status

# --- Permissions ---
from .permissions import HasValidAPIKey
# 웹 대시보드용 권한 클래스는 organizations 앱에서 가져와 재사용
from organizations.views import IsCompanySession

# --- Models ---
from organizations.models import Employee, Company
from .models import MotionType, SensorDevice

# --- Serializers ---
from .serializers import EvaluationRequestSerializer, MotionSerializer, SensorDeviceSerializer, MotionTypeSerializer

# --- Logic ---
from .logic import run_evaluation, update_max_dtw_for_motion


# --- ViewSets & Views ---

class SensorDeviceViewSet(ModelViewSet):
    """
    로그인한 회사의 SensorDevice를 관리하는 API
    """
    serializer_class = SensorDeviceSerializer
    permission_classes = [IsCompanySession] # 웹 대시보드에 로그인한 회사만 접근 가능

    def get_queryset(self):
        # 자신의 회사에 속한 디바이스만 조회하도록 제한
        company_id = self.request.session.get("company_id")
        return SensorDevice.objects.filter(company_id=company_id)

    def perform_create(self, serializer):
        # 새 디바이스를 등록할 때, 현재 로그인한 회사 소속으로 자동 설정
        company_id = self.request.session.get("company_id")
        serializer.save(company_id=company_id)


class MotionTypeViewSet(ModelViewSet):
    """
    평가 동작 유형(MotionType)을 관리하는 API
    - GET /api/ai/motion-types/
    - POST /api/ai/motion-types/
    """
    queryset = MotionType.objects.all().order_by('motion_name')
    serializer_class = MotionTypeSerializer
    # 로그인한 회사 관리자만 접근 가능하도록 설정
    permission_classes = [IsCompanySession]


class MotionRecordingView(APIView):
    """
    모범 동작(reference) 또는 0점 동작(zero_score) 데이터를 받아
    전처리 후 DB에 저장하고, max_dtw_distance를 업데이트합니다.
    """
    # 이 API는 관리자/개발자용이므로, 추후 IsAdminUser 같은 권한을 추가하는 것이 좋음
    permission_classes = [IsCompanySession]
    def post(self, request, *args, **kwargs):
        serializer = MotionSerializer(data=request.data)
        if serializer.is_valid():
            motion_recording = serializer.save()
            update_max_dtw_for_motion(motion_recording.motion_type)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnifiedEvaluationView(APIView):
    """
    Unity로부터 센서 데이터를 받아 즉시 평가하고 결과를 반환하는 API
    POST /api/ai/evaluate/
    """
    permission_classes = [HasValidAPIKey]  # 커스텀 권한 클래스로 교체

    def _try_get_employee(self, emp_no: str, company: Company):
        try:
            return Employee.objects.get(emp_no=emp_no, company=company)
        except Employee.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        company = request.company
        serializer = EvaluationRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        motion_name = validated_data['motionName']
        emp_no = validated_data['empNo']
        readings = validated_data['sensorData']

        employee = self._try_get_employee(emp_no, company)
        
        if not employee:
            return Response({"detail": f"회사({company.name})에 해당 사원번호({emp_no})가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

        evaluation_result = run_evaluation(
            motion_name=motion_name,
            employee=employee,
            raw_sensor_data=readings
        )

        if "error" in evaluation_result:
            return Response(evaluation_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = {
            "ok": True,
            "detail": "평가가 완료되었습니다.",
            "evaluation": evaluation_result
        }
        return Response(response_data, status=status.HTTP_200_OK)
