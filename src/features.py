"""
Feature Engineering for VayuGuard
"""
import pandas as pd
import numpy as np

def engineer_features(df):
    """Transform raw AQI data into ML features"""
    df = df.copy()
    df = df.sort_values(["station_id", "timestamp"])
    
    # Time features
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["month"] = df["timestamp"].dt.month
    df["day_of_year"] = df["timestamp"].dt.dayofyear
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_morning_rush"] = ((df["hour"] >= 7) & (df["hour"] <= 10)).astype(int)
    df["is_evening_rush"] = ((df["hour"] >= 17) & (df["hour"] <= 21)).astype(int)
    
    # Cyclical encoding
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    
    # ========== LAG FEATURES (gap-aware) ==========
    # Check if data has gaps - if so, use time-based merge instead of shift
    df["time_diff"] = df.groupby("station_id")["timestamp"].diff().dt.total_seconds() / 3600
    has_gaps = (df["time_diff"] > 2).any()
    
    if has_gaps:
        print("  ⚠️  Data has time gaps. Using robust lag calculation.")
        # Use merge-based lag for gap handling
        for lag in [1, 2, 3, 6, 12, 24, 48]:
            lag_df = df[["timestamp", "station_id", "aqi"]].copy()
            lag_df["timestamp"] = lag_df["timestamp"] + pd.Timedelta(hours=lag)
            lag_df = lag_df.rename(columns={"aqi": f"aqi_lag_{lag}h"})
            df = pd.merge(df, lag_df, on=["timestamp", "station_id"], how="left")
    else:
        # Normal shift (fast)
        for lag in [1, 2, 3, 6, 12, 24, 48]:
            df[f"aqi_lag_{lag}h"] = df.groupby("station_id")["aqi"].shift(lag)
            
    # Lag weather features
    for lag in [1, 3, 6, 24]:
        df[f"temp_lag_{lag}h"] = df.groupby("station_id")["temperature"].shift(lag)
        df[f"wind_lag_{lag}h"] = df.groupby("station_id")["wind_speed"].shift(lag)
        df[f"humidity_lag_{lag}h"] = df.groupby("station_id")["humidity"].shift(lag)
    
    # Rolling statistics
    for window in [6, 12, 24, 48, 168]:
        df[f"aqi_roll_mean_{window}h"] = (
            df.groupby("station_id")["aqi"]
            .rolling(window=window, min_periods=1).mean()
            .reset_index(0, drop=True)
        )
        df[f"aqi_roll_std_{window}h"] = (
            df.groupby("station_id")["aqi"]
            .rolling(window=window, min_periods=1).std()
            .reset_index(0, drop=True)
        )
        df[f"aqi_roll_max_{window}h"] = (
            df.groupby("station_id")["aqi"]
            .rolling(window=window, min_periods=1).max()
            .reset_index(0, drop=True)
        )
    
    # Rate of change
    df["aqi_diff_1h"] = df.groupby("station_id")["aqi"].diff(1)
    df["aqi_diff_24h"] = df.groupby("station_id")["aqi"].diff(24)
    
    # Weather interactions
    df["temp_x_wind"] = df["temperature"] * df["wind_speed"]
    df["humidity_x_temp"] = df["humidity"] * df["temperature"]
    
    # Wind direction numeric
    wind_map = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270, "NW": 315}
    df["wind_direction_deg"] = df["wind_direction"].map(wind_map)
    df["wind_dir_sin"] = np.sin(2 * np.pi * df["wind_direction_deg"] / 360)
    df["wind_dir_cos"] = np.cos(2 * np.pi * df["wind_direction_deg"] / 360)
    
    # Targets
    df["target_aqi_24h"] = df.groupby("station_id")["aqi"].shift(-24)
    df["target_aqi_48h"] = df.groupby("station_id")["aqi"].shift(-48)
    df["target_aqi_72h"] = df.groupby("station_id")["aqi"].shift(-72)
    
    # Clean
    df = df.dropna(subset=["target_aqi_24h"])
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    
    return df


def get_feature_columns(df, target_col="target_aqi_24h"):
    """Return feature columns (exclude targets and metadata)"""
    exclude = [
        "timestamp", "station_id", "city", "wind_direction",
        "target_aqi_24h", "target_aqi_48h", "target_aqi_72h", "aqi",
        "time_diff" # Ensuring the temporary time_diff column is excluded
    ]
    return [c for c in df.columns if c not in exclude]


if __name__ == "__main__":
    from utils import load_data
    
    df = load_data()
    print(f"Original: {df.shape}")
    
    df_feat = engineer_features(df)
    print(f"After features: {df_feat.shape}")
    
    features = get_feature_columns(df_feat)
    print(f"Feature count: {len(features)}")
    print(f"First 10: {features[:10]}")