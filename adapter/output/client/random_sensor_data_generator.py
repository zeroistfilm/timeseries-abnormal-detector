import random
from datetime import datetime
import pytz
from adapter.output.entity.sensor_data import SensorData

class RandomSensorDataGenerator:
    def __init__(self):
        self.kst = pytz.timezone('Asia/Seoul')

    def generate_sensor_data(self, sensor_id: str) -> SensorData:
        """임의의 센서 데이터를 생성합니다."""
        # 90%는 정상 데이터 (0-100), 10%는 비정상 데이터 (100-200)
        is_abnormal = random.random() < 0.1
        if is_abnormal:
            value = random.uniform(100, 200)
        else:
            value = random.uniform(0, 100)

        return SensorData(
            sensor_id=sensor_id,
            value=value,
            timestamp=datetime.now(self.kst)
        )
