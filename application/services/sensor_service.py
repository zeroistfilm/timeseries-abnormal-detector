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

    async def initialize(self):
        await self.influxdbClient.initializeClient()


    async def isAnomaly(self, farmIdx, sector, measurement, value):
        age = await self.influxdbClient.getCurrentAge(farmIdx, sector)
        rules = self.ruleClient.getRule(measurement, age)
        if not rules:
            return False
        ruleManager = RuleMatchDetectorManager()
        ruleManager.add_detectors(rules)
        context = RuleMatchContext(
            topic=measurement,
            current_value=value,
            timestamp=datetime.now(),
            history=None
        )
        ruleMatchedResult = ruleManager.detect_all(context)
        return ruleMatchedResult



    async def process_data(self, farmIdx, sector):
        age = await self.influxdbClient.getCurrentAge(farmIdx, sector)
        rawData = await self.influxdbClient.getRecentData(farmIdx, sector)
        if not rawData:
            raise Exception("No data")
        #룰이 있는 데이터만 필터링
        filteredData = {}
        for measurement in rawData.keys():
            for topic in rawData[measurement].keys():
                rules = self.ruleClient.getRule(measurement, age)
                if not rules:
                    continue
                filteredData[topic] = (measurement, rawData[measurement][topic], rules)
            # 룰 매칭기 생성
        for topic, (measurement, df, rules) in filteredData.items():
            ruleManager = RuleMatchDetectorManager()
            valueList = df["value"].tolist()[-1]
            last_time = df.index[-1]
            context = RuleMatchContext(
                topic=topic,
                current_value=valueList,  # 마지막 값
                timestamp=last_time,
                history=df
            )
            ruleManager.add_detectors(rules)
            ruleMatchedResult = ruleManager.detect_all(context)


            for result in ruleMatchedResult:
                self.scylladbClient.resisterTopicStatus(result)




if __name__ == '__main__':
    import asyncio
    async def main():
        service = SensorService()
        await service.initialize()
        # await service.process_data(101, 1)
        service.getFarmList()
    asyncio.run(main())

