# ai/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from organizations.models import Employee
from .models import SensorDevice, MotionType # .models에서 직접 import
from .serializers import EvaluationRequestSerializer, MotionSerializer
from .logic import run_evaluation

class MotionRecordingView(APIView):
    """
    모범 동작(reference) 또는 0점 동작(zero_score) 데이터를 받아
    전처리 후 DB에 저장합니다.
    """
    def post(self, request, *args, **kwargs):
        serializer = MotionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UnifiedEvaluationView(APIView):
    SUCCES_RESPONSE = {
            "ok": True,
            "detail": "평가가 완료되었습니다.",
        }
    
    def _try_get_sensor_device(self, api_key):
        try:
            device = SensorDevice.objects.get(api_key=api_key, is_active=True)
        except SensorDevice.DoesNotExist:
            return Response({"detail": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)
        
        return device
    
    def _try_get_employee(self, emp_no, device):
        try:
            employee = Employee.objects.get(emp_no=emp_no, company=device.company)
        except Employee.DoesNotExist:
            return Response({"detail": "해당 사원번호를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        return employee

    """
    Unity로부터 센서 데이터를 받아 즉시 평가하고 결과를 반환하는 API
    POST /api/ai/evaluate/
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return Response({"detail": "Missing X-API-Key"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 기기 정보를 가져옴
        device = self._try_get_sensor_device(api_key)

        serializer = EvaluationRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        motion_name = validated_data['motionName']
        emp_no = validated_data['empNo']
        readings = validated_data['sensorData'] # 키 이름 수정: readings -> sensorData

        # 직원 정보를 가져옴
        employee = self._try_get_employee(emp_no, device)

        evaluation_result = run_evaluation(
            motion_name=motion_name,
            employee=employee,
            raw_sensor_data=readings
        )

        if "error" in evaluation_result:
            return Response(evaluation_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.SUCCES_RESPONSE["evaluation"] = evaluation_result

        return Response(self.SUCCES_RESPONSE, status=status.HTTP_200_OK)