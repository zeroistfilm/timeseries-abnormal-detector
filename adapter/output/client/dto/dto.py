from datetime import datetime, timezone, timedelta
from typing import List
from dataclasses import dataclass, field
import re

@dataclass
class MeasurementOperation:
    measurement: List[str] = field(default_factory=list)
    queryStartTime: str = "-1d"
    queryEndTime: str = "now()"
    aggregateWindowSize: str = "10m"
    movingAverageWindowSize: str = "6"
    aggregateMethod: str = "mean"


    operator: str = ""
    method: str = ""
    detail: dict = field(default_factory=dict)
    targetTime: int = 0
    queryOption: dict = field(default_factory=dict)
    skipTimeRange: List[tuple] = field(default_factory=list)

    def __post_init__(self):
        self.validate()

        print(self.queryStartTime)

    def validate(self):
        # measurement의 길이 검증
        if not (1 <= len(self.measurement) <= 2):
            raise ValueError("measurement는 1개 또는 2개의 항목만 가질 수 있습니다.")

        if len(self.measurement) == 1:
            if self.operator:
                raise ValueError("measurement이 1개인 경우 operator는 필요하지 않습니다.")

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

            if not isinstance(self.detail['gradient'], (float, int)):
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

        if len(self.queryOption.keys()) > 0:
            if 'method' not in self.queryOption:
                raise ValueError("queryOption은 method detail이 필요합니다.")

            if self.queryOption['sub_function'] not in ['mean', 'sum']:
                raise ValueError("method는 'mean', 'sum' 중 하나여야 합니다.")




        self.queryStartTime = self._parse_and_convert_to_utc(self.queryStartTime)
        self.queryEndTime = self._parse_and_convert_to_utc(self.queryEndTime)

        if self.aggregateWindowSize[-1] not in ['d', 'h', 'm']:
            raise ValueError("aggregateWindowSize는 'd', 'h', 'm' 중 하나로 끝나야 합니다.")
        elif not self.aggregateWindowSize[:-1].isdigit():
            raise ValueError("aggregateWindowSize는 숫자로 시작해야 합니다.")

        if not self.aggregateMethod in ['mean', 'median', 'max', 'first','last']:
            raise ValueError("aggregateMethod는 'mean', 'median', 'max', 'first', 'last' 중 하나여야 합니다.")

        if not self.movingAverageWindowSize.isdigit():
            raise ValueError("movingAverageWindowSize는 숫자로 입력해주세요.")




    def _parse_and_convert_to_utc(self, query_time: str) -> str:
        """
        query_time 입력을 검증하고 UTC로 변환한 값을 반환합니다.

        Args:
            query_time (str): 입력된 시간 (예: '2024-12-13 KST', '2024-12-13_12:30 KST', '-1d')

        Returns:
            str: UTC 시간 문자열 (%Y-%m-%dT%H:%M:%SZ)
        """

        # 상대 시간 형식 (d, h)
        if query_time[-1] in ['d', 'h']:
            return query_time
        elif query_time == "now()":
            return query_time
        else:
            try:
                # KST를 UTC로 변환
                kst = timezone(timedelta(hours=9))
                if re.match(r"^\d{4}-\d{2}-\d{2}$", query_time):
                    date = datetime.strptime(query_time, "%Y-%m-%d").replace(tzinfo=kst)
                elif re.match(r"^\d{4}-\d{2}-\d{2}_\d{2}$", query_time):
                    date = datetime.strptime(query_time, "%Y-%m-%d_%H").replace(tzinfo=kst)
                elif re.match(r"^\d{4}-\d{2}-\d{2}_\d{2}:\d{2}$", query_time):
                    date = datetime.strptime(query_time, "%Y-%m-%d_%H:%M").replace(tzinfo=kst)
                elif re.match(r"^\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}$", query_time):
                    date = datetime.strptime(query_time, "%Y-%m-%d_%H:%M:%S").replace(tzinfo=kst)
                else:
                    raise ValueError(f"입력값 {query_time} 기대값 'YYYY-MM-DD', 'YYYY-MM-DD_HH', 'YYYY-MM-DD_HH:MM', 'YYYY-MM-DD_HH:MM:SS'")

                # UTC로 변환
                utc_time = date.astimezone(timezone.utc)
                return utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')

            except ValueError as e:
                raise ValueError(f"Invalid queryStartTime format: {query_time}. Error: {e}")

