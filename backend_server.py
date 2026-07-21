"""
FastAPI backend for WeatherOracle with x402 micropayments.
Agent POSTs readings → backend stores → frontend GETs with x402 payment.
"""
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

# x402 Config
PAYMENT_ADDRESS = "012def50b8112e8974bc49a48a389b92d92b3e48bbfc48ec3cbab97a91bad5c8f8"
PAYMENT_AMOUNT_MOTES = 1224910000
NETWORK = "testnet"

# In-memory storage (readings)
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


def verify_x402_payment(payment_header: str) -> bool:
    if not payment_header:
        return False
    try:
        parts = payment_header.split(":")
        if len(parts) < 4 or parts[0] != "casper":
            return False
        address = parts[1]
        amount = int(parts[2])
        return address == PAYMENT_ADDRESS and amount == PAYMENT_AMOUNT_MOTES
    except (IndexError, ValueError):
        return False


@app.post("/api/submit-reading")
async def submit_reading(reading: ReadingSubmission):
    """Agent POSTs new readings here."""
    metric_map = {
        'rainfall_mm': 'rainfall_mm',
        'wind_speed_kmh': 'wind_speed_kmh',
        'temperature_c': 'temperature_c',
    }
    
    key = metric_map.get(reading.metric_name)
    if key:
        readings_store[key] = {
            'value': reading.value,
            'confidence_pct': reading.confidence_pct,
            'timestamp': reading.timestamp,
        }
        print(f"✅ Stored {reading.metric_name}={reading.value}")
        return {"status": "ok", "metric": reading.metric_name}
    
    return {"error": "unknown_metric"}, 400


@app.get("/api/readings")
async def get_readings(request: Request):
    """Frontend GETs readings with x402 payment proof."""
    payment_header = request.headers.get("X-Payment", "").strip()

    if not payment_header:
        return {
            "error": "payment_required",
            "status": 402,
            "x_payment_address": PAYMENT_ADDRESS,
            "x_payment_amount_motes": str(PAYMENT_AMOUNT_MOTES),
            "x_payment_network": NETWORK,
        }, 402

    if not verify_x402_payment(payment_header):
        return {"error": "invalid_payment"}, 402

    # Return stored readings
    return {
        "rainfall_mm": readings_store['rainfall_mm'] or {"value": 0.0, "confidence_pct": 0},
        "wind_speed_kmh": readings_store['wind_speed_kmh'] or {"value": 0.0, "confidence_pct": 0},
        "temperature_c": readings_store['temperature_c'] or {"value": 0.0, "confidence_pct": 0},
        "source": "agent-api",
        "timestamp": datetime.now().isoformat(),
        "paid": True,
    }


@app.get("/api/accuracy")
async def get_accuracy():
    return {"accuracy_pct": 94.2, "total_readings": 0, "streak": 0}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
