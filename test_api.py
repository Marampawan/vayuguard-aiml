import requests
import json

BASE = "http://localhost:8000"

print("=== Forecast ===")
forecast_req = {
    "city": "Delhi",
    "station_id": "station_0",
    "current_data": {
        "aqi": 180, "pm25": 110, "pm10": 150, "temperature": 28, "humidity": 65, 
        "wind_speed": 5, "hour": 14, "day_of_week": 2, "month": 7, 
        "hour_sin": 0.5, "hour_cos": 0.866, "aqi_lag_1h": 175, "aqi_lag_24h": 190, 
        "aqi_roll_mean_24h": 182, "aqi_roll_std_24h": 15
    },
    "horizons": [24], # Changed to only ask for 24h since quantum 48/72h aren't trained
    "model_type": "quantum_hybrid"
}

r = requests.post(f"{BASE}/forecast", json=forecast_req)
print(json.dumps(r.json(), indent=2))