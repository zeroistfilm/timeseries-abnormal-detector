from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
class SensorDataInput(BaseModel):
    sensor_id: str
    value: float
    timestamp: datetime

class AbnormalDataOutput(BaseModel):
    sensor_id: str
    value: float
    threshold: float
    detection_timestamp: datetime
    normalization_timestamp: Optional[datetime]
    status: str