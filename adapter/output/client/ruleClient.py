class RuleClient:
    def __init__(self):

        # 특정 값 사이에 있으면 매칭이라고 표시하고
        # 매칭되며 매칭을 보내는 방식으로 해야겠다.
        self.rule = {
            'global': {  # sector 대신
                'relativeHumidity': {  # topic대신
                    'rules': [
                        {
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_high_warning',
                            'description': '습도 80 초과 경고',
                            'max': 100,
                            'min': 80,
                            'if_matched': 'abnormal',
                            'level': 'warning'
                        },
                        {
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_normal',
                            'description': '습도 초과 유의',
                            'max': 80,
                            'min': 60,
                            'if_matched': 'normal',
                            'level': 'warning'
                        },
                        {
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_normal',
                            'description': '습도 적합',
                            'max': 60,
                            'min': 40,
                            'if_matched': 'normal',
                            'level': 'warning'
                        },
                        {
                            'rule_owner': 'global',
                            'type': 'threshold',
                            'rule_id': 'humidity_low_warning',
                            'description': '습도 30~40 사이',
                            'level': 'warning',
                            'max': 40,
                            'min': 30
                        },
                    ],
                }
            },
            #
            '101':{
                '1':{
                    '/dev/choretime/101/망성농장/1/relativeHumidity':{
                        'rules': [
                            {
                                'rule_owner': 'farm',
                                'type': 'threshold',
                                'rule_id': 'humidity_high_warning',
                                'description': '습도 80 초과 경고',
                                'max': 100,
                                'min': 80,
                                'if_matched': 'abnormal',
                                'level': 'warning'
                            },
                            {
                                'rule_owner': 'farm',
                                'type': 'threshold',
                                'rule_id': 'humidity_normal',
                                'description': '습도 초과 유의',
                                'max': 80,
                                'min': 60,
                                'if_matched': 'normal',
                                'level': 'warning'
                            },
                            {
                                'rule_owner': 'farm',
                                'type': 'threshold',
                                'rule_id': 'humidity_normal',
                                'description': '습도 적합',
                                'max': 60,
                                'min': 40,
                                'if_matched': 'normal',
                                'level': 'warning'
                            },
                            {
                                'rule_owner': 'farm',
                                'type': 'threshold',
                                'rule_id': 'humidity_low_warning',
                                'description': '습도 30~40 사이',
                                'level': 'warning',
                                'max': 40,
                                'min': 30
                            },
                        ],
                    },
                    },

            }
            #     '2': {
            #         '/dev/choretime/101/망성농장/2/relativeHumidity': {
            #             'rules': [
            #                 {
            #                     'type': 'threshold',
            #                     'rule_id': 'humidity_high_warning',
            #                     'description': '습도 80 초과 경고',
            #                     'max': 100,
            #                     'min': 80,
            #                     'if_matched': 'abnormal',
            #                     'level': 'warning'
            #                 },
            #                 {
            #                     'type': 'threshold',
            #                     'rule_id': 'humidity_normal',
            #                     'description': '습도 초과 유의',
            #                     'max': 80,
            #                     'min': 60,
            #                     'if_matched': 'normal',
            #                     'level': 'warning'
            #                 },
            #                 {
            #                     'type': 'threshold',
            #                     'rule_id': 'humidity_normal',
            #                     'description': '습도 적합',
            #                     'max': 60,
            #                     'min': 40,
            #                     'if_matched': 'normal',
            #                     'level': 'warning'
            #                 },
            #                 {
            #                     'type': 'threshold',
            #                     'rule_id': 'humidity_low_warning',
            #                     'description': '습도 30~40 사이',
            #                     'level': 'warning',
            #                     'max': 40,
            #                     'min': 30
            #                 },
            #             ],
            #         },
            #     },
            #     '3': {
            #         '/dev/choretime/101/망성농장/3/relativeHumidity': {
            #             'rules': [
            #                 {
            #                     'type': 'threshold',
            #                     'rule_id': 'humidity_high_warning',
            #                     'description': '습도 80 초과 경고',
            #                     'max': 100,
            #                     'min': 80,
            #                     'if_matched': 'abnormal',
            #                     'level': 'warning'
            #                 },
            #                 {
            #                     'type': 'threshold',
            #                     'rule_id': 'humidity_normal',
            #                     'description': '습도 초과 유의',
            #                     'max': 80,
            #                     'min': 60,
            #                     'if_matched': 'normal',
            #                     'level': 'warning'
            #                 },
            #                 {
            #                     'type': 'threshold',
            #                     'rule_id': 'humidity_normal',
            #                     'description': '습도 적합',
            #                     'max': 60,
            #                     'min': 40,
            #                     'if_matched': 'normal',
            #                     'level': 'warning'
            #                 },
            #                 {
            #                     'type': 'threshold',
            #                     'rule_id': 'humidity_low_warning',
            #                     'description': '습도 30~40 사이',
            #                     'level': 'warning',
            #                     'max': 40,
            #                     'min': 30
            #                 },
            #             ],
            #         },
            #     }
            #     },
        }

    def getRule(self, farmIdx:str, sector:str, measurement,topic):

        # 개별 룰 조회후 없으면 전역 룰 조회
        if str(farmIdx) in self.rule:
            if str(sector) in self.rule[str(farmIdx)]:
                if topic in self.rule[str(farmIdx)][str(sector)]:
                    return self.rule[str(farmIdx)][str(sector)][topic]

        if measurement in self.rule['global']:
            return self.rule['global'][measurement]

        return None


