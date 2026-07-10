"""
Scheduled Data Ingestion for VayuGuard
Fetches real data every 6 hours automatically
"""
import schedule
import time
import sys
import os
from datetime import datetime
import pandas as pd  # <--- Added Pandas import

sys.path.append("src")
from data_ingestion import fetch_city_data
from models.simple_quantum import train_simple_quantum
from utils import load_data
import joblib


def ingest_and_retrain():
    """
    1. Fetch new real data
    2. Retrain quantum model
    3. Save updated model
    """
    print(f"\n{'='*60}")
    print(f"SCHEDULED RUN: {datetime.now()}")
    print(f"{'='*60}")
    
    # Fetch data for multiple cities
    cities = ["Delhi", "Mumbai", "Bangalore"]
    all_data = []
    
    for city in cities:
        try:
            df = fetch_city_data(city=city, days_back=14)
            if df is not None:
                all_data.append(df)
                print(f"✅ {city}: {len(df)} records")
        except Exception as e:
            print(f"❌ {city}: {e}")
    
    if not all_data:
        print("No data fetched. Skipping retrain.")
        return
    
    # Combine
    combined = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined: {len(combined)} records")
    
    # Retrain model
    print("\nRetraining quantum model...")
    try:
        model, metrics = train_simple_quantum(combined)
        print(f"✅ Retrain complete: MAE={metrics['mae']:.2f}, R²={metrics['r2']:.3f}")
    except Exception as e:
        print(f"❌ Retrain failed: {e}")


def run_scheduler():
    """Run ingestion every 6 hours"""
    print("Starting scheduled ingestion...")
    print("Runs every 6 hours. Press Ctrl+C to stop.")
    
    # Run immediately once
    ingest_and_retrain()
    
    # Schedule every 6 hours
    schedule.every(6).hours.do(ingest_and_retrain)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once, don't schedule")
    args = parser.parse_args()
    
    if args.once:
        ingest_and_retrain()
    else:
        run_scheduler()