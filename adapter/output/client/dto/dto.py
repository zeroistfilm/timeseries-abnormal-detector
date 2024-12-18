
from typing import List
from dataclasses import dataclass, field
@dataclass
class MeasurementOperation:
    measurement: List[str] = field(default_factory=list)
    operator: str = ""
    method: str = ""
    detail: dict = field(default_factory=dict)
    targetTime: int = 0

    def __post_init__(self):
        self.validate()

    def validate(self):
        # measurement의 길이 검증
        if not (1 <= len(self.measurement) <= 2):
            raise ValueError("measurement는 1개 또는 2개의 항목만 가질 수 있습니다.")

        if len(self.measurement) == 1:
            if self.operator:
                raise ValueError("measurement이 1개인 경우 operation은 필요하지 않습니다.")

        if len(self.measurement) == 2:
            # operation 검증
            valid_operations = {'+', '-', '*', '/'}
            if self.operator not in valid_operations:
                raise ValueError(f"operation은 {valid_operations} 중 하나여야 합니다.")


        if self.method == "gradient":

            if 'trend' not in self.detail:
                raise ValueError("gradient method는 trend detail이 필요합니다.")

            if self.detail['trend'] not in ['up', 'down']:
                raise ValueError("trend는 'up', 'down' 중 하나여야 합니다.")

            if 'gradient' not in self.detail:
                raise ValueError("gradient method는 gradient detail이 필요합니다. float 형식으로 입력해주세요.")

            if not isinstance(self.detail['gradient'], float):
                raise ValueError("gradient detail은 float 형식으로 입력해주세요.")

        elif self.method == "threshold":

            if 'min' not in self.detail:
                raise ValueError("threshold method는 min detail이 필요합니다.")

            if not isinstance(self.detail['min'], (int, float)):
                raise ValueError("min detail은 int 또는 float 형식으로 입력해주세요.")

            if 'max' not in self.detail:
                raise ValueError("threshold method는 max detail이 필요합니다.")

            if not isinstance(self.detail['max'], (int, float)):
                raise ValueError("max detail은 int 또는 float 형식으로 입력해주세요.")

        else:
            raise ValueError("method는 gradient 또는 threshold 중 하나여야 합니다.")

        if not isinstance(self.targetTime, int):
            raise ValueError("targetTime detail은 int 형식으로 입력해주세요.")