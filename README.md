# Abnormal Data Detection System

이 시스템은 센서 데이터를 수집하고 이상 징후를 감지하는 FastAPI 기반 애플리케이션입니다.

## 기능

- FastAPI 기반의 REST API
- InfluxDB를 사용한 원시 데이터 저장
- 10분마다 데이터 이상 감지
- ScyllaDB를 사용한 이상 데이터 관리
- 1분마다 이상 데이터 모니터링

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. InfluxDB 설정:
- InfluxDB를 설치하고 실행
- 새로운 버킷과 토큰 생성

3. ScyllaDB 설정:
- ScyllaDB를 설치하고 실행

4. 환경 변수 설정:
- .env 파일의 설정값을 실제 환경에 맞게 수정

## 실행 방법

```bash
python main.py
```

서버는 기본적으로 http://localhost:8000 에서 실행됩니다.

## API 엔드포인트

### 센서 데이터 입력
POST /sensor-data
```json
{
    "sensor_id": "sensor1",
    "value": 95.5,
    "timestamp": "2023-12-01T12:00:00Z"  // 선택사항
}
```

### 이상 데이터 조회
GET /abnormal-data/{sensor_id}

## 모니터링

- 10분마다 자동으로 이상 데이터 감지
- 1분마다 이상 데이터의 정상화 여부 확인
- 이상 데이터는 ScyllaDB에 저장되어 추적 관리
