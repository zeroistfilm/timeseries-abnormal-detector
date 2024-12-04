from typing import Dict
from datetime import datetime, timedelta
import logging
from adapter.output.entity.sensor_events import SensorDataReceived, AbnormalDataDetected, AbnormalDataNormalized
from adapter.output.entity.sensor_data  import AbnormalData
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_sensor_data_received(event: SensorDataReceived):
    logger.info(f"Sensor data received - Device: {event.sensor_data.sensor_id}, Value: {event.sensor_data.value}, Time: {event.sensor_data.timestamp}")
    
    # 데이터 히스토리에 추가
    data_history[event.sensor_data.sensor_id] = data_history.get(event.sensor_data.sensor_id, [])
    data_history[event.sensor_data.sensor_id].append({
        'value': event.sensor_data.value,
        'time': event.sensor_data.timestamp
    })
    
    # 최근 5분만 유지
    cutoff_time = event.sensor_data.timestamp - timedelta(minutes=5)
    data_history[event.sensor_data.sensor_id] = [
        data for data in data_history[event.sensor_data.sensor_id]
        if data['time'] >= cutoff_time
    ]
    
    # 최신 데이터 업데이트
    latest_updates[event.sensor_data.sensor_id] = {
        'value': event.sensor_data.value,
        'time': event.sensor_data.timestamp
    }
    
    # 임계값 체크
    if event.sensor_data.value > threshold:
        # 이미 비정상 상태가 아닌 경우에만 새로운 비정상 이벤트 생성
        if event.sensor_data.sensor_id not in abnormal_devices:
            abnormal_data = AbnormalData(
                sensor_id=event.sensor_data.sensor_id,
                value=event.sensor_data.value,
                threshold=threshold,
                detection_timestamp=event.sensor_data.timestamp,
                normalization_timestamp=None,
                status='detected'
            )
            log_abnormal_data_detected(AbnormalDataDetected(abnormal_data=abnormal_data))
        else:
            # 이미 비정상 상태인 경우 값만 업데이트
            abnormal_devices[event.sensor_data.sensor_id].update({
                'value': event.sensor_data.value
            })
    elif event.sensor_data.sensor_id in abnormal_devices:
        # 정상으로 복귀
        abnormal_data = AbnormalData(
            sensor_id=event.sensor_data.sensor_id,
            value=event.sensor_data.value,
            threshold=threshold,
            detection_timestamp=abnormal_devices[event.sensor_data.sensor_id]['detection_time'],
            normalization_timestamp=event.sensor_data.timestamp,
            status='normalized'
        )
        log_abnormal_data_normalized(AbnormalDataNormalized(abnormal_data=abnormal_data))

def log_abnormal_data_detected(event: AbnormalDataDetected):
    logger.warning(f"Abnormal data detected - Device: {event.abnormal_data.sensor_id}, Value: {event.abnormal_data.value}, Threshold: {event.abnormal_data.threshold}, Time: {event.abnormal_data.detection_timestamp}")
    
    abnormal_devices[event.abnormal_data.sensor_id] = {
        'value': event.abnormal_data.value,
        'threshold': event.abnormal_data.threshold,
        'detection_time': event.abnormal_data.detection_timestamp
    }

def log_abnormal_data_normalized(event: AbnormalDataNormalized):
    duration = event.abnormal_data.normalization_timestamp - event.abnormal_data.detection_timestamp
    duration_seconds = duration.total_seconds()
    
    if duration_seconds >= 3600:
        duration_str = f"{int(duration_seconds // 3600)}시간 {int((duration_seconds % 3600) // 60)}분 {int(duration_seconds % 60)}초"
    elif duration_seconds >= 60:
        duration_str = f"{int(duration_seconds // 60)}분 {int(duration_seconds % 60)}초"
    else:
        duration_str = f"{int(duration_seconds)}초"
    
    logger.info(f"Abnormal data normalized - Device: {event.abnormal_data.sensor_id}, Duration: {duration_str}")
    
    if event.abnormal_data.sensor_id in abnormal_devices:
        detection_time = abnormal_devices[event.abnormal_data.sensor_id]['detection_time']
        abnormal_value = abnormal_devices[event.abnormal_data.sensor_id]['value']
        del abnormal_devices[event.abnormal_data.sensor_id]
        
        # 정상화 이력 생성
        normalization_record = {
            'sensor_id': event.abnormal_data.sensor_id,
            'abnormal_value': abnormal_value,
            'normal_value': event.abnormal_data.value,
            'detection_time': detection_time,
            'normalization_time': event.abnormal_data.normalization_timestamp,
            'duration': duration_str
        }
        
        # 현재 표시용 정상화 데이터 업데이트
        normalized_devices[event.abnormal_data.sensor_id] = {
            'detection_time': detection_time,
            'normalization_time': event.abnormal_data.normalization_timestamp
        }
        
        # 전체 이력에 추가
        normalization_history.append(normalization_record)
        
        # 현재 표시용 데이터는 최근 5개만 유지
        if len(normalized_devices) > 5:
            oldest_key = min(normalized_devices.keys(), 
                           key=lambda k: normalized_devices[k]['normalization_time'])
            del normalized_devices[oldest_key]

def get_monitor_data():
    current_time = datetime.now(pytz.timezone('Asia/Seoul'))
    time_cutoff = current_time - timedelta(minutes=5)
    
    # 모든 시간 데이터 수집
    all_times = set()
    for device_data in data_history.values():
        all_times.update(data['time'] for data in device_data)
    times = sorted(all_times)
    time_labels = [t.strftime('%H:%M:%S') for t in times]
    
    # 센서 데이터 준비
    sensor_data = {}
    for device_id, device_data in data_history.items():
        values = []
        time_value_map = {data['time']: data['value'] for data in device_data}
        for t in times:
            values.append(time_value_map.get(t))
        sensor_data[device_id] = values

    # 현재 비정상 상태인 디바이스들의 지속 시간 업데이트
    abnormal_devices_data = {}
    for device_id, data in abnormal_devices.items():
        duration = current_time - data['detection_time']
        abnormal_devices_data[device_id] = {
            'value': data['value'],
            'threshold': data['threshold'],
            'detection_time': data['detection_time'].strftime('%H:%M:%S'),
            'duration': f"{int(duration.total_seconds() // 3600)}시간 {int((duration.total_seconds() % 3600) // 60)}분 {int(duration.total_seconds() % 60)}초"
        }

    return {
        'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
        'stats': {
            'total_received': sum(len(device_data) for device_data in data_history.values()),
            'total_abnormal': len(abnormal_devices),
            'total_normalized': len(normalization_history)
        },
        'sensor_data': {
            'time': time_labels,
            'data': sensor_data
        },
        'threshold': threshold,
        'latest_updates': {
            device_id: {
                'value': data['value'],
                'time': data['time'].strftime('%H:%M:%S')
            }
            for device_id, data in sorted(
                latest_updates.items(),
                key=lambda x: x[1]['time'],
                reverse=True
            )[:8]
        },
        'abnormal_devices': abnormal_devices_data,
        'normalized_devices': {
            device_id: {
                'normalization_time': data['normalization_time'].strftime('%H:%M:%S'),
                'duration': f"{int((data['normalization_time'] - data['detection_time']).total_seconds() // 3600)}시간 {int(((data['normalization_time'] - data['detection_time']).total_seconds() % 3600) // 60)}분 {int((data['normalization_time'] - data['detection_time']).total_seconds() % 60)}초",
                'abnormal_value': next(
                    (record['abnormal_value'] 
                     for record in reversed(normalization_history) 
                     if record['sensor_id'] == device_id),
                    None
                )
            }
            for device_id, data in sorted(
                normalized_devices.items(),
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
                normalization_history,
                key=lambda x: x['normalization_time'],
                reverse=True
            )
        ]
    }

data_history = {}
latest_updates = {}
abnormal_devices = {}
normalized_devices = {}
normalization_history = []
threshold = 45.0
