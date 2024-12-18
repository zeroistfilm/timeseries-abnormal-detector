import pytz

if __name__ == "__main__":
import dotenv
dotenv.load_dotenv()
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from domain.MinVentDomain import MinVentDomain
from adapter.output.client.InfluxdbClient import InfluxDBClient
from adapter.output.client.ScylladbClient import ScyllaDBClient
from adapter.output.client.WeatherClient import WeatherClient
from adapter.output.client.MqttClient import MqttClient
from domain.uregDomain import UregDomain
import datetime
from py_singleton import singleton

@singleton
class MinVentService:
    def __init__(self):
        self.minVentDomain = MinVentDomain()
        self.ureg = UregDomain()
        self.Q = self.ureg.Q
        self.influxDBClient = InfluxDBClient()
        self.scyllaDBClient = ScyllaDBClient()
        self.weatherClient = WeatherClient()
        self.mqttClient = MqttClient()


    async def getOutsideWeather(self, farmIdx):
        # Note 조회된 결과가 없으면 외부 데이터 호출
        out_temp_C, out_humidity = await self.influxDBClient.getOutsideWeather(farmIdx)
        print("outside_temp_c, outside_humidity", out_temp_C, out_humidity)

        if out_temp_C is None and out_humidity is None:
            lat, long, farmName, sectors_count = self.scyllaDBClient.getGeoCode(farmIdx)
            print("lat, long", lat, long)
            if lat is None or long is None:
                raise ValueError("해당 농장의 위도 경도 정보가 없습니다.")

            out_temp_K, out_humidity, timestamp = self.weatherClient.getWeatherByGeoCode(lat, long)
            print("out_temp_K, out_humidity, timestamp", out_temp_K, out_humidity, timestamp)
            if out_temp_K is None or out_humidity is None:
                raise ValueError("해당 농장의 날씨 정보를 가져올 수 없습니다.")

            out_temp_C = self.Q(out_temp_K, 'kelvin').to('degC').magnitude
            out_humidity = (self.Q(out_humidity, '%') / 100.0).magnitude
            timestampUTC = timestamp.astimezone(pytz.utc)
            timestampUTC_str = timestampUTC.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            for sector in range(1, sectors_count+1):
                weather_data = [
                    (f"/dev/choretime/{farmIdx}/{farmName}/{sector}/outsideTemperatureExternal", out_temp_C),
                    (f"/dev/choretime/{farmIdx}/{farmName}/{sector}/outsideHumidityExternal", out_humidity * 100),
                ]
                # 반복문을 통해 MQTT 메시지 발행
                for topic, value in weather_data:
                    message = {
                        "farm_idx": str(farmIdx),
                        "farm_name": farmName,
                        "sector": str(sector),
                        "value": float(value),
                        "time": timestampUTC_str,
                    }
                    self.mqttClient.publish(topic, message)



        return out_temp_C, out_humidity

    async def calcMinVent(self, farmIdx, sector):

        _, _, farmName, _ = self.scyllaDBClient.getGeoCode(farmIdx)
        out_temp_C, out_humidity = await self.getOutsideWeather(farmIdx)

        _, water_consumption = await self.influxDBClient.getCurrentWaterTotal(farmIdx, sector)
        if water_consumption is None:
            raise ValueError("해당 농장의 물 사용량 정보를 가져올 수 없습니다.")

        _, set_temperature = await self.influxDBClient.getSetTemperature(farmIdx, sector)

        _, day_age = await self.influxDBClient.getDayAge(farmIdx, sector)

        _, in_humidity_percent = await self.influxDBClient.getCurrentHumidity(farmIdx, sector)
        if in_humidity_percent is None:
            raise ValueError("해당 농장의 내부 습도 정보를 가져올 수 없습니다.")

        _, in_temp = await self.influxDBClient.getCurrentTemperature(farmIdx, sector)
        if in_temp is None:
            raise ValueError("해당 농장의 내부 온도 정보를 가져올 수 없습니다.")

        water_consumption = self.Q(water_consumption, 'L').magnitude
        in_temp = self.Q(in_temp, 'degC').magnitude
        in_humidity = (self.Q(in_humidity_percent, '%') / 100.0).magnitude


        minVentCount = await self.influxDBClient.getCurrentMinVentCount(farmIdx, sector)
        DEFAULT_FAN_CMH = 43000 # 문터스 EM50 스펙
        minVentTime = self.minVentDomain.run(out_temp_C, out_humidity, in_temp, in_humidity, water_consumption,
                                             DEFAULT_FAN_CMH * minVentCount)



        minVentOnValue = minVentTime['fanOnTime'].magnitude
        minVentOffValue = minVentTime['fanOffTime'].magnitude

        weather_data = [
            (f"/dev/choretime/{farmIdx}/{farmName}/{sector}/recommendMinVentOn", minVentOnValue),
            (f"/dev/choretime/{farmIdx}/{farmName}/{sector}/recommendMinVentOff", minVentOffValue),
        ]

        timestamp_utc_now = pytz.utc.localize(datetime.datetime.utcnow())
        timestampUTC_str = timestamp_utc_now.strftime("%Y-%m-%dT%H:%M:%S.000Z")


        # 반복문을 통해 MQTT 메시지 발행
        for topic, value in weather_data:
            message = {
                "farm_idx": str(farmIdx),
                "farm_name": farmName,
                "sector": str(sector),
                "value": float(value),
                "time": timestampUTC_str,
            }
            self.mqttClient.publish(topic, message)

        return minVentTime





if __name__ == '__main__':
    import asyncio
    import plotly.graph_objects as go
    async def main():
        minVentService = MinVentService()
        await minVentService.influxDBClient.initializeClient()
        # await minVentService.calcMinVent(503, 1)
        await minVentService.calcMinVent(103, 3)

        # await minVentService.close()
    #
    #     fanOn=[]
    #     inCondi = []
    #     outCondi = []
    #
    #     for in_temp in range(5, 40, 10):
    #         for in_hum in range(30, 100, 5):
    #             # for out_temp in range(5, 40, 10):
    #             #     for out_hum in range(30, 100, 5):
    #             out_temp = 20
    #             out_hum = 50
    #             try:
    #                 res = minVentService.testCalcMinVent(in_temp, in_hum/100, out_temp, out_hum/100, 1000, 10000 * 2)
    #
    #                 if res['Fan_on_second'] < 0:
    #                     continue
    #                 if res['Fan_on_second'] > 300:
    #                     continue
    #                 fanOn.append(res['Fan_on_second'])
    #                 # inCondi.append(in_hum * 100 * in_temp)
    #                 # outCondi.append(out_hum * 100 * out_temp)
    #                 inCondi.append(in_temp)
    #                 outCondi.append(in_hum)
    #             except Exception as e:
    #                 continue
    #
    #
    #
    #     print(fanOn)
    #     print(inCondi)
    #     print(outCondi)
    #
    #     fig = go.Figure(data=[go.Scatter3d(
    #         x=inCondi,
    #         y=outCondi,
    #         z=fanOn,
    #         mode='markers',
    #         marker=dict(size=5, color=outCondi, colorscale='Viridis', opacity=0.8)
    #     )])
    #
    #     fig.update_layout(
    #         scene=dict(
    #             xaxis_title='InCondi',
    #             yaxis_title='OutCondi',
    #             zaxis_title='FanOn'
    #         ),
    #         title='3D Interactive Plot of FanOn vs InCondi and OutCondi'
    #     )
    #
    #     fig.show()
    #
    # #
    # #     # res = minVentService.testCalcMinVent(20, 0.5, 10, 0.5, 2000, 50000 * 2)
    # #     # print(res)
    # #
    #
    #
    #
    asyncio.run(main())
    #


