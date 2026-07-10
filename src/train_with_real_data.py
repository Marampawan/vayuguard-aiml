"""
Train all models using REAL data from APIs
"""
import sys
sys.path.append("src")

from data_ingestion import load_real_data, fetch_city_data
from models.xgboost_model import train_xgboost
from models.quantum_hybrid import train_quantum_hybrid
import pandas as pd


def main():
    # Try to load real data
    print("Attempting to load real data...")
    df = load_real_data(city="Delhi")
    
    # If no real data, fetch it
    if df is None:
        print("Fetching fresh data from APIs...")
        df = fetch_city_data(city="Delhi", days_back=14)
        
        if df is None:
            print("API failed. Using sample data for now.")
            from utils import generate_sample_data
            df = generate_sample_data(n_days=90, n_stations=3)
    
    print(f"\nTraining data shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Train XGBoost
    print("\n" + "="*70)
    print("TRAINING XGBOOST")
    print("="*70)
    xgb_model, xgb_metrics = train_xgboost(df, horizon=24)
    
    # Train Quantum Hybrid
    print("\n" + "="*70)
    print("TRAINING QUANTUM HYBRID")
    print("="*70)
    q_model, q_features, q_metrics = train_quantum_hybrid(df, horizon=24, use_quantum=True)
    
    # Compare
    print("\n" + "="*70)
    print("COMPARISON")
    print("="*70)
    print(f"XGBoost     - MAE: {xgb_metrics['avg_mae']:.2f}, R²: {xgb_metrics['avg_r2']:.3f}")
    print(f"Quantum Hyb - MAE: {q_metrics['avg_mae']:.2f}, R²: {q_metrics['avg_r2']:.3f}")
    
    winner = "Quantum Hybrid" if q_metrics['avg_mae'] < xgb_metrics['avg_mae'] else "XGBoost"
    print(f"\n🏆 Winner: {winner}")


if __name__ == "__main__":
    main()