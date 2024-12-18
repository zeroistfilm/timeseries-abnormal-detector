from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from adapter.output.entity.sensor_events import SensorDataReceived
from adapter.output.entity.sensor_data import SensorData
from adapter.input.controller.httpController import router
from application.services.sensor_service import SensorService
from application.services.MinVentService import MinVentService

sensorService = SensorService()
minVentService = MinVentService()
app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    await sensorService.initialize()
    scheduler = AsyncIOScheduler()
    async def scheduled_task():
        farm_config = [
            # {"farm_id": "503", "farm_name": "동송농장", "sectors": 2},
            {"farm_id": "505", "farm_name": "장곡농장", "sectors": 3},
            # {"farm_id": "507", "farm_name": "최율농장", "sectors": 2},
            {"farm_id": "101", "farm_name": "망성농장", "sectors": 19},
            {"farm_id": "102", "farm_name": "새론농장", "sectors": 13},
            {"farm_id": "103", "farm_name": "김제농장", "sectors": 5},
            {"farm_id": "104", "farm_name": "고산농장", "sectors": 4},
            {"farm_id": "105", "farm_name": "고창농장", "sectors": 4},
            {"farm_id": "106", "farm_name": "신왕농장", "sectors": 12},
            {"farm_id": "201", "farm_name": "수지농장", "sectors": 9},
            {"farm_id": "202", "farm_name": "반곡농장", "sectors": 7},
        ]
        for farm in farm_config:
            for sector in range(1, farm["sectors"]+1):
                try:
                    await sensorService.process_data(farm["farm_id"], sector)

                except Exception as e:
                    print(farm["farm_id"], sector, e)

                try:
                    await minVentService.calcMinVent(farm["farm_id"], sector)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(farm["farm_id"], sector, e)
        # for sector in range(1, 20):
        #     await sensorService.process_data(101, sector)


    scheduler.add_job(scheduled_task, 'interval', seconds=120)
    scheduler.start()




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
