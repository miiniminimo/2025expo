## 최종 API 명세서 (사용 흐름 기준)

이 문서는 관리자가 새로운 평가 시나리오를 설정하고, Unity 클라이언트가 해당 시나리오로 평가를 진행하며, 웹에서 그 결과를 조회하는 전체 과정을 순서대로 설명합니다.

---

### **1. 관리자 설정 흐름 (웹 대시보드)**

#### **1.1. CSRF 토큰 획득 (로그인 전 필수)**
*   **목적**: 웹사이트 보안(CSRF)을 위해, 로그인 API 호출 전에 반드시 필요한 보안 토큰을 발급받음.
*   **API**: `GET /api/auth/csrf`
*   **요청**: 없음
*   **설명**: 이 API를 호출하면, 브라우저의 쿠키에 `csrftoken`이 자동으로 저장됨.

#### **1.2. 관리자 로그인**
*   **목적**: 회사 계정으로 로그인하여 관리자 기능 사용 권한 획득.
*   **API**: `POST /api/auth/login`
*   **요청 예시**:
    ```json
    {
      "biz_no": "1234567890",
      "password": "a_secure_password123"
    }
    ```
*   **설명**: 요청 헤더에 `X-CSRFToken`으로 1.1에서 받은 토큰 값을 포함해야 함.

#### **1.3. 평가 과목(MotionType) 등록**
*   **목적**: '안전모 착용' 같은 새로운 평가 과목 생성.
*   **API**: `POST /api/ai/motion-types/`
*   **요청 예시**:
    ```json
    {
      "motionType": "fire_exit",
      "description": "화재시 행동 요령"
    }
    ```

#### **1.4. 훈련 장비(SensorDevice) 등록**
*   **목적**: Unity 장비 등록 및 API 키 발급.
*   **API**: `POST /api/ai/devices/`
*   **요청 예시**:
    ```json
    {
      "name": "1번 훈련용 헬멧",
      "device_uid": "HELMET-001"
    }
    ```

#### **1.5. 직원 수강 등록**
*   **목적**: 특정 직원을 특정 교육 과정에 등록.
*   **API**: `POST /api/enrollments/`
*   **요청 예시**:
    ```json
    {
      "employee": "e1f2a3b4-c5d6-7890-1234-567890abcdef",
      "course": "c1d2e3f4-a5b6-7890-1234-567890abcdef"
    }
    ```

---

### **2. Unity 클라이언트 평가 흐름**

#### **2.1. 모범/0점 동작 데이터 등록**
*   **목적**: AI 평가 기준 데이터 저장.
*   **API**: `POST /api/ai/recordings/`
*   **요청 예시**:
    ```json
    {
      "motionName": "fire_exit",
      "scoreCategory": "reference",
      "sensorData": [
        {"flex1": 0.1, "gyro_x": 0.4, "gyro_y": 0.0, "gyro_z": 0.1},
        {"flex1": 0.2, "gyro_x": 0.5, "gyro_y": 0.0, "gyro_z": 0.1},
        ...
        {"flex1": 0.5, "gyro_x": 0.3, "gyro_y": 0.1, "gyro_z": 0.3}
      ]
    }
    ```

#### **2.2. 사용자 동작 평가 요청**
*   **목적**: 사용자의 동작을 측정하여 서버에 점수 요청.
*   **API**: `POST /api/ai/evaluate/`
*   **요청 예시**:
    *   **Header**: `X-API-Key: <1.4에서 발급받은 API 키>`
    *   **Body**:
        ```json
        {
          "motionName": "fire_exit",
          "empNo": "EMP001",
          "sensorData": [
            {"flex1": 0.15, "gyro_x": 0.42, "gyro_y": 0.1, "gyro_z": 0.0},
            {"flex1": 0.22, "gyro_x": 0.51, "gyro_y": 0.1, "gyro_z": 0.0}
          ]
        }
        ```

---

### **3. 결과 조회 흐름 (웹 대시보드)**

#### **3.1. 최근 평가 그래프 데이터 조회**
*   **목적**: 특정 수강 기록에 대한 가장 최근 평가를 그래프로 시각화하기 위한 데이터 조회.
*   **API**: `GET /api/enrollments/{id}/latest-evaluation-graph/`
*   **설명**: `{id}`에는 조회하려는 수강 정보(`enrollment`)의 ID를 넣음.
