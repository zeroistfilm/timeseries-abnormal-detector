import random
from datetime import datetime
from typing import List
import pytz

class DataGenerator:
    def __init__(self, device_count: int = 10, normal_range: tuple = (0, 100), abnormal_range: tuple = (101, 200)):
        self.device_count = device_count
        self.normal_range = normal_range
        self.abnormal_range = abnormal_range
        self.device_ids = [f"device_{i}" for i in range(device_count)]
        self.kst = pytz.timezone('Asia/Seoul')
        self.previous_values = {}  # 각 디바이스의 이전 값을 저장
        self.device_states = {}    # 각 디바이스의 상태를 저장 (정상/비정상)
    
    def _generate_next_value(self, device_id: str) -> float:
        """이전 값에서 ±20% 범위 내의 새로운 값을 생성합니다."""
        previous_value = self.previous_values.get(device_id)
        is_abnormal = self.device_states.get(device_id, False)
        
        # 이전 값이 없는 경우 초기값 생성
        if previous_value is None:
            if is_abnormal:
                return random.uniform(self.abnormal_range[0], self.abnormal_range[1])
            return random.uniform(self.normal_range[0], self.normal_range[1])
        
        # 이전 값에서 ±20% 범위 내의 변화
        max_change = previous_value * 0.2
        change = random.uniform(-max_change, max_change)
        new_value = previous_value + change
        
        # 값이 범위를 벗어나면 조정
        if is_abnormal:
            return max(min(new_value, self.abnormal_range[1]), self.abnormal_range[0])
        return max(min(new_value, self.normal_range[1]), self.normal_range[0])
    
    def generate_data(self) -> List[tuple]:
        """각 디바이스의 새로운 센서 데이터를 생성합니다."""
        current_time = datetime.now(self.kst)
        data = []
        
        for device_id in self.device_ids:
            # 20% 확률로 비정상 상태로 전환
            if device_id not in self.device_states:
                self.device_states[device_id] = random.random() < 0.2
            elif random.random() < 0.1:  # 10% 확률로 상태 변경
                self.device_states[device_id] = not self.device_states[device_id]
            
            # 새로운 값 생성
            value = self._generate_next_value(device_id)
            self.previous_values[device_id] = value
            data.append((device_id, value, current_time))
        
        return data
