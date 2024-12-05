import random
from datetime import datetime
import pytz
from adapter.output.entity.sensor_data import SensorData


class RandomSensorDataGenerator:
    def __init__(self):
        self.kst = pytz.timezone('Asia/Seoul')
        self.topics = ['humidity/최율농장/2/1-1']
        self.last_values = {}  # 마지막 생성된 값을 저장

    def get_sensor_topic(self, sensor_id: str) -> str:
        # 토픽별 센서 설정
        """센서 ID에 해당하는 토픽을 반환"""
        for topic in self.topics:
            return topic
        return None

    def generate_sensor_data(self, sensor_id):
        """임의의 센서 데이터를 생성합니다."""
        if sensor_id is None:
            raise ValueError("Sensor ID must be provided.")

        # 첫 값 생성 시
        if sensor_id not in self.last_values:
            value = random.uniform(0, 100)
        else:
            # 이전 값의 ±10% 범위 내에서 랜덤값 생성
            last_value = self.last_values[sensor_id]
            max_change = last_value * 0.1  # 10% 변동폭
            value = last_value + random.uniform(-max_change, max_change)

            # 값 범위 제한 (0-100)
            value = max(0, min(100, value))

        # 현재 값을 저장
        self.last_values[sensor_id] = value

        # 이상치 생성 (5% 확률)
        return SensorData(
            sensor_id=sensor_id,
            value=round(value, 2),
            timestamp=datetime.now(self.kst),
        )

if __name__ == "__main__":
    generator = RandomSensorDataGenerator()
    sensor_data = generator.generate_sensor_data('humidity/최율농장/2/1-1')
    print(sensor_data)