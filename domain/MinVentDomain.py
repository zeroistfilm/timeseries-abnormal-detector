if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from py_singleton import singleton
from domain.uregDomain import UregDomain
# from domain.thermalDynamicDomain import ThermalDynamicDomain
import math


@singleton
class MinVentDomain:
    def __init__(self):
        self.ureg = UregDomain()
        self.Q = self.ureg.Q
        # self.thermalDynamicDomain = ThermalDynamicDomain()


    def run(self, out_temp, out_hum, in_temp, in_hum, daily_water_usage, fan_capacity):

        print("최소환기평가")
        print("out_temp", out_temp)
        print("out_hum", out_hum)
        print("in_temp", in_temp)
        print("in_hum", in_hum)
        print("daily_water_usage", daily_water_usage)
        print("fan_capacity", fan_capacity)

        outside_absolute_humidity = self.absolute_humidity(out_temp, out_hum)
        inside_absolute_humidity = self.absolute_humidity(in_temp, in_hum)
        moistureControlVentRate = self.calc_req_min_vent_rate(daily_water_usage, inside_absolute_humidity,
                                                               outside_absolute_humidity)

        return self.calc_min_vent_time(moistureControlVentRate, fan_capacity)



    def absolute_humidity(self, temperature, relative_humidity):

        if relative_humidity > 1:
            raise ValueError("상대습도는 0~1 사이의 값이어야 합니다.")

        def convertCtoF(celsius):
            return (celsius * 9 / 5) + 32

        temperature = convertCtoF(temperature)

        precipitable_water = relative_humidity * math.exp(17.863 - 9621 / (temperature + 460))

        water = 7000 * 0.62198 / ((29.92 / precipitable_water) - 1)
        moisture = water * 0.000142857

        mL_per_cubic_meter = (moisture / 13.5 / 8.34 * 128) / 0.000957506494

        return mL_per_cubic_meter

    def calc_req_min_vent_rate(self, daily_water_usage, inside_absolute_humidity, outside_absolute_humidity):
        def round_up(num, precision):
            precision = 10 ** precision
            return math.ceil(num * precision) / precision

        abs_diff_in_liters = inside_absolute_humidity - outside_absolute_humidity  # 습도의 차이 계산
        # 제거할 물의 양 계산
        cm_per_day = round_up(daily_water_usage / (abs_diff_in_liters / 1000), 0)
        # 시간당 환기 속도 계산
        cm_per_hour = cm_per_day / 24

        return round_up(cm_per_hour, 0)

    def calc_min_vent_time(self, moistureControlVentRate, fanCapacity):
        # Minimum ventilation rate (as per your earlier setup)

        moistureControlVentRate = self.Q(moistureControlVentRate, 'cmh')
        fanCapacity = self.Q(fanCapacity, 'cmh')

        # Calculate runtime percentage
        fanRuntimeOnPercentWhole = self.Q(round((moistureControlVentRate / fanCapacity) * 100, 0) / 100, '%')

        cycle_time = self.Q(300, 's')
        # Calculate on and off time (in seconds) for a 5-minute cycle (300 seconds)

        fanOnTime = cycle_time * fanRuntimeOnPercentWhole
        fanOffTime = cycle_time - self.Q(fanOnTime, 's')

        if fanOnTime >= cycle_time:
            # If fan runtime is greater than 5 minutes, return an error message
            return {
                "error": "The required minimum ventilation rate exceeds the capacity of the fan(s). Please increase the minimum ventilation fan capacity.",
                "fanOnTime": fanOnTime.to('s'),
                "fanOffTime": fanOffTime.to('s'),
                "fanRuntimeOnPercent": fanRuntimeOnPercentWhole.to('%')
            }
        else:
            # Return details if the runtime is under 300 seconds
            return {
                "fanOnTime": fanOnTime.to('s'),
                "fanOffTime": fanOffTime.to('s'),
                "fanRuntimeOnPercent": fanRuntimeOnPercentWhole.to('%')
            }


if __name__ == "__main__":
    minVentDomain = MinVentDomain()


    # outside_absolute_humidity = minVentDomain.absolute_humidity(50, 0.5)
    # inside_absolute_humidity = minVentDomain.absolute_humidity(60, 0.6)
    # print(outside_absolute_humidity)
    # print(inside_absolute_humidity)
    #
    # moistureControlVentRate = minVentDomain.calc_req_min_vent_rate(1000, inside_absolute_humidity,
    #                                                                outside_absolute_humidity)
    #
    # print(minVentDomain.calc_min_vent_time(moistureControlVentRate, 5000))



    print(minVentDomain.run(10, 0.5, 60, 0.6, 1000, 5000))
