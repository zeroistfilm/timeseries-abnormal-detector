from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AbnormalData:
    sensor_id: str
    value: float
    threshold: float
    detection_timestamp: datetime
    normalization_timestamp: Optional[datetime] = None
