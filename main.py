from fastapi import FastAPI, HTTPException
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from cassandra.cluster import Cluster
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
from dotenv import load_dotenv
import numpy as np
from typing import Dict, List
from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI()

# InfluxDB configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

# ScyllaDB configuration
SCYLLA_HOSTS = os.getenv("SCYLLA_HOSTS", "localhost").split(",")
SCYLLA_KEYSPACE = os.getenv("SCYLLA_KEYSPACE", "abnormal_detection")

# Initialize InfluxDB client
influx_client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)

# Initialize ScyllaDB client
scylla_cluster = Cluster(SCYLLA_HOSTS)
scylla_session = scylla_cluster.connect()

# Create keyspace and tables in ScyllaDB if they don't exist
scylla_session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS {SCYLLA_KEYSPACE}
    WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
""")

scylla_session.execute(f"""
    CREATE TABLE IF NOT EXISTS {SCYLLA_KEYSPACE}.abnormal_data (
        timestamp timestamp,
        sensor_id text,
        value double,
        threshold double,
        status text,
        PRIMARY KEY (sensor_id, timestamp)
    )
""")

class SensorData(BaseModel):
    sensor_id: str
    value: float
    timestamp: datetime = None

# Threshold configuration (can be moved to a configuration file or database)
THRESHOLDS = {
    "default": 100.0  # Default threshold value
}

def check_abnormal_data():
    """
    Every 10 minutes, check for abnormal data in InfluxDB
    """
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -10m)
        |> filter(fn: (r) => r["_measurement"] == "sensor_data")
    '''
    
    result = influx_client.query_api().query(query)
    
    for table in result:
        for record in table.records:
            value = record.get_value()
            sensor_id = record.values.get("sensor_id")
            threshold = THRESHOLDS.get(sensor_id, THRESHOLDS["default"])
            
            if value > threshold:
                # Store abnormal data in ScyllaDB
                scylla_session.execute(
                    f"""
                    INSERT INTO {SCYLLA_KEYSPACE}.abnormal_data
                    (timestamp, sensor_id, value, threshold, status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (record.get_time(), sensor_id, value, threshold, "abnormal")
                )

def monitor_abnormal_data():
    """
    Every minute, check if abnormal data has returned to normal
    """
    query = f"""
    SELECT * FROM {SCYLLA_KEYSPACE}.abnormal_data
    WHERE status = 'abnormal'
    """
    rows = scylla_session.execute(query)
    
    for row in rows:
        # Query current value from InfluxDB
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1m)
            |> filter(fn: (r) => r["_measurement"] == "sensor_data")
            |> filter(fn: (r) => r["sensor_id"] == "{row.sensor_id}")
            |> last()
        '''
        
        result = influx_client.query_api().query(query)
        
        for table in result:
            for record in table.records:
                current_value = record.get_value()
                if current_value <= row.threshold:
                    # Update status in ScyllaDB
                    scylla_session.execute(
                        f"""
                        UPDATE {SCYLLA_KEYSPACE}.abnormal_data
                        SET status = 'normalized'
                        WHERE sensor_id = %s AND timestamp = %s
                        """,
                        (row.sensor_id, row.timestamp)
                    )

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(check_abnormal_data, 'interval', minutes=10)
scheduler.add_job(monitor_abnormal_data, 'interval', minutes=1)
scheduler.start()

@app.post("/sensor-data")
async def insert_sensor_data(data: SensorData):
    """
    Endpoint to receive sensor data
    """
    if data.timestamp is None:
        data.timestamp = datetime.utcnow()
    
    # Write to InfluxDB
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    point = Point("sensor_data") \
        .tag("sensor_id", data.sensor_id) \
        .field("value", data.value) \
        .time(data.timestamp)
    
    try:
        write_api.write(bucket=INFLUXDB_BUCKET, record=point)
        return {"status": "success", "message": "Data inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/abnormal-data/{sensor_id}")
async def get_abnormal_data(sensor_id: str):
    """
    Endpoint to get abnormal data for a specific sensor
    """
    query = f"""
    SELECT * FROM {SCYLLA_KEYSPACE}.abnormal_data
    WHERE sensor_id = %s
    """
    rows = scylla_session.execute(query, [sensor_id])
    
    return [{
        "timestamp": row.timestamp,
        "sensor_id": row.sensor_id,
        "value": row.value,
        "threshold": row.threshold,
        "status": row.status
    } for row in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
