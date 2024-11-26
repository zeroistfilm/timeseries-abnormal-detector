from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class SensorData:
    sensor_id: str
    value: float
    timestamp: datetime
    
    @staticmethod
    def create(sensor_id: str, value: float, timestamp: Optional[datetime] = None) -> 'SensorData':
        if timestamp is None:
            timestamp = datetime.utcnow()
        return SensorData(sensor_id=sensor_id, value=value, timestamp=timestamp)

@dataclass
class AbnormalData:
    sensor_id: str
    value: float
    threshold: float
    detection_timestamp: datetime
    normalization_timestamp: Optional[datetime]
    status: str  # 'abnormal' or 'normalized'
    
    @staticmethod
    def create_from_sensor_data(sensor_data: SensorData, threshold: float) -> 'AbnormalData':
        return AbnormalData(
            sensor_id=sensor_data.sensor_id,
            value=sensor_data.value,
            threshold=threshold,
            detection_timestamp=sensor_data.timestamp,
            normalization_timestamp=None,
            status='abnormal'
        )
