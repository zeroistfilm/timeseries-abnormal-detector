from py_singleton import singleton

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    relative_import_path = '.'

import requests
#get env variables
import os
from dotenv import load_dotenv
from domain.uregDomain import UregDomain
import datetime
import pytz

@singleton
class WeatherClient:
    def __init__(self):
        self.ureg = UregDomain()
        self.Q = self.ureg.Q

        currPath = os.path.dirname(os.path.realpath(__file__))
        load_dotenv(f'{currPath}/WeatherAPI.env')

        print(os.getcwd())
        self.WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
        self.WEATHER_API_BASE = os.getenv('WEATHER_API_BASE')


    def getWeatherByGeoCode(self, lat, lon):
        req = requests.get(f"{self.WEATHER_API_BASE}?lat={lat}&lon={lon}&appid={self.WEATHER_API_KEY}")

        temp_K = req.json()['main']['temp']
        humidity = req.json()['main']['humidity']
        timestamp = req.json()['dt']

        # temp_C = self.Q(temp_K, 'K').to('degC')
        # humidity = self.Q(humidity, '%')

        korea_tz = pytz.timezone('Asia/Seoul')
        timestamp = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        timestamp = timestamp.astimezone(korea_tz)


        return temp_K, humidity, timestamp



if __name__ == '__main__':
    weather_client = WeatherClient()

    farm = {
        "망성농장": {
            "lat": "36.113908",
            "long": "127.031671",
            "farmIdx": "101",
            "region": "익산",
            "sectors": 19,
            "sector": {},
            "supplier": "하림"
        },
        "새론농장": {
            "lat": "36.113458",
            "long": "127.029018",
            "farmIdx": "102",
            "region": "익산",
            "sector": {},
            "supplier": "하림",
            "sectors": 13
        },
        "김제농장": {
            "lat": "35.862368",
            "long": "126.883971",
            "farmIdx": "103",
            "region": "김제",
            "sector": {},
            "supplier": "하림",
            "sectors": 5
        },
        "고산농장": {
            "lat": "36.112067",
            "long": "127.043976",
            "farmIdx": "104",
            "region": "익산",
            "sector": {},
            "supplier": "하림",
            "sectors": 4
        },
        "원뉴맨농장": {
            "lat": "35.499880",
            "long": "126.707174",
            "farmIdx": "105",
            "region": "고창",
            "sector": {},
            "supplier": "하림",
            "sectors": 4
        },
        "신왕농장": {
            "lat": "36.106148",
            "long": "127.013123",
            "farmIdx": "106",
            "region": "익산",
            "sector": {},
            "supplier": "하림",
            "sectors": 12
        },
        "수지농장": {
            "lat": "35.316287",
            "long": "127.336058",
            "farmIdx": "201",
            "region": "남원",
            "sector": {},
            "supplier": "하림",
            "sectors": 5
        },
        "반곡농장": {
            "lat": "36.121527",
            "long": "127.011462",
            "farmIdx": "202",
            "region": "익산",
            "sector": {},
            "supplier": "하림",
            "sectors": 7
        }
    }

    for farm_name, farm_info in farm.items():
        lat = farm_info['lat']
        long = farm_info['long']
        temp, humidity, timestamp = weather_client.getWeatherByGeoCode(lat, long)
        print(farm_name, temp, humidity, timestamp)


