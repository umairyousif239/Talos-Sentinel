from fastapi import FastAPI
from backend.api.vision import router as vision_router
from backend.api.alerts import router as alerts_router
from backend.api.sensors import router as sensors_router

app = FastAPI(
    title="AI Surveillance Backend",
    description="Edge Inference and Streaming",
    version="0.0.1"
)

# Usage of vision API
app.include_router(vision_router)

# Usage of Sensor ingestion (ESP32 → backend) API
app.include_router(sensors_router)

# Usage of Alert evaluation & retrieval API
app.include_router(alerts_router)

# Health Check
@app.get("/")
def root():
    return {
        "status": "running",
        "services": ["vision", "sensors", "alerts"]
    }