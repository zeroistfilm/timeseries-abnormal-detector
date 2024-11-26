from dataclasses import dataclass
from datetime import datetime

@dataclass
class SensorData:
    sensor_id: str
    value: float
    timestamp: datetime
