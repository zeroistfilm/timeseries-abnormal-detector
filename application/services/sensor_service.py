from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Callable
from adapter.output.entity.sensor_data import SensorData
from adapter.output.entity.sensor_events import SensorDataReceived, AbnormalDataDetected, AbnormalDataNormalized
from adapter.output.interface.IsensorRepository import ISensorRepository
from adapter.output.client.memory_sensor_repository import MemorySensorRepository
from adapter.output.client.ruleClient import RuleClient
from adapter.output.client.InfluxdbClient import InfluxDBClient
from adapter.output.client.ScylladbClient import ScyllaDBClient
from domain.events.event_handlers import log_sensor_data_received, log_abnormal_data_detected, \
    log_abnormal_data_normalized
from domain.anomaly.plugin import RuleMatchDetectorManager, ThresholdDetector, RuleMatchContext

from py_singleton import singleton


@singleton
class SensorService:
    def __init__(self):
        self.repository = MemorySensorRepository()
        self.ruleClient = RuleClient()
        self.influxdbClient = InfluxDBClient()
        self.scylladbClient = ScyllaDBClient()

        self.previous_states = {}  # 이전 상태 저장
        self.change_logs = []  # 변경 기록 저장


        # self.data_history = {}
        # self.latest_updates = {}
        # self.abnormal_devices = {}
        # self.normalized_devices = {}  # 정상화된 디바이스 추가
        # self.normalization_history = []  # 정상화 이력 추가
        # self.stats = {
        #     'total_received': 0,
        #     'total_abnormal': 0,
        #     'total_normalized': 0
        # }
        #
        # # 타임존 설정
        # self.kst = pytz.timezone('Asia/Seoul')
        #
        # # 이벤트 핸들러 초기화
        # self.event_handlers = {
        #     'sensor_data_received': [],
        #     'abnormal_data_detected': [],
        #     'abnormal_data_normalized': []
        # }
        #
        # # Event handlers setup
        # self.add_event_handler('sensor_data_received', log_sensor_data_received)
        # self.add_event_handler('abnormal_data_detected', log_abnormal_data_detected)
        # self.add_event_handler('abnormal_data_normalized', log_abnormal_data_normalized)

    async def initialize(self):
        await self.influxdbClient.initializeClient()

    async def process_data(self, farmIdx, sector):
        # self.stats['total_received'] += 1
        # self.latest_updates[sensor_id] = timestamp

        rawData = await self.influxdbClient.getRecentData(farmIdx, sector)

        #룰이 있는 데이터만 필터링
        filteredData = {}
        for measurement in rawData.keys():
            for topic in rawData[measurement].keys():
                rules = self.ruleClient.getRule(farmIdx, sector, measurement, topic)
                if not rules:
                    continue
                filteredData[topic] = (measurement, rawData[measurement][topic], rules)

        # 룰 매칭기 생성
        self.ruleManager = RuleMatchDetectorManager()
        for topic, (measurement, df, rules) in filteredData.items():
            rule = rules['rules']

            valueList = df["value"].tolist()
            last_time = df.index[-1]

            context = RuleMatchContext(
                topic=topic,
                current_value=valueList[-1],  # 마지막 값
                timestamp=last_time,
                history=df
            )

            self.ruleManager.add_detectors(rule)
            ruleMatchedResult = self.ruleManager.detect_all(context)


            for result in ruleMatchedResult:

                self.scylladbClient.resisterTopicStatus(result)



    def process_sensor_data(self, sensor_id: str, value: float, timestamp: datetime, metadata: Dict = None,
                            sensor_type: str = 'temperature'):
        # 통계 업데이트
        self.stats['total_received'] += 1
        self.latest_updates[sensor_id] = timestamp

        # 이전 데이터 이력 조회
        history_data = self.data_history.get(sensor_id, [])[-5:]  # 최근 5개 데이터만

        # 규칙 조회
        rules = self.rule_client.getRule(sensor_id)

        # 컨텍스트 생성
        context = AnomalyContext(
            sensor_id=sensor_id,
            current_value=value,
            timestamp=timestamp,
            history=history_data
        )

        # 규칙 기반 감지기 설정
        self.anomaly_manager.add_detector(rules)

        # 이상 감지 수행
        detection_results = self.anomaly_manager.detect_all(context)
        anomaly_detected = any(result.is_anomaly for result in detection_results)

        if anomaly_detected:  # 비정상인 경우
            abnormal_results = [r for r in detection_results if r.is_anomaly]
            # 1. 기존에 감지된 비정상 상태가 있는지 확인
            if sensor_id in self.abnormal_devices:
                current_status = self.abnormal_devices[sensor_id]
                current_violations = set(current_status.get('violations', set()))
                new_violations = set()

                # 2. & 3. 기존 상태와 비교하여 심각도 확인 및 업데이트
                for result in abnormal_results:
                    violation_key = f"{result.details['rule_owner']}/{result.details['level']}"
                    new_violations.add(violation_key)

                # 가장 심각한 위반 찾기
                severity_order = {'severe': 3, 'warning': 2, 'interest': 1}
                most_severe = max(abnormal_results,
                                  key=lambda x: severity_order.get(x.details['level'], 0))

                # 상태 업데이트
                self.abnormal_devices[sensor_id].update({
                    'current_value': value,
                    'last_update': timestamp,
                    'violations': new_violations,
                    'most_severe': {
                        'level': most_severe.details['level'],
                        'rule_owner': most_severe.details['rule_owner'],
                        'description': most_severe.details['description']
                    }
                })

            else:
                # 4. 새로운 비정상 상태 생성
                # 가장 심각한 위반 찾기
                severity_order = {'severe': 3, 'warning': 2, 'interest': 1}
                most_severe = max(abnormal_results,
                                  key=lambda x: severity_order.get(x.details['level'], 0))

                violations = set(
                    f"{result.details['rule_owner']}/{result.details['level']}"
                    for result in abnormal_results
                )

                self.abnormal_devices[sensor_id] = {
                    'first_detected': timestamp,
                    'last_update': timestamp,
                    'current_value': value,
                    'violations': violations,
                    'most_severe': {
                        'level': most_severe.details['level'],
                        'rule_owner': most_severe.details['rule_owner'],
                        'description': most_severe.details['description']
                    }
                }

                # 통계 업데이트
                self.stats['total_abnormal'] += 1

        else:  # 정상인 경우
            # 1. 기존에 비정상 처리 상태였는지 확인
            if sensor_id in self.abnormal_devices:
                # 2. 정상화 처리
                abnormal_record = self.abnormal_devices[sensor_id]

                # 정상화 기록 생성
                normalization_record = {
                    'sensor_id': sensor_id,
                    'abnormal_value': abnormal_record['current_value'],
                    'normal_value': value,
                    'detection_time': abnormal_record['first_detected'],
                    'normalization_time': timestamp,
                    'duration': self._format_duration(timestamp - abnormal_record['first_detected']),
                    'most_severe': abnormal_record['most_severe']
                }

                # 정상화 이력 업데이트
                self.normalized_devices[sensor_id] = normalization_record
                self.normalization_history.append(normalization_record)
                if len(self.normalization_history) > 10:
                    self.normalization_history = self.normalization_history[-10:]

                # 비정상 상태 제거
                del self.abnormal_devices[sensor_id]

                # 통계 업데이트
                self.stats['total_normalized'] += 1

        # 데이터 이력 업데이트
        self.data_history.setdefault(sensor_id, []).append(
            SensorData(sensor_id, value, timestamp, metadata)
        )

    def get_monitor_data(self):
        """현재 모니터링 데이터를 반환합니다."""
        current_time = datetime.now(self.kst)

        # 모든 시간 데이터 수집
        all_times = set()
        for device_data in self.data_history.values():
            all_times.update(data['time'] for data in device_data)
        all_times = sorted(all_times)[-30:]  # 최근 30개 시점만

        # 시계열 데이터 준비
        time_labels = [t.strftime('%H:%M:%S') for t in all_times]

        # 센서별 데이터 준비
        sensor_data = {}
        for device_id, device_data in self.data_history.items():
            time_value_map = {data['time']: data['value'] for data in device_data}
            values = []
            for t in all_times:
                values.append(time_value_map.get(t))
            sensor_data[device_id] = values

        # 비정상 디바이스 데이터 준비
        abnormal_devices_data = {}
        for device_id, data in self.abnormal_devices.items():
            duration = current_time - data['detection_time']
            detector_result = next((r for r in data.get('detectors', [])
                                    if r.detector_name == 'threshold_detector'), None)

            # Get sensor type and threshold from detector result
            sensor_type = detector_result.details.get('sensor_type',
                                                      'temperature') if detector_result else 'temperature'
            threshold = detector_result.details.get('threshold', 45.0) if detector_result else 45.0

            # Get unit from threshold detector config
            config = self.threshold_detector.sensor_configs.get(sensor_type)
            unit = config.unit if config else '°C'

            abnormal_devices_data[device_id] = {
                'value': data['value'],
                'threshold': threshold,
                'detection_time': data['detection_time'].strftime('%H:%M:%S'),
                'duration': self._format_duration(duration),
                'reasons': data.get('reasons', []),
                'sensor_type': sensor_type,
                'unit': unit,
                'severity': data.get('severity', 1),
                'location': data.get('location'),
                'threshold_type': data.get('threshold_type')
            }

        # 최신 업데이트 데이터 준비
        latest_updates_data = {}
        for device_id, data in sorted(
                self.latest_updates.items(),
                key=lambda x: x[1]['time'],
                reverse=True
        )[:5]:
            latest_updates_data[device_id] = {
                'value': data['value'],
                'time': data['time'].strftime('%H:%M:%S')
            }

        return {
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'sensor_data': {
                'time': time_labels,
                'data': sensor_data,
                'metadata': {
                    'temp-1': {
                        'locations': {
                            'harim': {'threshold': 25.0},
                            'farm': {'threshold': 35.0}
                        },
                        'detector_threshold': self.threshold_detector.sensor_configs['temperature'].fixed_threshold
                    },
                    'temp-2': {
                        'locations': {
                            'harim': {'threshold': 27.0},
                            'farm': {'threshold': 33.0}
                        },
                        'detector_threshold': self.threshold_detector.sensor_configs['temperature'].fixed_threshold
                    },
                    'hum-1': {
                        'locations': {
                            'harim': {'threshold': 75.0},
                            'farm': {'threshold': 85.0}
                        },
                        'detector_threshold': self.threshold_detector.sensor_configs['humidity'].fixed_threshold
                    }
                }
            },
            'stats': self.stats,
            'latest_updates': latest_updates_data,
            'abnormal_devices': abnormal_devices_data,
            'normalized_devices': self.normalized_devices,
            'normalization_history': list(reversed(self.normalization_history))
        }

    def process_generated_data(self, data):
        """생성된 데이터를 처리합니다."""
        self.process_sensor_data(data['sensor_id'], data['value'], data['timestamp'], data.get('metadata', {}),
                                 data.get('sensor_type', 'temperature'))

    def monitor_abnormal_data(self):
        """비정상 데이터를 모니터링하고 정상화 여부를 확인합니다."""
        # 현재 시간 기준으로 최근 5분 데이터 확인
        end_time = datetime.now(self.kst)
        start_time = end_time - timedelta(minutes=5)

        # 최근 데이터 조회
        recent_data = self.repository.get_sensor_data_in_range(start_time, end_time)

        # 현재 비정상 상태인 센서들 확인
        abnormal_sensors = self.repository.get_abnormal_data()

        # 딕셔너리를 리스트로 변환하여 순회
        for sensor_id, abnormal_data in list(abnormal_sensors.items()):
            # 해당 센서의 최근 데이터 찾기
            sensor_recent_data = [data for data in recent_data if data.sensor_id == sensor_id]

            if sensor_recent_data:
                # 최근 3개의 연속된 데이터가 모두 정상이면 정상화로 판단
                latest_data = sorted(sensor_recent_data, key=lambda x: x.timestamp, reverse=True)[:3]
                if len(latest_data) >= 3 and all(data.value <= max(
                        r.details.get('threshold', 0) for r in self.anomaly_manager.detect_all(AnomalyContext(
                                sensor_id=sensor_id,
                                current_value=data.value,
                                timestamp=data.timestamp,
                                history=self.data_history[sensor_id],
                                metadata={
                                    'latest_update': self.latest_updates.get(sensor_id),
                                    'is_currently_abnormal': sensor_id in self.abnormal_devices
                                }
                        ))) for data in latest_data):
                    # 정상화 처리
                    abnormal_data.normalization_timestamp = latest_data[0].timestamp
                    self.repository.update_abnormal_data(abnormal_data)

                    # 정상화 이벤트 발행
                    self._publish_event('abnormal_data_normalized',
                                        AbnormalDataNormalized(abnormal_data))

    def get_abnormal_data(self):
        return self.repository.get_abnormal_data()

    def get_abnormal_data_by_id(self, sensor_id: str):
        return self.repository.get_abnormal_data_by_id(sensor_id)

    def add_event_handler(self, event_type: str, handler: Callable):
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)

    def _publish_event(self, event_type: str, event):
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                handler(event)

    def _format_duration(self, duration: timedelta) -> str:
        total_seconds = duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)

        if hours > 0:
            return f"{hours}시간 {minutes}분 {seconds}초"
        elif minutes > 0:
            return f"{minutes}분 {seconds}초"
        else:
            return f"{seconds}초"
