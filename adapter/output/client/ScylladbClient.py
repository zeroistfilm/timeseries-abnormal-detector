from cassandra.cluster import Cluster
from py_singleton import singleton
from cassandra.query import SimpleStatement
import json
import pandas as pd
from typing import List
from domain.anomaly.plugin import RuleMatchResult

@singleton
class ScyllaDBClient:
    def __init__(self):
        self.cluster = Cluster(["haproxy.uniai.co.kr"])
        self.session = self.cluster.connect('prod')

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

        timestamp = ruleMatchResult.timestamp.to_pydatetime()
        rule_id = ruleMatchResult.rule_id
        detail_str = json.dumps(ruleMatchResult.details, ensure_ascii=False)
        topic = ruleMatchResult.topic

        # 1. 마지막 상태 조회
        query_last_status = """
               SELECT rule_id, detail FROM rule_match_status
               WHERE topic = %s
               ORDER BY createdAt DESC
               LIMIT 1;
               """
        last_status = self.session.execute(query_last_status, [topic]).one()
        # 2. 상태 비교
        if last_status:
            last_rule_id = last_status.rule_id
            last_detail = last_status.detail

            # 상태 변경이 없는 경우 종료
            if last_rule_id == rule_id and last_detail == str(detail_str):
                print(f"No status change for topic '{topic}'. Skipping record.")
                return



        # 3. 상태 변경 기록
        query_insert = """
               INSERT INTO rule_match_status (topic, createdAt, rule_id, detail)
               VALUES (%s, %s, %s, %s);
               """

        self.session.execute(
            query_insert,
            [topic, timestamp, rule_id, detail_str]
        )
        print(f"Status updated for topic '{topic}' with rule_id '{rule_id}'.")

