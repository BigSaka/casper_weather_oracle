from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os
import sys

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PAYMENT_ADDRESS = "012def50b8112e8974bc49a48a389b92d92b3e48bbfc48ec3cbab97a91bad5c8f8"
PAYMENT_AMOUNT_MOTES = 1224910000

readings_store = {
    'rainfall_mm': None,
    'wind_speed_kmh': None,
    'temperature_c': None,
}

class ReadingSubmission(BaseModel):
    metric_name: str
    value: float
    confidence_pct: int
    timestamp: int

@app.post("/api/submit-reading")
async def submit_reading(reading: ReadingSubmission):
    key = reading.metric_name
    if key in readings_store:
        readings_store[key] = {
            'value': reading.value,
            'confidence_pct': reading.confidence_pct,
            'timestamp': reading.timestamp,
        }
        return {"status": "ok", "metric": key}
    return {"error": "unknown_metric"}, 400

@app.get("/api/readings")
async def get_readings(request: Request):
    payment_header = request.headers.get("X-Payment", "").strip()
    if not payment_header:
        return {"error": "payment_required", "status": 402, "x_payment_address": PAYMENT_ADDRESS, "x_payment_amount_motes": str(PAYMENT_AMOUNT_MOTES)}, 402
    
    parts = payment_header.split(":")
    if len(parts) < 4 or parts[0] != "casper" or parts[1] != PAYMENT_ADDRESS or int(parts[2]) != PAYMENT_AMOUNT_MOTES:
        return {"error": "invalid_payment"}, 402
    
    return {
        "rainfall_mm": readings_store['rainfall_mm'] or {"value": 0.0, "confidence_pct": 0},
        "wind_speed_kmh": readings_store['wind_speed_kmh'] or {"value": 0.0, "confidence_pct": 0},
        "temperature_c": readings_store['temperature_c'] or {"value": 0.0, "confidence_pct": 0},
        "source": "agent-api",
        "timestamp": datetime.now().isoformat(),
        "paid": True,
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
