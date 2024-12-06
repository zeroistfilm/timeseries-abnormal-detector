from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

import pandas as pd

import datetime
from datetime import timezone, timedelta
import numpy as np
import random
import json
from py_singleton import singleton

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
                if '/dev/choretime' in topic:
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[6]

                elif '/dev/bigdutchman' in topic:
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[6]

                elif '/dev/area' in topic:
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[2]
                elif '/coxlab' in topic:
                    #/coxlab/co2/507/choiyulfarm/2/1-1
                    buildingNo = topic.split('/')[5]
                    measurement = topic.split('/')[2]
                elif '/dev/breedInfo' in topic:
                    #/dev\/breedInfo\/{farmIdx}\/[^\/]+\/{buildingNo}\/isBreedActive/
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
        #/{sector}/: 기존에는 {sector} 뒤에 다른 숫자들이 나오는 경우도 매칭될 가능성이 있었습니다.
        #/{sector}\//: {sector} 바로 뒤에 슬래시(/)가 와야만 매칭되도록 제한했습니다.
        query = f'''
        from(bucket: "ai_data")
        |> range(start:-30m)
        |> filter(fn: (r) => 
                r.topic  =~ /choretime\/{farmIdx}\/[^\/]+\/{sector}\//
        )
        '''
        original = await self.client.query_api().query(query=query)


        modifiedData = self.dataExtractByBuilding(original)
        #measurement, topic, (date, value)
        return modifiedData[str(sector)]

if __name__ == '__main__':
    async def main():
        client = InfluxDBClient()
        await client.initializeClient()
        result = await client.getRecentData(101, 1)
        for key, value in result.items():
            for key2, value2 in value.items():
                print(key2)


    import asyncio
    asyncio.run(main())