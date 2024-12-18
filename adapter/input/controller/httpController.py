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
