from typing import List

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from adapter.output.client.ruleClient import RuleClient
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import pandas as pd
import datetime
from py_singleton import singleton


from adapter.output.client.dto.dto import MeasurementOperation

@singleton
class InfluxDBClient():
    def __init__(self):
        self.client = None

    async def initializeClient(self):
        # print("InfluxClient initializeClient")
        self.client = InfluxDBClientAsync(url="http://uniai-master1:30003",
                                          token="4zkj5SioQD4H3HFdD7SJz6PPs5Ua5H_Vs1Sfs4QcPN6kfdkdPZK3v1MZYiwPt4fb9w_fOunPD6kCI2x2PbHn1w==",
                                          org="prod",
                                          timeout=10_000)

    def dataExtractByBuilding(self, data):
        result = {}
        for i in data:
            for j in i.records:
                topic = j.values['topic']
                # if 'sector' in j.values and '_measurement' in j.values:
                #     buildingNo = j.values['sector']
                #     measurement = j.values['_measurement']
                # else:
                #     topic = j.values['topic']
                #     buildingNo = topic.split('/')[5]
                #     measurement = topic.split('/')[6]
                if '/dev/weather' in topic:
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[6]

                elif '/dev/choretime' in topic:
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[6]

                elif '/dev/bigdutchman' in topic:
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[6]

                elif '/dev/area' in topic:
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[2]
                elif '/coxlab' in topic:
                    # /coxlab/co2/507/choiyulfarm/2/1-1
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[2]
                elif '/dev/breedInfo' in topic:
                    # /dev\/breedInfo\/{farmIdx}\/[^\/]+\/{buildingNo}\/isBreedActive/
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[6]
                else:
                    buildingNo = j.values['sector']
                    measurement = topic.split('/')[2]

                # if measurement == "relativeHumidity":
                #     if value['value'].mean() > 100:
                #         mean_value = 100

                if "relativeHumidity" in measurement:
                    if j.values['_value'] > 100:
                        j.values['_value'] = 100

                if not buildingNo in result:
                    result[buildingNo] = {}
                if not measurement in result[buildingNo]:
                    result[buildingNo][measurement] = {}
                if not topic in result[buildingNo][measurement]:
                    result[buildingNo][measurement][topic] = {
                        'date': [],
                        'value': []
                    }

                result[buildingNo][measurement][topic]['date'].append(j.values['_time'])
                result[buildingNo][measurement][topic]['value'].append(j.values['_value'])

        for buildingNo in result.keys():
            for measurement in result[buildingNo].keys():
                for topic in result[buildingNo][measurement].keys():
                    merged_data = pd.DataFrame()
                    merged_data['date'] = result[buildingNo][measurement][topic]['date']
                    merged_data['value'] = result[buildingNo][measurement][topic]['value']
                    merged_data['date'] = merged_data['date'].dt.tz_convert('Asia/Seoul')
                    merged_data.sort_values(by='date', inplace=True)
                    merged_data.set_index('date', inplace=True)

                    result[buildingNo][measurement][topic] = merged_data

        return result

    async def getAllTopics(self):
        query = '''
        from(bucket: "ai_data")
        |> range(start:-1d)
        |> distinct(column: "topic")
        '''
        tables = await self.client.query_api().query(query=query)
        topics = []
        for table in tables:
            for record in table.records:
                topics.append(record.values['topic'])
        return topics

    async def getRecentData(self, farmIdx, sector):
        # /{sector}/: 기존에는 {sector} 뒤에 다른 숫자들이 나오는 경우도 매칭될 가능성이 있었습니다.
        # /{sector}\//: {sector} 바로 뒤에 슬래시(/)가 와야만 매칭되도록 제한했습니다.
        query = f'''
        from(bucket: "ai_data")
        |> range(start:-1h)
        |> filter(fn: (r) => 
                r.topic  =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\//
        )
        '''
        original = await self.client.query_api().query(query=query)
        modifiedData = self.dataExtractByBuilding(original)

        if str(sector) not in modifiedData:
            return None
        return modifiedData[str(sector)]

    async def getCurrentAge(self, farmIdx, sector) -> int:
        query = f'''
        from(bucket: "ai_data")
        |> range(start:-1h)
        |> filter(fn: (r) => 
                r.topic  =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/age/
        )
        |> last()
        '''
        original = await self.client.query_api().query(query=query)
        modifiedData = self.dataExtractByBuilding(original)
        if str(sector) not in modifiedData:
            return None
        for topic in modifiedData[str(sector)]['age'].keys():
            return int(modifiedData[str(sector)]['age'][topic].iloc[-1]['value'])

    async def getCurrentTemperature(self, farmIdx, sector, date=None):
        if date is None:
            startDate = "-15m"
            endDate = "now()"
        else:
            startDate, endDate = self.convertTimeForInflux(date)

        # farmIdx = self.farmIdxMatchingTable[farmIdx]
        query = f'''
        from(bucket: "ai_data")
              |> range(start: {startDate}, stop: {endDate})
              |> filter(fn: (r) =>
                r.topic =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/averageTemperature/
              )
        '''

        res = await self.client.query_api().query(query=query)

        try:
            modifiedData = self.dataExtractByBuilding(res)

            minValues = []
            maxValues = []
            for measurement, topicValue in modifiedData[str(sector)].items():
                for topic, value in topicValue.items():
                    minValue = value['value'].min()
                    maxValue = value['value'].max()

                    minValues.append(minValue)
                    maxValues.append(maxValue)

            avgMinValue = sum(minValues) / len(minValues)
            avgMaxValue = sum(maxValues) / len(maxValues)

            return avgMinValue, avgMaxValue

        except Exception as e:
            print(e)
            return None, None

    async def getCurrentHumidity(self, farmIdx, sector, date=None):
        if date is None:
            startDate = "-15m"
            endDate = "now()"
        else:
            startDate, endDate = self.convertTimeForInflux(date)

        # farmIdx = self.farmIdxMatchingTable[farmIdx]
        query = f'''
        from(bucket: "ai_data")
              |> range(start: {startDate}, stop: {endDate})
              |> filter(fn: (r) =>
                r.topic =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/relativeHumidity/ or
                r.topic =~ /coxlab\/humidity\/{farmIdx}/
              )
        '''

        res = await self.client.query_api().query(query=query)
        modifiedData = self.dataExtractByBuilding(res)

        # print(modifiedData)
        minValues = []
        maxValues = []
        for measurement, topicValue in modifiedData[str(sector)].items():
            for topic, value in topicValue.items():
                minValue = value['value'].min()
                maxValue = value['value'].max()

                minValues.append(minValue)
                maxValues.append(maxValue)

        avgMinValue = sum(minValues) / len(minValues)
        avgMaxValue = sum(maxValues) / len(maxValues)

        return avgMinValue, avgMaxValue

    async def getCurrentWaterTotal(self, farmIdx, sector, date=None) -> (datetime.datetime, int):
        if date is None:
            startDate = "-15m"
            endDate = "now()"
        else:
            startDate, endDate = self.convertTimeForInflux(date)

        # farmIdx = self.farmIdxMatchingTable[farmIdx]
        query = f'''
           from(bucket: "ai_data")
             |> range(start: {startDate}, stop: {endDate})
             |> filter(fn: (r) =>
                   r.topic  =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/totalWaterToday/ 
             ) 
           '''

        res = await self.client.query_api().query(query=query)
        modifiedData = self.dataExtractByBuilding(res)

        for key in ['totalWaterToday', 'todayWaterTotal']:
            if str(sector) in modifiedData and key in modifiedData[str(sector)]:
                try:
                    for topic, value in modifiedData[str(sector)][key].items():
                        last_row = value.iloc[-1]
                        water_value = last_row['value']
                        time = last_row.name
                        return time, water_value
                except Exception as e:
                    print(e)
                    return None, None
        #
        #
        # try:
        #     for key, value in modifiedData[str(sector)]['totalWaterToday'].items():
        #         last_row = value.iloc[-1]  # Get the last row
        #         water_value = last_row['value']  # Access the 'value' column
        #         time = last_row.name  # Access the index (assuming it's a datetime index)
        #         return time, water_value
        # except Exception as e:
        #     print(e)
        #     return None, None
        #
        # try:
        #     for key, value in modifiedData[str(sector)]['todayWaterTotal'].items():
        #         last_row = value.iloc[-1]  # Get the last row
        #         water_value = last_row['value']  # Access the 'value' column
        #         time = last_row.name  # Access the index (assuming it's a datetime index)
        #         return time, water_value
        # except Exception as e:
        #     print(e)
        #     return None, None

    async def getAllTemperatureRelated(self, farmIdx, sector, date=None):
        if date is None:
            startDate = "-15m"
            endDate = "now()"
        else:
            startDate, endDate = self.convertTimeForInflux(date)

        # farmIdx = self.farmIdxMatchingTable[farmIdx]
        query = f'''
        from(bucket: "ai_data")
              |> range(start: {startDate}, stop: {endDate})
              |> filter(fn: (r) =>
                r.topic =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/.*Temperature/
              )
        '''

        res = await self.client.query_api().query(query=query)
        modifiedData = self.dataExtractByBuilding(res)

        return modifiedData

    async def getSetTemperature(self, farmIdx, sector, date=None):
        if date is None:
            startDate = "-15m"
            endDate = "now()"
        else:
            startDate, endDate = self.convertTimeForInflux(date)

        query = f'''
        from(bucket: "ai_data")
              |> range(start: {startDate}, stop: {endDate})
              |> filter(fn: (r) =>
                r.topic =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/setTemperature$/
              )
        '''
        res = await self.client.query_api().query(query=query)
        modifiedData = self.dataExtractByBuilding(res)

        for key, value in modifiedData[str(sector)]['setTemperature'].items():
            last_row = value.iloc[-1]
            set_temp = last_row['value']
            time = last_row.name
            return time, set_temp

    async def getDayAge(self, farmIdx, sector, date=None):
        if date is None:
            startDate = "-15m"
            endDate = "now()"
        else:
            startDate, endDate = self.convertTimeForInflux(date)

        query = f'''
        from(bucket: "ai_data")
              |> range(start: {startDate}, stop: {endDate})
              |> filter(fn: (r) =>
                r.topic =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/age/
              )
        '''
        res = await self.client.query_api().query(query=query)
        modifiedData = self.dataExtractByBuilding(res)

        for key, value in modifiedData[str(sector)]['age'].items():
            last_row = value.iloc[-1]
            day_age = last_row['value']
            time = last_row.name
            return time, day_age

    async def getOutsideWeather(self, farmIdx):
        '''
        어차피 다 같은거 쓰니까 1동으로 고정
        '''
        startDate = "-15m"
        endDate = "now()"

        query = f'''
        from(bucket: "ai_data")
              |> range(start: {startDate}, stop: {endDate})
              |> filter(fn: (r) =>
                r.topic =~ /choretime\/{farmIdx}\/[^\/]+/
              )
        '''
        res = await self.client.query_api().query(query=query)
        try:
            modifiedData = self.dataExtractByBuilding(res)
            out_temp = modifiedData[str(1)]['outsideTemperatureExternal']
            for topic, df in out_temp.items():
                out_temp_C = df.iloc[-1]['value']

            out_hum = modifiedData[str(1)]['outsideHumidityExternal']
            for topic, df in out_hum.items():
                out_humidity = df.iloc[-1]['value']

            return out_temp_C, out_humidity / 100
        except Exception as e:
            return None, None

    async def getCurrentMinVentCount(self, farmIdx, sector) -> int:
        modeMapping = {
            '---': 0,
            'STIR ON': 2,
            'TIMER 1': 3,
            'TIMER 2': 4,
            'MIN VENT': 5,
            'MIN CYCL': 6,
        }
        reversedMapping = {value: key for key, value in modeMapping.items()}
        query = f'''
        from(bucket: "ai_data")
              |> range(start: -15m)
              |> filter(fn: (r) =>
                r.topic =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/tunnelFanMode/ or
                r.topic =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/exhaustFanMode/
              )
              |> last()
        '''
        res = await self.client.query_api().query(query=query)
        modifiedData = self.dataExtractByBuilding(res)

        minVentFanStatus = []
        for key, value in modifiedData[str(sector)].items():
            for topic, value in value.items():
                last_row = value.iloc[-1]
                if reversedMapping[last_row['value']] == 'MIN VENT':
                    minVentFanStatus.append(topic)

        return len(minVentFanStatus)

    #========


    async def alarmQueryExecutor(self, farmIdx, sector, measurement:MeasurementOperation):
        query = self._generateQuery({'farmIdx': farmIdx, 'sector': sector}, measurement)
        result = await self._process_query(query)
        return result


    async def _process_query(self, query):
        """
        InfluxDB 쿼리 실행 및 결과 처리
        """
        res = await self.client.query_api().query(query=query)
        result = {}
        for table in res:
            for record in table.records:
                title = record.values['result']
                time = record.values['_time']
                value = record.values['_value']

                if title not in result:
                    result[title] = []
                result[title].append((time, value))

                # stateDuration 처리
                if 'stateDuration' in record.values:
                    duration = record.values['stateDuration']
                    if 'stateDuration' not in result:
                        result['stateDuration'] = []
                    result['stateDuration'].append((time, duration))

        return result

    def _generateQuery(self, farmInfo, measurement:MeasurementOperation):
        '''
        queryType:
            method : 'threshold' or 'gradient'
            detail : {
                'threshold'
                    min: float
                    max: float
                'gradient'
                    trend: 'up' or 'down'
                    gradient: float
            }
        '''
        def __getBasicQuery(farmIdx, sector, name, measurement):
            return f'''
                {name} = from(bucket: "ai_data")
                |> range(start: -1d, stop: now())
                |> filter(fn: (r) => r.topic =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\/{measurement}/)
                |> aggregateWindow(every: 10m, fn: mean, createEmpty: false)
                |> movingAverage(n: 6)
                |> yield(name: "{name}")
            '''

        if list(farmInfo.keys()) != ['farmIdx', 'sector']:
            raise ValueError("farmInfo must have keys 'farmIdx' and 'sector'")

        if not isinstance(measurement, MeasurementOperation):
            raise ValueError("measurement must be MeasurementOperation type")


        farmIdx = farmInfo['farmIdx']
        sector = farmInfo['sector']

        query = ""
        if len(measurement.measurement) == 1:
            single_measurement = measurement.measurement[0]
            query += __getBasicQuery(farmIdx, sector, "firstData", single_measurement)

        else:
            first_measurement = measurement.measurement[0]
            second_measurement = measurement.measurement[1]

            first_query = __getBasicQuery(farmIdx, sector, "firstData", first_measurement)
            second_query = __getBasicQuery(farmIdx, sector, "secondData", second_measurement)

            join_query = f'''
               joined = join(
                 tables: {{first: firstData, second: secondData}},
                 on: ["_time"]
               )

               operationResult = joined
                 |> map(fn: (r) => ({{
                   _time: r._time,
                   _value: r._value_first {measurement.operator} r._value_second,
                   topic: "operationResult"
                 }}))
                 |> yield(name: "operationResult")
               '''

            query += first_query + second_query + join_query


        if measurement.method == 'threshold':
            # min = queryType['detail']['min']
            # max = queryType['detail']['max']
            min = measurement.detail['min']
            max = measurement.detail['max']

            if min > max:
                raise ValueError("min must be less than max")
            if min == max:
                raise ValueError("min and max must be different")

            query += f'''
              |> map(fn: (r) => ({{ r with valid: (r._value > {min} and r._value <= {max}) }}))
              |> stateDuration(fn: (r) => r.valid, unit: 1m)
              |> yield(name: "threshold")
            '''

        elif measurement.method == 'gradient':

            # trend = queryType['detail']['trend']
            # gradient = queryType['detail']['gradient']
            trend = measurement.detail['trend']
            gradient = measurement.detail['gradient']

            if trend not in ['up', 'down']:
                raise ValueError("trend must be 'up' or 'down'")

            if trend == 'up':
                query += f'''
                  |> sort(columns: ["_time"])
                  |> derivative(unit: 10m, nonNegative: false)
                 |> yield(name: "derivative")
                  |> stateDuration(fn: (r) => r._value > {gradient}, unit: 1m)
                  |> yield(name: "trend")
                '''

            elif trend == 'down':
                query += f'''
                  |> sort(columns: ["_time"])
                  |> derivative(unit: 10m, nonNegative: false)
                  |> yield(name: "derivative")
                  |> stateDuration(fn: (r) => r._value < {gradient}, unit: 1m)
                  |> yield(name: "trend")
                '''
        return query






if __name__ == '__main__':
    async def main():
        client = InfluxDBClient()
        ruleClient = RuleClient()
        await client.initializeClient()
        age = await client.getCurrentAge(103, 2)
        rule = ruleClient.getRule('averageTemperature', age)
        print(rule)
        for elem in rule:
            # print(elem)
            min = elem.min
            max = elem.max

            # await client.alarmThreshold(103, 2, 'temperature1', (min,max), 1)
        # await client.alarmGradient(507, 2, 'setTemperature', -0.01, 3)
        # await client.alarmGradient(103, 2, 'averageTemperature', -0.01, 3)

        # 일령별로 고려되야함.
        # await client.alarmGradient(103, 2, 'totalWaterToday', 20, 3) #10분당 물 소비량이 30이 안되는 경우가 30분 이상 지속될 경우

        measurement = MeasurementOperation(measurement=['averageTemperature'])
        await client.alarmThreshold(103, 2, measurement, (min,max), 1)
        await client.alarmGradient(103, 2,
                                   measurement=measurement,
                                   trend="up",
                                   gradient=0.01,
                                   targetTime=3)  # 10분당 물 소비량이 30이 안되는 경우가 30분 이상 지속될 경우

    import asyncio

    asyncio.run(main())
