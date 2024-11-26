from abc import ABC, abstractmethod
from typing import List
from datetime import datetime, timedelta
from ..entities.sensor_data import SensorData, AbnormalData

class SensorRepository(ABC):
    @abstractmethod
    def save_sensor_data(self, data: SensorData) -> None:
        pass
    
    @abstractmethod
    def get_sensor_data_in_range(self, start_time: datetime, end_time: datetime) -> List[SensorData]:
        pass
    
    @abstractmethod
    def save_abnormal_data(self, data: AbnormalData) -> None:
        pass
    
    @abstractmethod
    def get_abnormal_data_by_sensor(self, sensor_id: str) -> List[AbnormalData]:
        pass
    
    @abstractmethod
    def get_active_abnormal_data(self) -> List[AbnormalData]:
        pass
    
    @abstractmethod
    def update_abnormal_data_status(self, abnormal_data: AbnormalData, new_status: str) -> None:
        pass
