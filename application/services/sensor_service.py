from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Callable
from adapter.output.entity.sensor_data import SensorData
from adapter.output.entity.sensor_events import SensorDataReceived, AbnormalDataDetected, AbnormalDataNormalized
from adapter.output.interface.IsensorRepository import ISensorRepository
from adapter.output.client.memory_sensor_repository import MemorySensorRepository
from domain.events.event_handlers import log_sensor_data_received, log_abnormal_data_detected, log_abnormal_data_normalized

class SensorService:
    def __init__(self):
        self.repository = MemorySensorRepository()


        self.event_handlers: Dict[str, List[Callable]] = {
            'sensor_data_received': [],
            'abnormal_data_detected': [],
            'abnormal_data_normalized': []
        }
        self.kst = pytz.timezone('Asia/Seoul')
        self.threshold = 45.0  # 임계값 수정
        self.data_history = {}
        self.abnormal_devices = {}
        self.latest_updates = {}
        self.normalized_devices = {}
        self.normalization_history = []
        self.stats = {
            'total_received': 0,
            'total_abnormal': 0,
            'total_normalized': 0
        }

        # Event handlers setup
        self.add_event_handler('sensor_data_received', log_sensor_data_received)
        self.add_event_handler('abnormal_data_detected', log_abnormal_data_detected)
        self.add_event_handler('abnormal_data_normalized', log_abnormal_data_normalized)

    def add_event_handler(self, event_type: str, handler: Callable):
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    def _publish_event(self, event_type: str, event):
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                handler(event)
    
    def _format_duration(self, duration: timedelta) -> str:
        total_seconds = duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        if hours > 0:
            return f"{hours}시간 {minutes}분 {seconds}초"
        elif minutes > 0:
            return f"{minutes}분 {seconds}초"
        else:
            return f"{seconds}초"

    def process_sensor_data(self, sensor_id: str, value: float, timestamp: datetime):
        # 통계 업데이트
        self.stats['total_received'] += 1
        
        # 데이터 히스토리 업데이트
        if sensor_id not in self.data_history:
            self.data_history[sensor_id] = []
        self.data_history[sensor_id].append({
            'value': value,
            'time': timestamp
        })
        
        # 5분 이전 데이터 제거
        cutoff_time = timestamp - timedelta(minutes=5)
        self.data_history[sensor_id] = [
            data for data in self.data_history[sensor_id]
            if data['time'] >= cutoff_time
        ]
        
        # 최신 데이터 업데이트
        self.latest_updates[sensor_id] = {
            'value': value,
            'time': timestamp
        }
        
        # 센서 데이터 생성 및 저장
        sensor_data = SensorData(sensor_id=sensor_id, value=value, timestamp=timestamp)
        self.repository.save_sensor_data(sensor_data)
        
        # 이벤트 발행
        self._publish_event('sensor_data_received', SensorDataReceived(sensor_data))
        
        # 임계값 체크 및 비정상 상태 처리
        if value > self.threshold:
            if sensor_id not in self.abnormal_devices:
                abnormal_data = self.repository.save_abnormal_data(sensor_id, value, self.threshold, timestamp)
                self.stats['total_abnormal'] += 1
                self.abnormal_devices[sensor_id] = {
                    'value': value,
                    'threshold': self.threshold,
                    'detection_time': timestamp
                }
                self._publish_event('abnormal_data_detected', AbnormalDataDetected(abnormal_data))
            else:
                self.abnormal_devices[sensor_id].update({'value': value})
        elif sensor_id in self.abnormal_devices:
            detection_time = self.abnormal_devices[sensor_id]['detection_time']
            abnormal_value = self.abnormal_devices[sensor_id]['value']
            
            abnormal_data = self.repository.get_abnormal_data_by_id(sensor_id)
            if abnormal_data:
                abnormal_data.normalization_timestamp = timestamp
                self.repository.update_abnormal_data(abnormal_data)
                
                self.stats['total_normalized'] += 1
                
                # 정상화 이력 추가
                normalization_record = {
                    'sensor_id': sensor_id,
                    'abnormal_value': abnormal_value,
                    'normal_value': value,
                    'detection_time': detection_time,
                    'normalization_time': timestamp,
                    'duration': self._format_duration(timestamp - detection_time)
                }
                
                self.normalized_devices[sensor_id] = {
                    'normalization_time': timestamp,
                    'detection_time': detection_time
                }
                self.normalization_history.append(normalization_record)
                
                del self.abnormal_devices[sensor_id]
                self._publish_event('abnormal_data_normalized', AbnormalDataNormalized(abnormal_data))

    def get_monitor_data(self):
        current_time = datetime.now(self.kst)
        
        # 모든 시간 데이터 수집
        all_times = set()
        for device_data in self.data_history.values():
            all_times.update(data['time'] for data in device_data)
        times = sorted(all_times)
        time_labels = [t.strftime('%H:%M:%S') for t in times]
        
        # 센서 데이터 준비
        sensor_data = {}
        for device_id, device_data in self.data_history.items():
            values = []
            time_value_map = {data['time']: data['value'] for data in device_data}
            for t in times:
                values.append(time_value_map.get(t))
            sensor_data[device_id] = values
        
        # 비정상 상태 디바이스 데이터 준비
        abnormal_devices_data = {}
        for device_id, data in self.abnormal_devices.items():
            duration = current_time - data['detection_time']
            abnormal_devices_data[device_id] = {
                'value': data['value'],
                'threshold': data['threshold'],
                'detection_time': data['detection_time'].strftime('%H:%M:%S'),
                'duration': self._format_duration(duration)
            }
        
        return {
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'stats': self.stats,
            'sensor_data': {
                'time': time_labels,
                'data': sensor_data
            },
            'threshold': self.threshold,
            'latest_updates': {
                device_id: {
                    'value': data['value'],
                    'time': data['time'].strftime('%H:%M:%S')
                }
                for device_id, data in sorted(
                    self.latest_updates.items(),
                    key=lambda x: x[1]['time'],
                    reverse=True
                )[:8]
            },
            'abnormal_devices': abnormal_devices_data,
            'normalized_devices': {
                device_id: {
                    'normalization_time': data['normalization_time'].strftime('%H:%M:%S'),
                    'duration': self._format_duration(data['normalization_time'] - data['detection_time']),
                    'abnormal_value': next(
                        (record['abnormal_value'] 
                         for record in reversed(self.normalization_history) 
                         if record['sensor_id'] == device_id),
                        None
                    )
                }
                for device_id, data in sorted(
                    self.normalized_devices.items(),
                    key=lambda x: x[1]['normalization_time'],
                    reverse=True
                )[:5]
            },
            'normalization_history': [
                {
                    'sensor_id': record['sensor_id'],
                    'abnormal_value': record['abnormal_value'],
                    'normal_value': record['normal_value'],
                    'detection_time': record['detection_time'].strftime('%H:%M:%S'),
                    'normalization_time': record['normalization_time'].strftime('%H:%M:%S'),
                    'duration': record['duration']
                }
                for record in sorted(
                    self.normalization_history,
                    key=lambda x: x['normalization_time'],
                    reverse=True
                )
            ]
        }

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
