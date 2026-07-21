from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

PAYMENT_ADDRESS = "012def50b8112e8974bc49a48a389b92d92b3e48bbfc48ec3cbab97a91bad5c8f8"
PAYMENT_AMOUNT_MOTES = 1224910000

readings = {}

class Reading(BaseModel):
    metric_name: str
    value: float
    confidence_pct: int
    timestamp: int

@app.post("/api/submit-reading")
def submit(r: Reading):
    readings[r.metric_name] = {"value": r.value, "confidence_pct": r.confidence_pct, "timestamp": r.timestamp}
    return {"ok": True}

@app.get("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
