from typing import List

from domain.anomaly.plugin import Rule


class RuleClient:
    def __init__(self):
        # 특정 값 사이에 있으면 매칭이라고 표시하고
        # 매칭되며 매칭을 보내는 방식으로 해야겠다.
        self.rule = {
            'global': {  # sector 대신
                'relativeHumidity': {  # topic대신
                    'rules': {
                        'humidity_high_danger': [
                            (0, 0),  # Index 0
                            *[(85, 100)] * 3,  # Index 1 to 3
                            *[(90, 100)] * 25,  # Index 4 to 28
                            *[(95, 100)] * 14  # Index 29 to 41
                        ],
                        'humidity_high_warning': [
                            (0, 0),  # Index 0
                            *[(75, 85)] * 3,  # Index 1 to 3
                            *[(80, 90)] * 25,  # Index 4 to 28
                            *[(85, 95)] * 14  # Index 29 to 41
                        ],
                        'humidity_high_caution': [
                            (0, 0),  # Index 0
                            *[(65, 75)] * 3,  # Index 1 to 3
                            *[(70, 80)] * 25,  # Index 4 to 28
                            *[(75, 85)] * 14  # Index 29 to 41
                        ],
                        'humidity_high_attention': [
                            (0, 0),  # Index 0
                            *[(60, 65)] * 3,  # Index 1 to 3
                            *[(65, 70)] * 25,  # Index 4 to 28
                            *[(70, 75)] * 14  # Index 29 to 41
                        ],
                        'humidity_fit': [
                            (0, 0),  # Index 0
                            *[(40, 60)] * 3,  # Index 1 to 3
                            *[(45, 65)] * 7,  # Index 4 to 10
                            *[(50, 65)] * 9,  # Index 11 to 19
                            *[(55, 65)] * 9,  # Index 20 to 28
                            *[(60, 70)] * 14  # Index 29 to 41
                        ],
                        'humidity_low_warning': [
                            (0, 0),  # Index 0
                            *[(0, 40)] * 3,  # Index 1 to 3
                            *[(0, 45)] * 7,  # Index 4 to 10
                            *[(0, 50)] * 9,  # Index 11 to 19
                            *[(0, 55)] * 9,  # Index 20 to 28
                            *[(0, 60)] * 14  # Index 29 to 41
                        ]
                    },
                    'template': {
                        'humidity_high_danger': {
                            'max': None,
                            'min': None,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_high_danger',
                            'description': '습도 초과 위험',
                            'if_matched': 'abnormal',
                            'level': 'danger'
                        },
                        'humidity_high_warning': {
                            'max': None,
                            'min': None,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_high_warning',
                            'description': '습도 높음 경고',
                            'if_matched': 'abnormal',
                            'level': 'warning'
                        },
                        'humidity_high_caution': {
                            'max': None,
                            'min': None,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_high_caution',
                            'description': '습도 높음 주의',
                            'if_matched': 'abnormal',
                            'level': 'caution'
                        },
                        'humidity_high_attention': {
                            'max': None,
                            'min': None,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_high_attention',
                            'description': '습도 높음 관심',
                            'if_matched': 'abnormal',
                            'level': 'attention'
                        },
                        'humidity_fit': {
                            'max': None,
                            'min': None,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_fit',
                            'description': '습도 적합',
                            'if_matched': 'normal',
                            'level': 'warning'
                        },
                        'humidity_low_warning': {
                            'max': None,
                            'min': None,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_low_warning',
                            'description': '습도 낮음 주의',
                            'if_matched': 'abnormal',
                            'level': 'warning',
                        },
                    }
                },
                'averageTemperature': {
                    'rules': {
                        'temperature_high_danger': [
                            (0, 0),  # Index 0
                            *[(36, 100)] * 3,  # Repeated 3 times
                            *[(35, 100)] * 4,  # Repeated 4 times
                            *[(34, 100)] * 5,  # Repeated 5 times
                            *[(33, 100)] * 4,  # Repeated 4 times
                            *[(32, 100)] * 5,  # Repeated 5 times
                            *[(31, 100)] * 5,  # Repeated 5 times
                            *[(30, 100)] * 4,  # Repeated 4 times
                            *[(29, 100)] * 5,  # Repeated 5 times
                            *[(28, 100)] * 4,  # Repeated 4 times
                            *[(27, 100)] * 3  # Repeated 3 times
                        ],
                        'temperature_high_warning': [
                            (0, 0),  # Index 0
                            *[(35, 36)] * 2,  # Repeated 2 times
                            *[(34, 36)] * 1,  # Repeated 1 time
                            *[(34, 35)] * 3,  # Repeated 3 times
                            *[(33, 35)] * 1,  # Repeated 1 time
                            *[(33, 34)] * 2,  # Repeated 2 times
                            *[(32, 34)] * 3,  # Repeated 3 times
                            *[(32, 33)] * 1,  # Repeated 1 time
                            *[(31, 33)] * 3,  # Repeated 3 times
                            *[(31, 32)] * 1,  # Repeated 1 time
                            *[(30, 32)] * 4,  # Repeated 4 times
                            *[(29, 31)] * 4,  # Repeated 4 times
                            *[(28, 31)] * 1,  # Repeated 1 time
                            *[(28, 30)] * 3,  # Repeated 3 times
                            *[(27, 30)] * 1,  # Repeated 1 time
                            *[(27, 29)] * 3,  # Repeated 3 times
                            *[(26, 29)] * 2,  # Repeated 2 times
                            *[(26, 28)] * 2,  # Repeated 2 times
                            *[(25, 28)] * 2,  # Repeated 2 times
                            *[(25, 27)] * 2,  # Repeated 2 times
                            *[(24, 27)] * 1  # Repeated 1 time
                        ],
                        'temperature_high_caution': [
                            (0, 0),  # Index 0
                            *[(34, 35)] * 2,  # Repeated 2 times
                            *[(33, 34)] * 3,  # Repeated 3 times
                            *[(32, 34)] * 1,  # Repeated 1 time
                            *[(32, 33)] * 2,  # Repeated 2 times
                            *[(31, 33)] * 1,  # Repeated 1 time
                            *[(31, 32)] * 3,  # Repeated 3 times
                            *[(30, 32)] * 1,  # Repeated 1 time
                            *[(30, 31)] * 2,  # Repeated 2 times
                            *[(29, 31)] * 2,  # Repeated 2 times
                            *[(29, 30)] * 1,  # Repeated 1 time
                            *[(28, 30)] * 3,  # Repeated 3 times
                            *[(27, 29)] * 3,  # Repeated 3 times
                            *[(26, 29)] * 1,  # Repeated 1 time
                            *[(26, 28)] * 2,  # Repeated 2 times
                            *[(25, 28)] * 2,  # Repeated 2 times
                            *[(25, 27)] * 2,  # Repeated 2 times
                            *[(24, 27)] * 2,  # Repeated 2 times
                            *[(24, 26)] * 1,  # Repeated 1 time
                            *[(23, 26)] * 3,  # Repeated 3 times
                            *[(22, 25)] * 3,  # Repeated 3 times
                            *[(21, 25)] * 1,  # Repeated 1 time
                            *[(21, 24)] * 1  # Repeated 1 time
                        ],
                        'temperature_fit': [
                            (0, 0),  # Index 0
                            *[(32, 34)] * 2,  # Repeated 2 times
                            *[(31, 33)] * 2,  # Repeated 2 times
                            *[(30, 33)] * 1,  # Repeated 1 time
                            *[(30, 32)] * 1,  # Repeated 1 time
                            *[(29, 32)] * 2,  # Repeated 2 times
                            *[(28, 31)] * 3,  # Repeated 3 times
                            *[(27, 31)] * 1,  # Repeated 1 time
                            *[(27, 30)] * 1,  # Repeated 1 time
                            *[(26, 30)] * 2,  # Repeated 2 times
                            *[(26, 29)] * 1,  # Repeated 1 time
                            *[(25, 29)] * 2,  # Repeated 2 times
                            *[(25, 28)] * 1,  # Repeated 1 time
                            *[(24, 28)] * 2,  # Repeated 2 times
                            *[(23, 27)] * 3,  # Repeated 3 times
                            *[(22, 26)] * 3,  # Repeated 3 times
                            *[(21, 25)] * 2,  # Repeated 2 times
                            *[(20, 25)] * 2,  # Repeated 2 times
                            *[(20, 24)] * 1,  # Repeated 1 time
                            *[(19, 24)] * 2,  # Repeated 2 times
                            *[(19, 23)] * 1,  # Repeated 1 time
                            *[(18, 23)] * 2,  # Repeated 2 times
                            *[(17, 22)] * 3,  # Repeated 3 times
                            *[(16, 21)] * 2  # Repeated 2 times
                        ],
                        'temperature_low_caution': [
                            (0, 0),  # Index 0
                            *[(31, 32)] * 2,  # Repeated 2 times
                            *[(30, 31)] * 2,  # Repeated 2 times
                            *[(29, 30)] * 2,  # Repeated 2 times
                            *[(28, 29)] * 2,  # Repeated 2 times
                            *[(27, 28)] * 2,  # Repeated 2 times
                            *[(26, 28)] * 1,  # Repeated 1 time
                            *[(26, 27)] * 2,  # Repeated 2 times
                            *[(25, 26)] * 3,  # Repeated 3 times
                            *[(24, 25)] * 2,  # Repeated 2 times
                            *[(23, 25)] * 1,  # Repeated 1 time
                            *[(23, 24)] * 2,  # Repeated 2 times
                            *[(22, 23)] * 2,  # Repeated 2 times
                            *[(21, 23)] * 1,  # Repeated 1 time
                            *[(21, 22)] * 2,  # Repeated 2 times
                            *[(20, 22)] * 1,  # Repeated 1 time
                            *[(20, 21)] * 2,  # Repeated 2 times
                            *[(19, 20)] * 2,  # Repeated 2 times
                            *[(18, 20)] * 1,  # Repeated 1 time
                            *[(18, 19)] * 2,  # Repeated 2 times
                            *[(17, 19)] * 1,  # Repeated 1 time
                            *[(17, 18)] * 2,  # Repeated 2 times
                            *[(16, 18)] * 1,  # Repeated 1 time
                            *[(16, 17)] * 2,  # Repeated 2 times
                            *[(15, 17)] * 1,  # Repeated 1 time
                            *[(15, 16)] * 2  # Repeated 2 times
                        ],
                        'temperature_low_warning': [(0, 0),
                                                    *[(30, 31)] * 2,  # Repeated 2 times
                                                    *[(29, 30)] * 2,  # Repeated 2 times
                                                    *[(28, 29)] * 2,  # Repeated 2 times
                                                    *[(27, 28)] * 2,  # Repeated 2 times
                                                    *[(26, 27)] * 2,  # Repeated 2 times
                                                    *[(25, 26)] * 3,  # Repeated 3 times
                                                    *[(24, 25)] * 2,  # Repeated 2 times
                                                    *[(23, 25)] * 1,  # Repeated 1 time
                                                    *[(23, 24)] * 2,  # Repeated 2 times
                                                    *[(22, 23)] * 2,  # Repeated 2 times
                                                    *[(21, 23)] * 1,  # Repeated 1 time
                                                    *[(21, 22)] * 2,  # Repeated 2 times
                                                    *[(20, 21)] * 2,  # Repeated 2 times
                                                    *[(19, 21)] * 1,  # Repeated 1 time
                                                    *[(19, 20)] * 2,  # Repeated 2 times
                                                    *[(18, 20)] * 1,  # Repeated 1 time
                                                    *[(18, 19)] * 1,  # Repeated 1 time
                                                    *[(17, 19)] * 1,  # Repeated 1 time
                                                    *[(17, 18)] * 2,  # Repeated 2 times
                                                    *[(16, 18)] * 1,  # Repeated 1 time
                                                    *[(16, 17)] * 1,  # Repeated 1 time
                                                    *[(15, 17)] * 1,  # Repeated 1 time
                                                    *[(15, 16)] * 2,  # Repeated 2 times
                                                    *[(14, 16)] * 1,  # Repeated 1 time
                                                    *[(14, 15)] * 1,  # Repeated 1 time
                                                    *[(13, 15)] * 2  # Repeated 2 times
                                                    ],
                        'temperature_low_danger': [(0, 0),
                                                   *[(0, 30)] * 2,
                                                   *[(0, 29)] * 2,
                                                   *[(0, 28)] * 2,
                                                   *[(0, 27)] * 2,
                                                   *[(0, 26)] * 2,
                                                   *[(0, 25)] * 3,
                                                   *[(0, 24)] * 2,
                                                   *[(0, 23)] * 3,
                                                   *[(0, 22)] * 2,
                                                   *[(0, 21)] * 3,
                                                   *[(0, 20)] * 2,
                                                   *[(0, 19)] * 3,
                                                   *[(0, 18)] * 2,
                                                   *[(0, 17)] * 3,
                                                   *[(0, 16)] * 2,
                                                   *[(0, 15)] * 3,
                                                   *[(0, 14)]* 2,
                                                   *[(0, 13)] * 2],
                    },
                    'template': {
                        'temperature_high_danger': {
                            'max': 100,
                            'min': 36,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'temperature_high_danger',
                            'description': '온도 상한 위험',
                            'if_matched': 'abnormal',
                            'level': 'danger'
                        },
                        'temperature_high_warning': {
                            'max': 36,
                            'min': 35,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'temperature_high_warning',
                            'description': '온도 상한 경고',
                            'if_matched': 'abnormal',
                            'level': 'warning'
                        },
                        'temperature_high_caution': {
                            'max': 35,
                            'min': 34,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': '',
                            'description': '온도 상한 주의',
                            'if_matched': 'abnormal',
                            'level': 'caution'
                        },
                        'temperature_fit': {
                            'max': 34,
                            'min': 32,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'temperature_fit',
                            'description': '온도 적합',
                            'if_matched': 'normal',
                            'level': 'normal'
                        },
                        'temperature_low_caution': {
                            'max': 32,
                            'min': 31,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'temperature_low_caution',
                            'description': '온도 하한 주의',
                            'if_matched': 'abnormal',
                            'level': 'caution'
                        },
                        'temperature_low_warning': {
                            'max': 31,
                            'min': 30,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': '',
                            'description': '온도 하한 경고',
                            'if_matched': 'abnormal',
                            'level': 'warning'
                        },
                        'temperature_low_danger': {
                            'max': 30,
                            'min': -50,
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'temperature_low_danger',
                            'description': '온도 하한 위험',
                            'if_matched': 'abnormal',
                            'level': 'danger'
                        },
                    }

                }
            },
        }

    def getRule(self, farmIdx: str, sector: str, measurement, topic, age: int) -> list[Rule]:

        ruleList = []
        # TODO
        # 개별 농장 데이터가 필요하면 입력하기
        # if str(farmIdx) in self.rule:
        #     if str(sector) in self.rule[str(farmIdx)]:
        #         if topic in self.rule[str(farmIdx)][str(sector)]:
        #             return self.rule[str(farmIdx)][str(sector)][topic]

        if measurement in self.rule['global']:
            ruleNames = self.rule['global'][measurement]['rules'].keys()
            for rule in ruleNames:
                try:
                    minMixList = list(self.rule['global'][measurement]['rules'][rule])
                    min, max = minMixList[age]
                    templates = self.rule['global'][measurement]['template'][rule]
                    templates['min'] = min
                    templates['max'] = max
                    templates['measurement'] = measurement
                    ruleList.append(Rule(**templates))
                except Exception as e:
                    import traceback
                    print(f'Error : {e}', measurement, age)
                    pass
        else:
            # Note : 관심 룰로 정의되지 않는 Measurement
            pass

        return ruleList


if __name__ == "__main__":
    client = RuleClient()
    result = client.getRule('101', '1', 'averageTemperature', '', 2)
    print(result)
