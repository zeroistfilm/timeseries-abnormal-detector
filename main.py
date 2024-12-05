from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from adapter.output.entity.sensor_events import SensorDataReceived
from adapter.output.entity.sensor_data import SensorData
from adapter.input.controller.httpController import router
from application.services.sensor_service import SensorService

sensorService = SensorService()
app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    await sensorService.initialize()
    scheduler = AsyncIOScheduler()
    async def scheduled_task():
        for sector in range(1, 4):
            await sensorService.process_data(101, sector)


    scheduler.add_job(scheduled_task, 'interval', seconds=10)
    scheduler.start()




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
