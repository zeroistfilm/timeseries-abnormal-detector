if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from adapter.output.client.InfluxdbClient import InfluxDBClient
from datetime import timezone, timedelta
import numpy as np
import random
import json
from py_singleton import singleton

from adapter.output.client.dto.dto import MeasurementOperation



@singleton
class AnomalyDetectService:
    def __init__(self):
        self.influxdbClient = InfluxDBClient()

    async def alarmMonitor(self, farmIdx: int, sector: int, measurement: MeasurementOperation):
        """
        threshold, gradient 등 다양한 알람 조건을 처리하는 통합 함수.

        Args:
            farmIdx (int): 농장 ID
            sector (int): 구역 ID
            measurement (MeasurementOperation): 알람 설정 정보
        """
        if not isinstance(measurement, MeasurementOperation):
            raise ValueError("measurement must be MeasurementOperation type")

        # 공통 파라미터 추출
        method = measurement.method  # threshold, gradient 등
        targetTime = measurement.targetTime
        detail = measurement.detail

        # method에 따라 설정
        if method == 'gradient':
            gradient = detail['gradient']
            trend = detail['trend']
            queryType = {
                'method': 'gradient',
                'detail': {'trend': trend, 'gradient': gradient}
            }
            result = await self.influxdbClient.alarmQueryExecutor(farmIdx, sector, measurement)
            highlight_ranges = self._highlight_ranges(result['stateDuration'], targetTime)
            self._plot_data(result, highlight_ranges,
                            f"{measurement.measurement} changed more than {gradient} ({trend}) for {targetTime} minutes")

        elif method == 'threshold':
            threshold = (detail.get('min'), detail.get('max'))
            queryType = {
                'method': 'threshold',
                'detail': {'min': threshold[0], 'max': threshold[1]}
            }
            result = await self.influxdbClient.alarmQueryExecutor(farmIdx, sector, measurement)
            highlight_ranges = self._highlight_ranges(result['stateDuration'], targetTime)
            self._plot_data(result, highlight_ranges,
                            f"{measurement.measurement} between {threshold[0]} and {threshold[1]} for {targetTime} minutes")

        else:
            raise ValueError(f"Unsupported method: {method}")

        print(highlight_ranges)


    def _highlight_ranges(self, state_duration_data, target_time):
        """
        stateDuration 값이 target_time 이상인 구간을 추출.
        값이 감소하면 구간을 종료하고 초기화.
        """
        highlight_ranges = []  # 최종 음영 범위를 저장
        current_range_start = None  # 현재 구간의 시작점
        change_start = None  # 변화 시작점

        for i, (time, value) in enumerate(state_duration_data):
            # 값이 감소하면 현재 구간 종료 및 초기화
            if i > 0 and value < state_duration_data[i - 1][1]:
                if current_range_start is not None:
                    highlight_ranges.append((change_start, time))  # 이전 변화 구간 저장
                current_range_start = None
                change_start = None

            # 변화 시작점 감지
            if change_start is None and value > 0:
                change_start = time

            # target_time 이상인 구간의 시작
            if value >= target_time and current_range_start is None:
                current_range_start = time

            # target_time 이하로 돌아간 경우
            elif value < target_time and current_range_start is not None:
                highlight_ranges.append((change_start, time))  # 구간 저장
                current_range_start = None
                change_start = None  # 변화 시작점 초기화

        # 마지막 구간 처리
        if current_range_start is not None:
            highlight_ranges.append((change_start, state_duration_data[-1][0]))

        return highlight_ranges

    def _plot_data(self, result, highlight_ranges, title):
        """
        여러 Y축을 사용하여 데이터를 시각화하고 음영 범위를 추가합니다.
        """
        import matplotlib.pyplot as plt

        fig, ax1 = plt.subplots(figsize=(24, 12))  # 메인 축 생성

        # 첫 번째 Y축: firstData
        if 'firstData' in result:
            first_time = [point[0] for point in result['firstData']]
            first_value = [point[1] for point in result['firstData']]
            ax1.plot(first_time, first_value, label="firstData", linestyle='-', marker='o', color='tab:blue')

        if 'secondData' in result:
            second_time = [point[0] for point in result['secondData']]
            second_value = [point[1] for point in result['secondData']]
            ax1.plot(second_time, second_value, label="secondData", linestyle='-', marker='x', color='tab:blue')

        ax1.set_xlabel("Time")
        ax1.set_ylabel("First and Second Data", color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        # 두 번째 Y축: derivative
        if 'derivative' in result:
            ax2 = ax1.twinx()  # 두 번째 Y축 생성
            derivative_time = [point[0] for point in result['derivative']]
            derivative_value = [point[1] for point in result['derivative']]
            ax2.plot(derivative_time, derivative_value, label="derivative", linestyle='-', marker='x',
                     color='tab:orange')
            ax2.set_ylabel("Derivative", color='tab:orange')
            ax2.tick_params(axis='y', labelcolor='tab:orange')

        # 세 번째 Y축: stateDuration
        if 'stateDuration' in result:
            ax3 = ax1.twinx()  # 세 번째 Y축 생성
            ax3.spines['right'].set_position(("outward", 60))  # 세 번째 Y축을 오른쪽으로 이동
            state_time = [point[0] for point in result['stateDuration']]
            state_value = [point[1] for point in result['stateDuration']]
            ax3.plot(state_time, state_value, label="State Duration", linestyle='-', marker='s', color='tab:gray')
            ax3.set_ylabel("State Duration", color='tab:red')
            ax3.tick_params(axis='y', labelcolor='tab:red')

        if 'operationResult' in result:
            ax4 = ax1.twinx()
            ax4.spines['right'].set_position(("outward", 120))
            operation_time = [point[0] for point in result['operationResult']]
            operation_value = [point[1] for point in result['operationResult']]
            ax4.plot(operation_time, operation_value, label="Operation Result", linestyle='-', marker='s', color='tab:green')
            ax4.set_ylabel("Operation Result", color='tab:green')
            ax4.tick_params(axis='y', labelcolor='tab:green')

        # 음영 범위 추가
        for start, end in highlight_ranges:
            ax1.axvspan(start, end, color='red', alpha=0.3,
                        label="Alarm Range" if start == highlight_ranges[0][0] else "")

        # 그래프 제목 및 설정
        plt.title(title)
        ax1.set_xlabel("Time")
        fig.tight_layout()

        # 범례 설정
        fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
        plt.grid(True)
        plt.show()

if __name__ ==  "__main__":
    import asyncio
    import random
    import numpy as np
    import time
    #
    # ALARM_RULES = [
    #     {
    #         "name": "single_condition_example",
    #         "conditions": [
    #             {
    #                 "measurement": "averageTemperature",
    #                 "type": "threshold",
    #                 "detail": {"min": 0, "max": 15.0},  # 온도 15°C 이하
    #             }
    #         ],
    #         "logic": "AND",
    #         "targetTime": 10,
    #         "message": "온도가 15°C 이하입니다.",
    #     },
    #     {
    #         "name": "double_condition_example",
    #         "conditions": [
    #             {
    #                 "measurement": "outsideTemperatureExternal",
    #                 "type": "threshold",
    #                 "detail": {"min": -100, "max": 10},  # 히터 작동 중
    #             },
    #             {
    #                 "measurement": "averageTemperature",
    #                 "type": "threshold",
    #                 "detail": {"min": 0, "max": 15.0},  # 온도 15°C 이하
    #             },
    #         ],
    #         "logic": "AND",  # 두 조건 모두 충족
    #         "targetTime": 10,
    #         "message": "히터 작동 중인데도 온도가 15°C 이하입니다.",
    #     },
    #     {
    #         "name": "triple_condition_example",
    #         "conditions": [
    #             {
    #                 "logic": "AND",
    #                 "conditions": [  # 그룹 조건 1
    #                     {
    #                         "measurement": "outsideTemperatureExternal",
    #                         "type": "gradient",
    #                         "detail": {"trend": "up", "gradient": 2.0},
    #                     },
    #                     {
    #                         "measurement": "temperature",
    #                         "type": "threshold",
    #                         "detail": {"min": 20, "max": 30.0},
    #                     },
    #                 ],
    #             },
    #             {
    #                 "measurement": "humidity",
    #                 "type": "threshold",
    #                 "detail": {"min": 80.0, "max": None},  # 습도 80% 이상
    #             },
    #         ],
    #         "logic": "OR",  # 그룹 조건 1 OR 습도 조건
    #         "targetTime": 15,
    #         "message": "외부 온도 급상승과 습도가 높은 상태입니다.",
    #     },
    # ]



    async def main():
        anomalyDetectService = AnomalyDetectService()
        await anomalyDetectService.influxdbClient.initializeClient()

        measurement = MeasurementOperation(
            measurement=['relativeHumidity', 'averageTemperature'],
            operator='*',
            method='gradient',
            detail={
                'trend': 'up',
                'gradient': 0.1,

            },
            targetTime=10
        )
        await anomalyDetectService.alarmMonitor(103, 3, measurement)


        measurement = MeasurementOperation(
            measurement=['relativeHumidity', 'averageTemperature'],
            operator='*',
            method='threshold',
            detail={
                'min': 2300,
                'max': 10000,
            },
            targetTime=10
        )
        await anomalyDetectService.alarmMonitor(103, 3, measurement)


        measurement = MeasurementOperation(
            measurement=['relativeHumidity'],
            method='threshold',
            detail={
                'min': 82,
                'max': 84,
            },
            targetTime=30
        )
        await anomalyDetectService.alarmMonitor(103, 3, measurement)

        measurement = MeasurementOperation(
            measurement=['relativeHumidity'],
            method='gradient',
            detail={
                'trend': 'up',
                'gradient': 0.1,
            },
            targetTime=30
        )
        await anomalyDetectService.alarmMonitor(103, 3, measurement)

        # await anomalyDetectService.execute_alarm_rules(
        #     farmIdx=103,
        #     sector=2,
        #     rules=ALARM_RULES
        # )
    asyncio.run(main())