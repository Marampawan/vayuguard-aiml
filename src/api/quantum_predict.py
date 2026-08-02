"""
Simple Quantum Prediction API Endpoint
Lightweight endpoint for frontend GitHub Pages integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import time

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from quantum_integration import run_qbraid_prediction, check_qbraid_connection

app = FastAPI(title="VayuGuard Quantum Predict API", version="1.0.0")

# CORS configuration for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-username.github.io",  # Replace with your GitHub Pages URL
        "http://localhost:8000",
        "http://localhost:3000",
        "*"  # Remove this in production and specify exact origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    temp: float
    humidity: float
    wind: float


class PredictionResponse(BaseModel):
    aqi: int
    status: str
    device: str = "simulated"
    execution_time_ms: float = 0.0


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "service": "VayuGuard Quantum Prediction API",
        "status": "running",
        "endpoints": ["/api/qbraid-predict", "/health", "/quantum-status"]
    }


@app.get("/health")
def health():
    """Health check with qBraid connection status"""
    qb_status = check_qbraid_connection()
    return {
        "status": "healthy",
        "qbraid_connected": qb_status["connected"],
        "qbraid_devices": qb_status["devices"][:3] if qb_status["devices"] else []
    }


@app.get("/quantum-status")
def quantum_status():
    """Check qBraid quantum device availability"""
    return check_qbraid_connection()


@app.post("/api/qbraid-predict", response_model=PredictionResponse)
def predict_aqi(request: PredictionRequest):
    """
    Quantum AQI Prediction Endpoint
    
    Receives atmospheric telemetry (temp, humidity, wind) and returns
    quantum-corrected AQI prediction using qBraid quantum circuits.
    
    Args:
        request: PredictionRequest with temp (°C), humidity (%), wind (km/h)
    
    Returns:
        PredictionResponse with predicted AQI and execution details
    """
    start_time = time.time()
    
    try:
        # Validate input ranges
        if not (0 <= request.temp <= 60):
            raise HTTPException(status_code=400, detail="Temperature must be between 0 and 60°C")
        if not (0 <= request.humidity <= 100):
            raise HTTPException(status_code=400, detail="Humidity must be between 0 and 100%")
        if not (0 <= request.wind <= 200):
            raise HTTPException(status_code=400, detail="Wind speed must be between 0 and 200 km/h")
        
        # Run quantum prediction
        predicted_aqi = run_qbraid_prediction(
            temp=request.temp,
            humidity=request.humidity,
            wind=request.wind,
            use_simulator=True  # Use simulator by default (faster, no credits)
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        # Get device info
        qb_status = check_qbraid_connection()
        device = qb_status["devices"][0] if qb_status["devices"] else "simulated"
        
        return PredictionResponse(
            aqi=predicted_aqi,
            status="qBraid Job Complete",
            device=device,
            execution_time_ms=round(execution_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("Starting VayuGuard Quantum Prediction API...")
    print("Access docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)