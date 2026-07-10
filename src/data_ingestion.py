"""
Real-time Data Ingestion for VayuGuard
Fetches both Air Quality and Weather from Open-Meteo (Rock Solid, No API Keys)
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

OPENMETEO_WEATHER_BASE = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_AQI_BASE = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Hardcode primary city coordinates to avoid location API failures
CITY_COORDS = {
    "Delhi": {"lat": 28.6139, "lon": 77.2090, "station_id": "station_delhi_01"},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "station_id": "station_mumbai_01"},
    "Bangalore": {"lat": 12.9716, "lon": 77.5946, "station_id": "station_bangalore_01"}
}

def fetch_openmeteo_data(city="Delhi", days_back=14):
    if city not in CITY_COORDS:
        print(f"Coordinates for {city} not found. Add to CITY_COORDS.")
        return pd.DataFrame()

    coords = CITY_COORDS[city]
    lat, lon = coords["lat"], coords["lon"]
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # 1. Fetch Air Quality
    aqi_params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_str,
        "end_date": end_str,
        "hourly": ["pm10", "pm2_5", "nitrogen_dioxide", "ozone"],
        "timezone": "auto"
    }
    
    # 2. Fetch Weather
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_str,
        "end_date": end_str,
        "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "wind_direction_10m", "precipitation"],
        "timezone": "auto"
    }

    try:
        print(f"  Fetching Air Quality for {city}...")
        aqi_res = requests.get(OPENMETEO_AQI_BASE, params=aqi_params, timeout=30)
        aqi_res.raise_for_status()
        aqi_data = aqi_res.json().get("hourly", {})

        print(f"  Fetching Weather for {city}...")
        wx_res = requests.get(OPENMETEO_WEATHER_BASE, params=weather_params, timeout=30)
        wx_res.raise_for_status()
        wx_data = wx_res.json().get("hourly", {})

        records = []
        for i, ts in enumerate(aqi_data.get("time", [])):
            records.append({
                "timestamp": pd.to_datetime(ts),
                "station_id": coords["station_id"],
                "city": city,
                "pm10": aqi_data.get("pm10", [np.nan]*9999)[i],
                "pm25": aqi_data.get("pm2_5", [np.nan]*9999)[i],
                "no2": aqi_data.get("nitrogen_dioxide", [np.nan]*9999)[i],
                "o3": aqi_data.get("ozone", [np.nan]*9999)[i],
                "temperature": wx_data.get("temperature_2m", [np.nan]*9999)[i],
                "humidity": wx_data.get("relative_humidity_2m", [np.nan]*9999)[i],
                "wind_speed": wx_data.get("wind_speed_10m", [np.nan]*9999)[i],
                "wind_direction": wx_data.get("wind_direction_10m", [np.nan]*9999)[i],
                "precipitation": wx_data.get("precipitation", [np.nan]*9999)[i],
            })
        
        df = pd.DataFrame(records)
        return df
        
    except Exception as e:
        print(f"Error fetching data for {city}: {e}")
        return pd.DataFrame()

def calculate_aqi(pm25, pm10):
    if pd.isna(pm25): return np.nan
    if pm25 <= 30: aqi = pm25 * 50 / 30
    elif pm25 <= 60: aqi = 50 + (pm25 - 30) * 50 / 30
    elif pm25 <= 90: aqi = 100 + (pm25 - 60) * 100 / 30
    elif pm25 <= 120: aqi = 200 + (pm25 - 90) * 100 / 30
    elif pm25 <= 250: aqi = 300 + (pm25 - 120) * 100 / 130
    else: aqi = 400 + (pm25 - 250) * 100 / 130
    return min(500, max(0, aqi))

def deg_to_cardinal(deg):
    if pd.isna(deg): return "N"
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[round(deg / 45) % 8]

def fetch_city_data(city="Delhi", days_back=14):
    print(f"Fetching real data for: {city}...")
    
    df = fetch_openmeteo_data(city, days_back)
    if df.empty:
        return None
        
    # Calculate AQI and process wind direction
    df["aqi"] = df.apply(lambda row: calculate_aqi(row.get("pm25"), row.get("pm10")), axis=1)
    df["wind_direction"] = df["wind_direction"].apply(deg_to_cardinal)
    
    # Drop rows where AQI couldn't be calculated
    df = df.dropna(subset=["aqi"])
    
    os.makedirs("data/raw", exist_ok=True)
    output_path = f"data/raw/real_aqi_{city.lower()}_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(output_path, index=False)
    
    return df

def load_real_data(city="Delhi"):
    import glob
    pattern = f"data/raw/real_aqi_{city.lower()}_*.csv"
    files = glob.glob(pattern)
    if not files: return None
    latest = max(files, key=os.path.getctime)
    return pd.read_csv(latest, parse_dates=["timestamp"])