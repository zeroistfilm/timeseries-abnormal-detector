import datetime

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

    async def multiAlarmMonitor(self, farmIdx: int, sector: int, measurements: list[MeasurementOperation]):
        """
        다수의 알람 조건을 처리하는 통합 함수.

        Args:
            farmIdx (int): 농장 ID
            sector (int): 구역 ID
            measurements (List[MeasurementOperation]): 알람 설정 정보 리스트
        """

        resultTimes = []
        for measurement in measurements:
            result, times = await self.alarmMonitor(farmIdx, sector, measurement)
            # measurement.skipTimeRange
            resultTimes.append(times)

        overlaps = self.find_overlapping_intervals(resultTimes)

        return overlaps

    def find_overlapping_intervals(self, resultTimes):
        # resultTimes는 [ [ (start, end), (start, end), ...],
        #                  [ (start, end), (start, end), ...], ... ] 형태의 리스트
        # 서로 다른 list(각 measurement 결과) 간 겹치는 구간을 찾기 위해 모든 쌍 비교
        if not resultTimes:
            return []

        if len(resultTimes) == 1:
            return resultTimes[0]
        # 첫 번째 measurement 결과를 기준으로 시작해 다음 measurement들과 비교
        base_intervals = resultTimes[0]
        overlapping = []

        # 모든 measurement들의 intervals와 비교
        for other_measurements in resultTimes[1:]:
            for base_start, base_end in base_intervals:
                for other_start, other_end in other_measurements:
                    # 두 구간이 겹치는지 확인
                    # 겹치는 조건: base_start < other_end and other_start < base_end
                    if base_start < other_end and other_start < base_end:
                        # 겹치는 구간은 start는 max(base_start, other_start),
                        # end는 min(base_end, other_end)
                        overlap_start = max(base_start, other_start)
                        overlap_end = min(base_end, other_end)
                        overlapping.append((overlap_start, overlap_end))

        return overlapping

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

        # InfluxDB 쿼리 실행 (공통)
        result = await self.influxdbClient.alarmQueryExecutor(farmIdx, sector, measurement)
        highlight_ranges = self._highlight_ranges(result['stateDuration'], targetTime)

        # 시간 필터링 적용
        filtered_ranges = self._expandAndFilterTimeRanges(highlight_ranges, measurement.skipTimeRange)

        print(filtered_ranges)
        # method에 따라 제목 생성
        if method == 'gradient':
            gradient = detail['gradient']
            trend = detail['trend']
            title = f"{measurement.measurement} changed more than {gradient} ({trend}) for {targetTime} minutes"
        elif method == 'threshold':
            threshold = (detail.get('min'), detail.get('max'))
            title = f"{measurement.measurement} between {threshold[0]} and {threshold[1]} for {targetTime} minutes"
        else:
            raise ValueError(f"Unsupported method: {method}")

        # 필터링된 데이터로 그래프 생성
        self._plot_data(result, filtered_ranges, title)

        return result, filtered_ranges

    def _expandAndFilterTimeRanges(self, times, skipTimeRange):
        """
        시간 범위를 분 단위로 확장한 후, skipTimeRange에 해당하는 시간을 제외하고 필터링합니다.

        Args:
            times (list of tuples): [(startTime, endTime)] 시간 범위 리스트
            skipTimeRange (list of tuples): 제외할 시간대 [(skipStartHour, skipEndHour)]

        Returns:
            list of tuples: 필터링된 시간 범위 리스트
        """
        expanded_times = []

        # Step 1: 시간 범위를 1분 단위로 확장
        for startTime, endTime in times:
            current_time = startTime
            while current_time < endTime:
                expanded_times.append(current_time)
                current_time += timedelta(minutes=1)

        # Step 2: 시간 필터링 (skipTimeRange 제외)
        filtered_times = [
            time for time in expanded_times
            if not any(skipStart <= time.hour < skipEnd for skipStart, skipEnd in skipTimeRange)
        ]

        # Step 3: 필터링된 시간대를 다시 범위로 결합
        if not filtered_times:
            return []

        filtered_ranges = []
        range_start = filtered_times[0]
        for i in range(1, len(filtered_times)):
            if (filtered_times[i] - filtered_times[i - 1]) > timedelta(minutes=1):
                filtered_ranges.append((range_start, filtered_times[i - 1]))
                range_start = filtered_times[i]
        filtered_ranges.append((range_start, filtered_times[-1]))

        return filtered_ranges

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
        import matplotlib.dates as mdates

        fig, ax1 = plt.subplots(figsize=(24, 12))  # 메인 축 생성

        if 'merged' in result:
            first_time = [point[0] for point in result['merged']]
            first_value = [point[1] for point in result['merged']]
            ax1.plot(first_time, first_value, label="merged", linestyle='-', marker='o', color='tab:blue')
        else:
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
            ax4.plot(operation_time, operation_value, label="Operation Result", linestyle='-', marker='s',
                     color='tab:green')
            ax4.set_ylabel("Operation Result", color='tab:green')
            ax4.tick_params(axis='y', labelcolor='tab:green')

        # 음영 범위 추가
        for i, (start, end) in enumerate(highlight_ranges):
            ax1.axvspan(start, end, color='red', alpha=0.3,
                        label="Alarm Range" if i == 0 else "")

        # 시간축 설정: 1시간 단위로 레이블 표시
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        fig.autofmt_xdate()  # 날짜 포맷을 자동으로 맞추기 위해 호출

        # 그래프 제목 및 설정
        plt.title(title)
        ax1.set_xlabel("Time")
        fig.tight_layout()

        # 격자 표시 (메인 x축 기준)
        ax1.grid(True, which='both', linestyle='--', alpha=0.7)

        # 범례 설정
        fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
        plt.show()


if __name__ == "__main__":
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

        rules = [
            # {
            #     'name': 'high_thi_no_fan_low_humidity',
            #     'conditions': [
            #         MeasurementOperation(
            #             measurement=['THI'],
            #             method='threshold',
            #             detail={'min':1700, 'max': 10000},  # 높은 온열지수
            #             targetTime=30,
            #             queryOption={
            #                 'method': 'merge',
            #                 'sub_function': 'mean'
            #             }
            #         ),
            #         MeasurementOperation(
            #             measurement=['tunnelFanStatus'],
            #             method='threshold',
            #             detail={'min':0, 'max':0.2},  # 터널팬 미작동
            #             targetTime=30,
            #             queryOption={
            #                 'method': 'merge',
            #                 'sub_function': 'mean'
            #             }
            #         ),
            #         MeasurementOperation(
            #             measurement=['relativeHumidity'],
            #             method='threshold',
            #             detail={'min': 60, 'max': 100},  # 상대습도 높음
            #             targetTime=30,
            #             queryOption={
            #                 'method': 'merge',
            #                 'sub_function': 'mean'
            #             }
            #         )
            #     ],
            #     'logic': 'AND',
            #     'targetTime': 30,
            #     'message': '온열지수가 높고 터널팬이 작동하지 않으며 습도가 높습니다. 즉시 팬과 환경 상태를 점검하세요.'
            # },
            {
                'name': 'temp_out_of_range_dead_rising',
                'conditions': [
                    MeasurementOperation(
                        measurement=['temperature1'],
                        queryStartTime='-30d',
                        queryEndTime='now()',
                        aggregateWindowSize='1h',
                        aggregateMethod='mean',
                        movingAverageWindowSize='5',

                        method='gradient',
                        detail={'trend': 'down', 'gradient': 1},
                        targetTime=30,

                        # skipTimeRange=[(0, 2), (23, 24)],
                        # queryOption={
                        #     'method': 'merge',
                        #     'sub_function': 'mean'
                        # }
                    )
                ],
                'logic': 'AND',
                'targetTime': 30,
                'message': '음수량 감소',
            },
            # {
            #     'name': 'high_static_pressure_no_min_vent',
            #     'conditions': [
            #         MeasurementOperation(
            #             measurement=['staticPressure'],
            #             method='threshold',
            #             detail={'min': 20, 'max': 50},  # 높은 정압
            #             targetTime=30,
            #             queryOption={
            #                 'method': 'merge',
            #                 'sub_function': 'mean'
            #             }
            #         ),
            #         MeasurementOperation(
            #             measurement=['minVentStatus'],
            #             method='threshold',
            #             detail={'min':-10,'max': 0},  # 최소 환기 미작동
            #             targetTime=30,
            #             queryOption={
            #                 'method': 'merge',
            #                 'sub_function': 'sum'
            #             }
            #         )
            #     ],
            #     'logic': 'AND',
            #     'targetTime': 30,
            #     'message': '정압이 높고 최소환기가 작동하지 않습니다. 환기 시스템을 점검하세요.'
            # },
            # {
            #     'name': 'low_water_high_culled_rate',
            #     'conditions': [
            #         MeasurementOperation(
            #             measurement=['totalWaterToday'],
            #             method='gradient',
            #             detail={'trend': 'down', 'gradient': 10},  # 급수량 급감
            #             targetTime=30,
            #             queryOption={
            #                 'method': 'merge',
            #                 'sub_function': 'sum'
            #             }
            #         ),
            #         MeasurementOperation(
            #             measurement=['culledPercent'],
            #             method='gradient',
            #             detail={'trend': 'up', 'gradient': 0.1},  # 도태율 증가
            #             targetTime=30,
            #             queryOption={
            #                 'method': 'merge',
            #                 'sub_function': 'mean'
            #             }
            #         )
            #     ],
            #     'logic': 'AND',
            #     'targetTime': 30,
            #     'message': '급수량이 감소하면서 도태율이 증가합니다. 급수 시스템과 병아리 상태를 확인하세요.'
            # }
        ]

        for rule in rules:
            measurements = rule['conditions']
            overlapTimes = await anomalyDetectService.multiAlarmMonitor(101, 2, measurements)
            if overlapTimes:
                print(f"Alarm Rule: {rule['name']}")
                print(f"Overlap Times: {overlapTimes}")
                print("message: ", rule['message'])
                print()
                import pandas as pd
                df = pd.DataFrame(overlapTimes, columns=["Start Time", "End Time"])

                # 중복된 시간 블록을 보기 좋게 정렬
                df['Duration'] = df['End Time'] - df['Start Time']
                df_sorted = df.sort_values(by=["Start Time", "End Time"]).reset_index(drop=True)
                print(df_sorted)

        # await anomalyDetectService.execute_alarm_rules(
        #     farmIdx=103,
        #     sector=2,
        #     rules=ALARM_RULES
        # )


    asyncio.run(main())
