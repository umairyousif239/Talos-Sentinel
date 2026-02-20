from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from backend.api.vision import router as vision_router
from backend.api.alerts import router as alerts_router
from backend.api.sensors import router as sensors_router
from backend.api.login import router as auth_router, get_password_hash

from backend.modules.auth_store import init_auth_db, create_user_in_db
from backend.modules.alert_loop import alert_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auth Database Startup
    init_auth_db()
    # seed the admin account if it already doesnt exist
    hashed_pw = get_password_hash("fyp2026")
    create_user_in_db("admin", hashed_pw)
    print("Auth Database initialized")
    # Surveillance Startup
    task = asyncio.create_task(alert_loop())
    print("✅ Alert evaluation loop started")

    yield  # App runs here

    # Shutdown (optional cleanup)
    task.cancel()
    print("🛑 Shutting down backend")

app = FastAPI(
    title="AI Surveillance Backend",
    description="Edge Inference and Streaming",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Usage of login API
app.include_router(auth_router)

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
        "services": ["vision", "sensors", "alerts"],
        "alerts_mode": "background"
    }