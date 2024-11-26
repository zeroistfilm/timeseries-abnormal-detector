from typing import Callable
from datetime import datetime, timedelta
import pytz
from .sensor_events import SensorDataReceived, AbnormalDataDetected, AbnormalDataNormalized
from ..entities.sensor_data import AbnormalData

class EventLogger:
    def __init__(self):
        self.abnormal_devices = {}
        self.latest_updates = {}
        self.normalized_devices = {}  # 현재 표시용 정상화 데이터
        self.normalization_history = []  # 전체 정상화 이력
        self.stats = {
            'total_received': 0,
            'total_abnormal': 0,
            'total_normalized': 0
        }
        self.kst = pytz.timezone('Asia/Seoul')
        self.threshold = 45.0  # 임계값을 35도로 수정
        self.data_history = {}  # 데이터 히스토리 추가
    
    def _format_duration(self, duration: timedelta) -> str:
        """시간 차이를 시:분:초 형식으로 변환합니다."""
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
    
    def get_monitor_data(self):
        current_time = datetime.now(self.kst)
        time_cutoff = current_time - timedelta(minutes=5)
        
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

        # 현재 비정상 상태인 디바이스들의 지속 시간 업데이트
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
    
    def log_sensor_data_received(self, event: SensorDataReceived):
        self.stats['total_received'] += 1
        current_time = event.sensor_data.timestamp
        
        # 데이터 히스토리에 추가
        if event.sensor_data.sensor_id not in self.data_history:
            self.data_history[event.sensor_data.sensor_id] = []
        self.data_history[event.sensor_data.sensor_id].append({
            'value': event.sensor_data.value,
            'time': current_time
        })
        
        # 최근 5분만 유지
        cutoff_time = current_time - timedelta(minutes=5)
        self.data_history[event.sensor_data.sensor_id] = [
            data for data in self.data_history[event.sensor_data.sensor_id]
            if data['time'] >= cutoff_time
        ]
        
        # 최신 데이터 업데이트
        self.latest_updates[event.sensor_data.sensor_id] = {
            'value': event.sensor_data.value,
            'time': current_time
        }
        
        # 임계값 체크
        if event.sensor_data.value > self.threshold:
            # 이미 비정상 상태가 아닌 경우에만 새로운 비정상 이벤트 생성
            if event.sensor_data.sensor_id not in self.abnormal_devices:
                abnormal_data = AbnormalData(
                    sensor_id=event.sensor_data.sensor_id,
                    value=event.sensor_data.value,
                    threshold=self.threshold,
                    detection_timestamp=current_time,
                    normalization_timestamp=None,
                    status='detected'
                )
                self.log_abnormal_data_detected(AbnormalDataDetected(abnormal_data=abnormal_data))
            else:
                # 이미 비정상 상태인 경우 값만 업데이트
                self.abnormal_devices[event.sensor_data.sensor_id].update({
                    'value': event.sensor_data.value
                })
        elif event.sensor_data.sensor_id in self.abnormal_devices:
            # 정상으로 복귀
            abnormal_data = AbnormalData(
                sensor_id=event.sensor_data.sensor_id,
                value=event.sensor_data.value,
                threshold=self.threshold,
                detection_timestamp=self.abnormal_devices[event.sensor_data.sensor_id]['detection_time'],
                normalization_timestamp=current_time,
                status='normalized'
            )
            self.log_abnormal_data_normalized(AbnormalDataNormalized(abnormal_data=abnormal_data))

    def log_abnormal_data_detected(self, event: AbnormalDataDetected):
        self.stats['total_abnormal'] += 1
        self.abnormal_devices[event.abnormal_data.sensor_id] = {
            'value': event.abnormal_data.value,
            'threshold': event.abnormal_data.threshold,
            'detection_time': event.abnormal_data.detection_timestamp
        }
    
    def log_abnormal_data_normalized(self, event: AbnormalDataNormalized):
        self.stats['total_normalized'] += 1
        if event.abnormal_data.sensor_id in self.abnormal_devices:
            detection_time = self.abnormal_devices[event.abnormal_data.sensor_id]['detection_time']
            abnormal_value = self.abnormal_devices[event.abnormal_data.sensor_id]['value']
            del self.abnormal_devices[event.abnormal_data.sensor_id]
            
            # 정상화 이력 생성
            normalization_record = {
                'sensor_id': event.abnormal_data.sensor_id,
                'abnormal_value': abnormal_value,
                'normal_value': event.abnormal_data.value,
                'detection_time': detection_time,
                'normalization_time': event.abnormal_data.normalization_timestamp,
                'duration': self._format_duration(event.abnormal_data.normalization_timestamp - detection_time)
            }
            
            # 현재 표시용 정상화 데이터 업데이트
            self.normalized_devices[event.abnormal_data.sensor_id] = {
                'detection_time': detection_time,
                'normalization_time': event.abnormal_data.normalization_timestamp
            }
            
            # 전체 이력에 추가
            self.normalization_history.append(normalization_record)
            
            # 현재 표시용 데이터는 최근 5개만 유지
            if len(self.normalized_devices) > 5:
                oldest_key = min(self.normalized_devices.keys(), 
                               key=lambda k: self.normalized_devices[k]['normalization_time'])
                del self.normalized_devices[oldest_key]
