from cassandra.cluster import Cluster
from py_singleton import singleton
from cassandra.query import SimpleStatement
import json
import pandas as pd
from typing import List
from domain.anomaly.plugin import RuleMatchResult
from datetime import datetime, timezone, timedelta
@singleton
class ScyllaDBClient:
    def __init__(self):
        self.cluster = Cluster(["haproxy.uniai.co.kr"])
        self.session = self.cluster.connect('prod')

        self.farmInfo = self.getTableData('farminfo')


    def insert_dict(self, tableName, key, data_dict):
        # Python dict를 JSON 문자열로 변환
        json_data = json.dumps(data_dict)
        # CQL 쿼리 실행
        query = SimpleStatement(f"""
            INSERT INTO {tableName} (key, value) VALUES (%s, %s)
        """)
        self.session.execute(query, [key, json_data])
        print("Data inserted successfully")

    def getTableData(self, table):
        query = SimpleStatement(f"""
            SELECT * FROM {table}
        """)
        rows = self.session.execute(query)
        result = {}
        for row in rows:
            key = row.key
            value = json.loads(row.value)
            result[key] = value
        return result


    def resisterTopicStatus(self, ruleMatchResult:RuleMatchResult):
        """
        상태 정보를 Cassandra에 등록합니다. 상태가 변경된 경우에만 기록합니다.
        :param ruleMatchResult: RuleMatchResult 객체

        CREATE TABLE rule_match_status (
        topic TEXT,
        createdAt TIMESTAMP,
        rule_id TEXT,
        detail TEXT,
        PRIMARY KEY (topic, createdAt)
        ) WITH CLUSTERING ORDER BY (createdAt DESC)
        and caching = {'keys': 'ALL', 'rows_per_partition': 'ALL'}
        and compaction = {'class': 'SizeTieredCompactionStrategy'}
        and compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
        and dclocal_read_repair_chance = 0
        and speculative_retry = '99.0PERCENTILE';
        """

        timestamp = ruleMatchResult.timestamp.to_pydatetime() #KST

        rule_id = ruleMatchResult.rule_id
        detail_str = json.dumps(ruleMatchResult.details, ensure_ascii=False)
        topic = ruleMatchResult.topic

        # 1. 마지막 상태 조회
        query_last_status = """
               SELECT * FROM rule_match_status
               WHERE topic = %s
               ORDER BY createdAt DESC
               LIMIT 1;
               """
        last_status = self.session.execute(query_last_status, [topic]).one()
        # 2. 상태 비교
        if last_status:
            last_rule_id = last_status.rule_id
            last_created_at = last_status.createdat



            # 상태 변경이 없는 경우 duration을 업데이트
            if last_rule_id == rule_id:
                timestamp = timestamp.replace(tzinfo=timezone(timedelta(hours=9)))  # Assuming UTC for naive timestamps
                last_created_at = last_created_at.replace(tzinfo=timezone.utc)  # Assuming UTC for naive timestamps
                duration_seconds = (timestamp - last_created_at).total_seconds()
                duration_str = f"{int(duration_seconds // 3600):02}:{int((duration_seconds % 3600) // 60):02}:{int(duration_seconds % 60):02}"

                duration_update_query = """
                      UPDATE prod.rule_match_status
                      SET duration = %s, updatedat = %s
                      WHERE topic = %s AND createdat = %s;
                  """
                self.session.execute(duration_update_query, [duration_str, timestamp, topic, last_created_at])
                print(f"Duration updated for topic '{topic}': {duration_str}")
                return

        # 3. 상태 변경 기록
        query_insert = """
               INSERT INTO rule_match_status (topic, createdAt, rule_id, detail, updatedat)
               VALUES (%s, %s, %s, %s, %s);
               """

        self.session.execute(
            query_insert,
            [topic, timestamp, rule_id, detail_str, timestamp]
        )
        print(f"Status updated for topic '{topic}' with rule_id '{rule_id}'.")
        return

    def getGeoCode(self, farmIdx):
        lat, long = None, None
        for farmName, value in self.farmInfo.items():
            if value['farmIdx'] == str(farmIdx):
                sectors = value['sectors']
                return value['lat'], value['long'], farmName, sectors

        if lat is None or long is None:
            raise ValueError("해당 농장의 위도 경도 정보가 없습니다.")


