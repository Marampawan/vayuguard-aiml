"""
Data Validation & Cleaning for Real API Data
Self-contained version - Fixed for true 24h hour-based target alignment.
"""
import os
import sys
import glob
import pandas as pd
import numpy as np


def load_real_data(city="Delhi"):
    """
    Finds and loads the latest real data CSV file for a specific city.
    """
    pattern = f"data/raw/real_aqi_{city.lower()}_*.csv"
    files = glob.glob(pattern)
    if not files:
        print(f"❌ No real data CSV files found matching: {pattern}")
        return None
    latest = max(files, key=os.path.getctime)
    print(f"📂 Loading data file: {latest}")
    return pd.read_csv(latest, parse_dates=["timestamp"])


def validate_and_clean(df, min_samples=1000):
    """
    Clean real API data before training.
    """
    print(f"\n{'='*60}")
    print("DATA VALIDATION")
    print(f"{'='*60}")
    
    original_len = len(df)
    print(f"Original samples: {original_len}")
    
    # 1. Check required columns
    required = ["timestamp", "station_id", "city", "aqi"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"❌ Missing columns: {missing}")
        return None
    
    # 2. Check AQI validity
    valid_aqi = df["aqi"].notna() & (df["aqi"] >= 0) & (df["aqi"] <= 500)
    df = df[valid_aqi].copy()
    print(f"After AQI filter: {len(df)} (removed {original_len - len(df)})")
    
    if len(df) < min_samples:
        print(f"❌ Too few samples: {len(df)} < {min_samples}")
        return None
    
    # 3. Sort and check time continuity
    df = df.sort_values(["station_id", "timestamp"])
    
    # 4. Check for each station
    for station in df["station_id"].unique():
        station_df = df[df["station_id"] == station]
        time_diff = station_df["timestamp"].diff().dt.total_seconds() / 3600
        
        gaps = time_diff[time_diff > 2]
        if len(gaps) > 0:
            print(f"  ⚠️  Station {station}: {len(gaps)} gaps > 2h")
            print(f"     Max gap: {time_diff.max():.1f} hours")
    
    # 5. Forward fill small gaps, compute target hourly, THEN drop remaining NaNs
    filled_records = []
    for station in df["station_id"].unique():
        station_df = df[df["station_id"] == station].set_index("timestamp")
        station_df = station_df.sort_index()
        
        city_name = df[df["station_id"] == station]["city"].iloc[0]
        
        if "wind_direction" in station_df.columns:
            wind_dir_series = station_df["wind_direction"].resample("1h").last().ffill(limit=3)
        else:
            wind_dir_series = None

        # Resample to strict 1-hour sequences
        station_df = station_df.resample("1h").mean(numeric_only=True)
        
        # Forward fill up to 3 hours
        station_df = station_df.ffill(limit=3)
        
        # Compute target alignment while time-series index is complete
        station_df["target_aqi_24h"] = station_df["aqi"].shift(-24)
        
        # Safely drop rows where target or current features are genuinely missing
        station_df = station_df.dropna(subset=["aqi", "target_aqi_24h"])
        
        # Restore metadata
        station_df["station_id"] = station
        station_df["city"] = city_name
        if wind_dir_series is not None:
            station_df["wind_direction"] = wind_dir_series
        
        filled_records.append(station_df.reset_index())
    
    df = pd.concat(filled_records, ignore_index=True)
    print(f"After gap filling & alignment filtering: {len(df)}")
    
    print(f"\nAQI Statistics:")
    print(df.groupby("city")["aqi"].describe())
    
    print(f"\n✅ Data validation passed: {len(df)} samples")
    return df


def diagnose_target_alignment(df, horizon=24):
    """
    Check if target is properly aligned with features using true chronological offsets.
    """
    print(f"\n{'='*60}")
    print(f"TARGET DIAGNOSIS (horizon={horizon}h)")
    print(f"{'='*60}")
    
    corr = df["aqi"].corr(df["target_aqi_24h"])
    print(f"True Chronological AQI vs Target correlation: {corr:.3f}")
    
    if corr < 0.5:
        print("❌ WARNING: Low correlation! Target might still see seasonal fluctuations.")
    else:
        print("✅ SUCCESS: Strong physical correlation established.")
    
    sample = df[["timestamp", "station_id", "aqi", "target_aqi_24h"]].head(10)
    print(f"\nSample alignment check:")
    print(sample.to_string())
    
    return df


if __name__ == "__main__":
    df = load_real_data(city="Delhi")
    if df is not None:
        df_clean = validate_and_clean(df)
        if df_clean is not None:
            diagnose_target_alignment(df_clean, horizon=24)
            
            # Export to processed folder so the models can find it
            os.makedirs("data/processed", exist_ok=True)
            df_clean.to_csv("data/processed/clean_delhi.csv", index=False)
            print("💾 SUCCESS: Saved validated dataset to data/processed/clean_delhi.csv")