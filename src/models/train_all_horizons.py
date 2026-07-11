import pandas as pd
import xgboost as xgb
import joblib
import json
import os
import sys

sys.path.append("src")
from utils import load_data

# The 6 optimal features your quantum circuit found
QUANTUM_FEATURES = ['aqi_roll_mean_168h', 'aqi_lag_24h', 'aqi_roll_mean_24h', 'aqi_lag_1h', 'humidity', 'wind_speed']

def fix_all_horizons(df):
    print("Training good Quantum-Hybrid models for 24h, 48h, and 72h...")
    os.makedirs("models_saved", exist_ok=True)

    for h in [24, 48, 72]:
        df_copy = df.copy().sort_values(["station_id", "timestamp"])

        # Rebuild features
        df_copy["aqi_lag_1h"] = df_copy.groupby("station_id")["aqi"].shift(1)
        df_copy["aqi_lag_24h"] = df_copy.groupby("station_id")["aqi"].shift(24)
        df_copy["aqi_roll_mean_24h"] = df_copy.groupby("station_id")["aqi"].rolling(24, min_periods=1).mean().reset_index(0, drop=True)
        df_copy["aqi_roll_mean_168h"] = df_copy.groupby("station_id")["aqi"].rolling(168, min_periods=1).mean().reset_index(0, drop=True)
        df_copy["target"] = df_copy.groupby("station_id")["aqi"].shift(-h)

        df_clean = df_copy.dropna()
        features_to_use = [f for f in QUANTUM_FEATURES if f in df_clean.columns]

        X = df_clean[features_to_use]
        y = df_clean["target"]

        # Train Model
        model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
        model.fit(X, y)

        # Save exactly how the API expects them
        joblib.dump(model, f"models_saved/quantum_hybrid_{h}h.pkl")
        with open(f"models_saved/quantum_hybrid_{h}h_features.json", "w") as f:
            json.dump({"features": features_to_use}, f)

        print(f"✅ Successfully trained and saved {h}h model!")

if __name__ == "__main__":
    df = load_data()
    fix_all_horizons(df)