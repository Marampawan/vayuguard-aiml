"""
FastAPI Serving Layer for VayuGuard ML
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils import aqi_category

app = FastAPI(title="VayuGuard ML API", version="1.0.0")
models = {}
feature_lists = {}

@app.on_event("startup")
async def load_models():
    print("Loading models...")
    model_types = ["xgboost", "quantum_hybrid", "simple_quantum"]
    horizons = [24, 48, 72]
    
    loaded = 0
    for model_type in model_types:
        for horizon in horizons:
            key = f"{model_type}_{horizon}h"
            model_path = f"models_saved/{key}.pkl"
            feat_path = f"models_saved/{key}_features.json"
            
            if os.path.exists(model_path) and os.path.exists(feat_path):
                models[key] = joblib.load(model_path)
                with open(feat_path) as f:
                    data = json.load(f)
                    # FIXED: Handle both dictionary formats and raw list formats safely!
                    if isinstance(data, dict) and "features" in data:
                        feature_lists[key] = data["features"]
                    else:
                        feature_lists[key] = data
                print(f"  Loaded: {key}")
                loaded += 1

    # Fallback to load the base simple_quantum if horizon-specific ones aren't found
    if "quantum_hybrid_24h" not in models and os.path.exists("models_saved/simple_quantum.pkl"):
        models["quantum_hybrid_24h"] = joblib.load("models_saved/simple_quantum.pkl")
        with open("models_saved/simple_quantum_metrics.json") as f:
            m = json.load(f)
            feature_lists["quantum_hybrid_24h"] = m.get("features", [])
        print("  Loaded: simple_quantum (as quantum_hybrid_24h fallback)")
        loaded += 1

    print(f"Total loaded: {loaded} models")

class ForecastRequest(BaseModel):
    city: str
    station_id: str
    current_data: Dict[str, float]
    horizons: List[int] = [24, 48, 72]
    model_type: str = "quantum_hybrid"

class HealthRiskRequest(BaseModel):
    forecast_aqi: float
    user_profile: Dict[str, bool]

@app.get("/health")
def health():
    return {"status": "healthy", "models_loaded": list(models.keys())}

@app.post("/forecast")
def forecast(req: ForecastRequest):
    results = []
    for h in req.horizons:
        key = f"{req.model_type}_{h}h"
        if key not in models:
            # Skip gracefully if a horizon (like 48h or 72h) isn't trained yet
            continue

        model = models[key]
        features = feature_lists[key]
        
        # Extract the specific features this model needs, default to 0.0 if missing
        row = {f: req.current_data.get(f, 0.0) for f in features}
        X = pd.DataFrame([row])

        try:
            # Try Pandas DataFrame format (Works for Classical XGBoost)
            pred = float(model.predict(X)[0])
        except Exception:
            # Fallback to raw Numpy Array (Works for Quantum Hybrid)
            pred = float(model.predict(X.values)[0])

        pred = max(0, min(500, pred))
        results.append({
            "horizon_hours": h,
            "predicted_aqi": round(pred, 1),
            "category": aqi_category(pred)
        })

    if not results:
        raise HTTPException(status_code=400, detail=f"No models found for type '{req.model_type}' at the requested horizons.")

    return {
        "city": req.city,
        "station_id": req.station_id,
        "forecasts": results,
        "model": req.model_type,
        "time": datetime.now().isoformat()
    }

@app.post("/health-risk")
def health_risk(req: HealthRiskRequest):
    aqi = req.forecast_aqi
    p = req.user_profile
    base = 1 if aqi <= 100 else 2 if aqi <= 150 else 3 if aqi <= 200 else 4 if aqi <= 300 else 5
    risk = min(5, base + int(p.get("has_asthma", False)) + int(p.get("elderly", False)))
    
    levels = {1: "Low", 2: "Moderate", 3: "High", 4: "Very High", 5: "Severe"}
    advices = {
        1: "Air quality acceptable. No special precautions.",
        2: "Sensitive individuals should limit outdoor exertion.",
        3: "Reduce outdoor activities. Keep windows closed.",
        4: "Avoid outdoor exercise. Use N95 masks.",
        5: "Emergency: avoid all outdoor exposure."
    }
    
    precautions = []
    if p.get("has_asthma") and risk >= 3: precautions.append("Keep rescue inhaler handy")
    if p.get("outdoor_worker") and risk >= 3: precautions.append("Reschedule outdoor work")
    
    return {
        "risk_level": risk,
        "risk_category": levels[risk],
        "advisory": advices[risk],
        "precautions": precautions
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)