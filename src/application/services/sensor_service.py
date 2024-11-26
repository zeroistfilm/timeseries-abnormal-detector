from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Callable
from src.domain.models.sensor_data import SensorData
from src.domain.events.sensor_events import SensorDataReceived, AbnormalDataDetected, AbnormalDataNormalized
from src.domain.repositories.sensor_repository import SensorRepository

class SensorService:
    def __init__(self, repository: SensorRepository):
        self.repository = repository
        self.event_handlers: Dict[str, List[Callable]] = {
            'sensor_data_received': [],
            'abnormal_data_detected': [],
            'abnormal_data_normalized': []
        }
        self.kst = pytz.timezone('Asia/Seoul')
        self.threshold = 100.0  # 임계값 설정
    
    def add_event_handler(self, event_type: str, handler: Callable):
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    def _publish_event(self, event_type: str, event):
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                handler(event)
    
    def process_sensor_data(self, sensor_id: str, value: float, timestamp: datetime):
        # 센서 데이터 생성
        sensor_data = SensorData(sensor_id=sensor_id, value=value, timestamp=timestamp)
        
        # 데이터베이스에 저장
        self.repository.save_sensor_data(sensor_data)
        
        # 이벤트 발행
        self._publish_event('sensor_data_received', SensorDataReceived(sensor_data))
        
        # 임계값 체크
        if value > self.threshold:
            abnormal_data = self.repository.save_abnormal_data(sensor_id, value, self.threshold, timestamp)
            self._publish_event('abnormal_data_detected', AbnormalDataDetected(abnormal_data))
    
    def process_generated_data(self, data):
        """생성된 데이터를 처리합니다."""
        self.process_sensor_data(data['sensor_id'], data['value'], data['timestamp'])
    
    def monitor_abnormal_data(self):
        """비정상 데이터를 모니터링하고 정상화 여부를 확인합니다."""
        # 현재 시간 기준으로 최근 5분 데이터 확인
        end_time = datetime.now(self.kst)
        start_time = end_time - timedelta(minutes=5)
        
        # 최근 데이터 조회
        recent_data = self.repository.get_sensor_data_in_range(start_time, end_time)
        
        # 현재 비정상 상태인 센서들 확인
        abnormal_sensors = self.repository.get_abnormal_data()
        
        # 딕셔너리를 리스트로 변환하여 순회
        for sensor_id, abnormal_data in list(abnormal_sensors.items()):
            # 해당 센서의 최근 데이터 찾기
            sensor_recent_data = [data for data in recent_data if data.sensor_id == sensor_id]
            
            if sensor_recent_data:
                # 최근 3개의 연속된 데이터가 모두 정상이면 정상화로 판단
                latest_data = sorted(sensor_recent_data, key=lambda x: x.timestamp, reverse=True)[:3]
                if len(latest_data) >= 3 and all(data.value <= self.threshold for data in latest_data):
                    # 정상화 처리
                    abnormal_data.normalization_timestamp = latest_data[0].timestamp
                    self.repository.update_abnormal_data(abnormal_data)
                    
                    # 정상화 이벤트 발행
                    self._publish_event('abnormal_data_normalized', 
                                     AbnormalDataNormalized(abnormal_data))
