from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List

router = APIRouter(prefix="/sensors", tags=["Sensors"])

class SensorFrame(BaseModel):
    frame_id: int
    timestamp_ms: int
    flame: int
    mq135_raw: int
    thermal: List[float] = Field(..., min_length=64, max_length=64)

@router.post("/sensor-frame")
def receive_sensor_frame(frame: SensorFrame):
    print("RECEIVED:", frame.frame_id)
    return {"status": "ok"}