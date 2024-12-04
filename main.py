from fastapi import FastAPI, WebSocket, HTTPException

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json


from adapter.output.entity.sensor_events import SensorDataReceived
from adapter.output.entity.sensor_data import SensorData

from adapter.input.controller.httpController import router, generate_data

app = FastAPI()
app.include_router(router)






@app.on_event("startup")
async def startup_event():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_data, 'interval', seconds=1)
    scheduler.start()



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
