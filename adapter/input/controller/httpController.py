from adapter.input.dto.controllerDto import SensorDataInput, AbnormalDataOutput
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import WebSocket, HTTPException
from application.services.sensor_service import SensorService
from adapter.output.client.random_sensor_data_generator import RandomSensorDataGenerator
import traceback
import json
router = APIRouter(prefix="", tags=[""])

# 활성 WebSocket 연결을 저장할 set
active_connections = set()

sensor_service = SensorService()
data_generator = RandomSensorDataGenerator()
async def generate_data():
    """데이터를 생성하고 WebSocket으로 전송합니다."""
    try:
        # 각 센서에 대해 데이터 생성
        sensor_ids = ["sensor-1", "sensor-2", "sensor-3"]  # 예시 센서 ID들
        for sensor_id in sensor_ids:
            sensor_data = data_generator.generate_sensor_data(sensor_id)
            sensor_service.process_sensor_data(
                sensor_id=sensor_data.sensor_id,
                value=sensor_data.value,
                timestamp=sensor_data.timestamp
            )

        # 모든 활성 WebSocket 연결에 데이터 전송
        for connection in active_connections.copy():
            try:
                await connection.send_text(json.dumps({"status": "success"}))
            except:
                active_connections.remove(connection)
    except Exception as e:
        print(f"Error generating data: {e}")
        traceback.print_exc()


@router.get("/", response_class=HTMLResponse)
async def get_monitor():
    with open("./adapter/input/controller/monitor.html", "r", encoding="utf-8") as f:
        return f.read()


@router.get("/api/monitor-data")
async def get_monitor_data():
    return sensor_service.get_monitor_data()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)


@router.get("/abnormal")
async def get_abnormal_data():
    """현재 비정상 상태인 센서 데이터를 반환합니다."""
    return {"abnormal_devices": repository.get_abnormal_data()}


@router.post("/sensor-data")
async def insert_sensor_data(data: SensorDataInput):
    """새로운 센서 데이터를 추가합니다."""
    try:
        sensor_service.process_sensor_data(
            data.sensor_id,
            data.value,
            data.timestamp
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/abnormal/{sensor_id}")
async def get_abnormal_data(sensor_id: str):
    """특정 센서의 비정상 데이터를 반환합니다."""
    abnormal_data = repository.get_abnormal_data_by_id(sensor_id)
    if not abnormal_data:
        raise HTTPException(status_code=404, detail="Abnormal data not found")
    return abnormal_data
