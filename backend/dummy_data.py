import random
import requests

API_URL = "http://127.0.0.1:8000/sensor-frame"

while True:
    payload = {
        "frame_id": random.randint(0, 100),
        "timestamp_ms": random.randint(0, 100),
        "flame": random.randint(0, 100),
        "mq135_raw": random.randint(0, 100),
        "thermal": [random.randint(0, 100) for _ in range(64)]  # 64 random values
    }
    response = requests.post(API_URL, json=payload, timeout=0.2)
    print("POST", response.status_code)