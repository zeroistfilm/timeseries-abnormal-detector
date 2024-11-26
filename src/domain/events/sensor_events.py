from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..entities.sensor_data import SensorData, AbnormalData

@dataclass
class SensorDataReceived:
    sensor_data: SensorData

@dataclass
class AbnormalDataDetected:
    abnormal_data: AbnormalData

@dataclass
class AbnormalDataNormalized:
    abnormal_data: AbnormalData
