"""
VayuGuard Data Engineering Pipeline
Fetches REAL historical data and can generate realistic synthetic data to fill gaps.
"""
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timedelta

# Real GPS Coordinates for our target cities
CITIES = {
    "Delhi": {"lat": 28.6139, "lon": 77.2090, "id": "station_0"},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "id": "station_1"},
    "Bangalore": {"lat": 12.9716, "lon": 77.5946, "id": "station_2"}
}

def fetch_real_data(past_days=90, save_path="data/raw/real_aqi.csv"):
    """
    Pulls real weather and pollution data from Open-Meteo APIs.
    No API keys required!
    """
    print(f"\n{'='*60}")
    print(f"🌍 DOWNLOADING REAL-TIME CLIMATE DATA ({past_days} Days)")
    print(f"{'='*60}")
    
    all_records = []
    
    for city, info in CITIES.items():
        print(f"[*] Fetching data for {city}...")
        
        # 1. Fetch Air Quality Data
        aqi_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality?"
            f"latitude={info['lat']}&longitude={info['lon']}&"
            f"hourly=pm10,pm2_5,nitrogen_dioxide,ozone,us_aqi&"
            f"past_days={past_days}&timezone=auto"
        )
        aqi_res = requests.get(aqi_url).json()
        
        # 2. Fetch Weather Data
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={info['lat']}&longitude={info['lon']}&"
            f"hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation&"
            f"past_days={past_days}&timezone=auto"
        )
        weather_res = requests.get(weather_url).json()
        
        # 3. Merge and Format Data
        times = aqi_res['hourly']['time']
        for i in range(len(times)):
            # Skip rows where AQI is missing
            if aqi_res['hourly']['us_aqi'][i] is None:
                continue
                
            # Convert wind direction degrees to categorical to match our ML pipeline
            wind_deg = weather_res['hourly']['wind_direction_10m'][i]
            if wind_deg is None: wind_dir = "N"
            else:
                dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
                wind_dir = dirs[int((wind_deg / 45) + 0.5) % 8]
            
            all_records.append({
                "timestamp": times[i],
                "station_id": info['id'],
                "city": city,
                "aqi": aqi_res['hourly']['us_aqi'][i],
                "pm25": aqi_res['hourly']['pm2_5'][i],
                "pm10": aqi_res['hourly']['pm10'][i],
                "no2": aqi_res['hourly']['nitrogen_dioxide'][i],
                "o3": aqi_res['hourly']['ozone'][i],
                "temperature": weather_res['hourly']['temperature_2m'][i],
                "humidity": weather_res['hourly']['relative_humidity_2m'][i],
                "wind_speed": weather_res['hourly']['wind_speed_10m'][i],
                "wind_direction": wind_dir,
                "precipitation": weather_res['hourly']['precipitation'][i] or 0.0
            })

    # Create DataFrame and clean it up
    df = pd.DataFrame(all_records)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Fill any minor gaps with the previous hour's data
    df = df.ffill().fillna(0)
    
    # Save the file
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    
    print(f"\n[✔] SUCCESS! Downloaded {len(df)} real-world hourly records.")
    print(f"[✔] Data saved to: {save_path}")
    return df

def generate_realistic_data(n_days=180, n_stations=3, based_on_real=None, save_path="data/raw/sample_aqi.csv"):
    """
    Generate synthetic data that mimics real AQI patterns to fix low-sample issues.
    If based_on_real dataframe is provided, it copies its statistical properties.
    """
    print(f"\n{'='*60}")
    print(f"🧪 GENERATING REALISTIC SYNTHETIC DATA ({n_days} Days)")
    print(f"{'='*60}")

    if based_on_real is not None and len(based_on_real) > 100:
        # Use real data statistics
        city_stats = based_on_real.groupby("city")["aqi"].agg(["mean", "std", "min", "max"])
        print(f"Generating data based on real statistics:\n{city_stats}\n")
        cities = based_on_real["city"].unique().tolist()
    else:
        cities = ["Delhi", "Mumbai", "Bangalore"]
        city_stats = pd.DataFrame({
            "mean": [180, 120, 80],
            "std": [50, 40, 30],
            "min": [50, 40, 30],
            "max": [400, 300, 200]
        }, index=cities)

    np.random.seed(42)
    records = []
    start_date = datetime(2024, 1, 1)

    for station_id in range(min(n_stations, len(cities))):
        city = cities[station_id]
        
        # Protect against missing stats using default fallbacks
        base_aqi = city_stats.loc[city, "mean"] if city in city_stats.index else 100
        std_aqi = city_stats.loc[city, "std"] if city in city_stats.index else 30
        
        for hour in range(n_days * 24):
            timestamp = start_date + timedelta(hours=hour)
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Daily pattern: higher in morning/evening
            daily_pattern = (std_aqi * 0.5) * np.sin((hour_of_day - 6) * np.pi / 12)**2
            
            # Weekly pattern: weekdays worse
            weekly_pattern = (std_aqi * 0.3) if day_of_week < 5 else 0
            
            # Random noise + slow trend
            noise = np.random.normal(0, std_aqi * 0.2)
            trend = hour * 0.005
            
            aqi = base_aqi + daily_pattern + weekly_pattern + noise + trend
            aqi = max(0, min(500, aqi))  # Keep in valid range
            
            # Weather correlated with AQI
            temperature = 25 + 10 * np.sin((hour_of_day - 14) * np.pi / 12) + np.random.normal(0, 2)
            humidity = 60 + np.random.normal(0, 10)
            wind_speed = max(0, 10 - (aqi / 50) + np.random.normal(0, 2))
            precipitation = max(0, np.random.exponential(0.5) if np.random.random() < 0.05 else 0)
            
            records.append({
                "timestamp": timestamp,
                "station_id": f"station_{station_id}",
                "city": city,
                "aqi": round(aqi, 1),
                "pm25": round(aqi * 0.6 + np.random.normal(0, 5), 1),
                "pm10": round(aqi * 0.8 + np.random.normal(0, 5), 1),
                "no2": round(aqi * 0.2 + np.random.normal(0, 2), 1),
                "o3": round(40 + np.random.normal(0, 10), 1),
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
                "wind_speed": round(wind_speed, 1),
                "wind_direction": np.random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
                "precipitation": round(precipitation, 1),
            })

    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    print(f"[✔] Generated {len(df)} records → {save_path}")
    return df

def load_data(path="data/raw/real_aqi.csv"):
    """Loads the data into pandas."""
    # Fallback to sample data if real data hasn't been fetched yet
    if not os.path.exists(path):
        print("Real data not found. Falling back to sample data.")
        path = "data/raw/sample_aqi.csv"
    return pd.read_csv(path, parse_dates=["timestamp"])

def aqi_category(aqi):
    """Convert AQI number to category"""
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Satisfactory"
    elif aqi <= 200: return "Moderate"
    elif aqi <= 300: return "Poor"
    elif aqi <= 400: return "Very Poor"
    else: return "Severe"

if __name__ == "__main__":
    # 1. Fetch real API data
    real_df = fetch_real_data(past_days=90)
    
    # 2. Automatically generate 180 days of gap-free, realistic data based on the API numbers!
    # This solves the "too few samples" and the missing gap issues perfectly.
    hybrid_df = generate_realistic_data(n_days=180, based_on_real=real_df, save_path="data/raw/sample_aqi.csv")