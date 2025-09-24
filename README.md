## API 명세서

### 1. 인증 및 관리 API (웹 대시보드용)

*   `GET /api/auth/csrf`
    *   **목적**: CSRF 토큰 획득

*   `POST /api/auth/login`
    *   **목적**: 회사 계정 로그인
    *   **요청 예시**:
        ```json
        {
          "biz_no": "1234567890",
          "password": "a_secure_password123"
        }
        ```

*   `POST /api/auth/logout`
    *   **목적**: 로그아웃

*   `GET /api/auth/me`
    *   **목적**: 로그인 상태 확인

*   `GET, POST /api/courses/`
    *   **목적**: 교육 과정 목록 조회, 신규 생성

*   `GET, PUT, DELETE /api/courses/{id}/`
    *   **목적**: 특정 교육 과정 조회, 수정, 삭제

*   `GET, POST /api/enrollments/`
    *   **목적**: 수강 정보 목록 조회, 신규 등록
    *   **요청 예시**:
        ```json
        {
          "employee": "e1f2a3b4-c5d6-7890-1234-567890abcdef",
          "course": "c1d2e3f4-a5b6-7890-1234-567890abcdef"
        }
        ```

*   `GET, PUT, DELETE /api/enrollments/{id}/`
    *   **목적**: 특정 수강 정보 조회, 수정, 삭제

*   `GET, POST /api/ai/motion-types/`
    *   **목적**: 평가 과목 목록 조회, 신규 생성
    *   **요청 예시**:
        ```json
        {
          "motionName": "fire_exit",
          "description": "소화기 사용 실습"
        }
        ```

*   `GET, PUT, DELETE /api/ai/motion-types/{id}/`
    *   **목적**: 특정 평가 과목 조회, 수정, 삭제

*   `GET, POST /api/ai/devices/`
    *   **목적**: 훈련 장비 목록 조회, 신규 등록
    *   **요청 예시**:
        ```json
        {
          "name": "1번 훈련용 헬멧",
          "device_uid": "HELMET-001"
        }
        ```

*   `GET, PUT, DELETE /api/ai/devices/{id}/`
    *   **목적**: 특정 훈련 장비 조회, 수정, 삭제

*   `POST /api/ai/recordings/`
    *   **목적**: 모범/0점 동작 데이터 등록
    *   **요청 예시**:
        ```json
        {
          "motionName": "fire_exit",
          "scoreCategory": "reference",
          "sensorData": [
            {"flex1": 0.1, "gyro_x": 0.4, "gyro_y": 0.0, "gyro_z": 0.1},
            {"flex1": 0.2, "gyro_x": 0.5, "gyro_y": 0.0, "gyro_z": 0.1}
          ]
        }
        ```

### 2. 평가 API (Unity 클라이언트용)

*   `POST /api/ai/evaluate/`
    *   **목적**: 사용자 동작 평가 요청
    *   **헤더**: `X-API-Key`
    *   **요청 예시**:
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
