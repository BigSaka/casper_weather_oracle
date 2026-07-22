"""
Casper WeatherOracle MCP Server
Exposes weather readings to AI agents via Model Context Protocol
"""
import json
from datetime import datetime

# Mock readings (in production, fetch from API)
READINGS = {
    'rainfall_mm': {'value': 31.5, 'confidence_pct': 98, 'timestamp': datetime.now().isoformat()},
    'wind_speed_kmh': {'value': 61.3, 'confidence_pct': 94, 'timestamp': datetime.now().isoformat()},
    'temperature_c': {'value': 36.0, 'confidence_pct': 89, 'timestamp': datetime.now().isoformat()},
}

class WeatherOracleMCP:
    """MCP Server for WeatherOracle"""
    
    def __init__(self):
        self.name = "WeatherOracle"
        self.version = "1.0.0"
    
    def get_readings(self, region: str = "miami"):
        """Get latest weather readings for a region"""
        return {
            "region": region,
            "readings": READINGS,
            "source": "casper-weather-oracle",
            "contract": "012def50b8112e8974bc49a48a389b92d92b3e48bbfc48ec3cbab97a91bad5c8f8",
            "network": "casper-testnet"
        }
    
    def get_reading(self, metric: str):
        """Get a specific metric reading"""
        if metric in READINGS:
            return {
                "metric": metric,
                "data": READINGS[metric],
                "source": "casper-weather-oracle"
            }
        return {"error": f"Metric {metric} not found"}
    
    def get_confidence_score(self):
        """Get average confidence across all metrics"""
        values = [r['confidence_pct'] for r in READINGS.values()]
        avg = sum(values) / len(values) if values else 0
        return {
            "average_confidence_pct": round(avg, 1),
            "metrics_count": len(READINGS),
            "timestamp": datetime.now().isoformat()
        }

# FastAPI wrapper for MCP
from fastapi import FastAPI

app = FastAPI()
mcp = WeatherOracleMCP()

@app.get("/mcp/readings")
def mcp_readings(region: str = "miami"):
    """MCP: Get all weather readings"""
    return mcp.get_readings(region)

@app.get("/mcp/reading/{metric}")
def mcp_reading(metric: str):
    """MCP: Get specific metric reading"""
    return mcp.get_reading(metric)

@app.get("/mcp/confidence")
def mcp_confidence():
    """MCP: Get confidence score"""
    return mcp.get_confidence_score()

@app.get("/mcp/info")
def mcp_info():
    """MCP: Server info"""
    return {
        "name": mcp.name,
        "version": mcp.version,
        "description": "Casper WeatherOracle — autonomous agent posting verified weather data on-chain",
        "endpoints": [
            "/mcp/readings?region=miami",
            "/mcp/reading/{metric}",
            "/mcp/confidence",
            "/mcp/info"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)
