from datetime import datetime
import pytz
from typing import Dict, List
from adapter.output.entity.sensor_data import SensorData
from adapter.output.entity.abnormal_data import AbnormalData
from adapter.output.interface.IsensorRepository import ISensorRepository
from py_singleton import singleton
@singleton
class MemorySensorRepository(ISensorRepository):
    def __init__(self):
        self.sensor_data: List[SensorData] = []
        self.abnormal_data: Dict[str, AbnormalData] = {}
        self.kst = pytz.timezone('Asia/Seoul')

    def save_sensor_data(self, sensor_data: SensorData) -> None:
        """센서 데이터를 저장합니다."""
        self.sensor_data.append(sensor_data)
        # 최대 10000개까지만 저장
        if len(self.sensor_data) > 10000:
            self.sensor_data = self.sensor_data[-10000:]

    def get_sensor_data_in_range(self, start_time: datetime, end_time: datetime) -> List[SensorData]:
        """주어진 시간 범위 내의 센서 데이터를 반환합니다."""
        return [
            data for data in self.sensor_data
            if start_time <= data.timestamp <= end_time
        ]

    def save_abnormal_data(self, sensor_id: str, value: float, threshold: float, timestamp: datetime) -> AbnormalData:
        """비정상 데이터를 저장합니다."""
        abnormal_data = AbnormalData(
            sensor_id=sensor_id,
            value=value,
            threshold=threshold,
            detection_timestamp=timestamp,
            normalization_timestamp=None
        )
        self.abnormal_data[sensor_id] = abnormal_data
        return abnormal_data

    def update_abnormal_data(self, abnormal_data: AbnormalData) -> None:
        """비정상 데이터를 업데이트합니다."""
        if abnormal_data.sensor_id in self.abnormal_data:
            self.abnormal_data[abnormal_data.sensor_id] = abnormal_data
            # 정상화된 경우 딕셔너리에서 제거
            if abnormal_data.normalization_timestamp is not None:
                del self.abnormal_data[abnormal_data.sensor_id]

    def get_abnormal_data(self) -> Dict[str, AbnormalData]:
        """현재 비정상 상태인 데이터를 반환합니다."""
        return self.abnormal_data

    def get_abnormal_data_by_id(self, sensor_id: str) -> AbnormalData | None:
        """특정 센서의 비정상 데이터를 반환합니다."""
        return self.abnormal_data.get(sensor_id)
