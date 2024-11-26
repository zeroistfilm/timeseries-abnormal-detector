from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
from pathlib import Path

from src.domain.events.event_handlers import EventLogger
from src.domain.events.sensor_events import SensorDataReceived
from src.domain.entities.sensor_data import SensorData
from src.infrastructure.data_generator import DataGenerator
from src.infrastructure.repositories.mock_sensor_repository import MockSensorRepository

# 데이터 모델 정의
class SensorDataInput(BaseModel):
    sensor_id: str
    value: float
    timestamp: datetime

class AbnormalDataOutput(BaseModel):
    sensor_id: str
    value: float
    threshold: float
    detection_timestamp: datetime
    normalization_timestamp: Optional[datetime]
    status: str

app = FastAPI()

# Initialize components
repository = MockSensorRepository()
event_logger = EventLogger()
data_generator = DataGenerator(device_count=5, normal_range=(0, 50), abnormal_range=(50, 100))

# HTML 템플릿 디렉토리 마운트
templates_dir = Path(__file__).parent.parent.parent / "templates"
app.mount("/templates", StaticFiles(directory=str(templates_dir)), name="templates")

# 활성 WebSocket 연결을 저장할 set
active_connections = set()

@app.on_event("startup")
async def startup_event():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_data, 'interval', seconds=1)
    scheduler.start()

async def generate_data():
    """데이터를 생성하고 WebSocket으로 전송합니다."""
    try:
        sensor_data_list = data_generator.generate_data()
        for device_id, value, timestamp in sensor_data_list:
            # SensorData 객체 생성
            sensor_data = SensorData.create(
                sensor_id=device_id,
                value=value,
                timestamp=timestamp
            )
            event = SensorDataReceived(sensor_data=sensor_data)
            event_logger.log_sensor_data_received(event)
        
        # 모든 활성 WebSocket 연결에 데이터 전송
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps({"status": "success"}))
            except:
                active_connections.remove(connection)
    except Exception as e:
        print(f"Error generating data: {e}")

@app.get("/", response_class=HTMLResponse)
async def get_monitor():
    with open(templates_dir / "monitor.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/monitor-data")
async def get_monitor_data():
    return event_logger.get_monitor_data()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        while True:
            await websocket.receive_text()  # 클라이언트의 메시지를 기다립니다
    except:
        active_connections.remove(websocket)

@app.get("/abnormal")
async def get_abnormal_data():
    """현재 비정상 상태인 센서 데이터를 반환합니다."""
    return {"abnormal_devices": repository.get_abnormal_data()}

@app.post("/sensor-data")
async def insert_sensor_data(data: SensorDataInput):
    try:
        # sensor_service.process_sensor_data(
        #     data.sensor_id,
        #     data.value,
        #     data.timestamp
        # )
        return {"status": "success", "message": "Data processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/abnormal-data/{sensor_id}", response_model=List[AbnormalDataOutput])
async def get_abnormal_data(sensor_id: str):
    try:
        # return sensor_service.get_abnormal_data_by_sensor(sensor_id)
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
