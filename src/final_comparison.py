"""
Final Model Comparison for VayuGuard Capstone
Compares: Baseline, XGBoost, Simple Quantum Hybrid
"""
import json
import pandas as pd
import sys
import os

sys.path.append("src")

from utils import load_data
from models.baseline import train_prophet
from models.xgboost_model import train_xgboost
from models.simple_quantum import train_simple_quantum


def compare_all_models():
    print("=" * 70)
    print("VAYUGUARD FINAL MODEL COMPARISON")
    print("=" * 70)
    
    # Load data
    df = load_data()
    print(f"\nDataset: {len(df)} samples, {df['city'].nunique()} cities")
    
    results = []
    
    # 1. Prophet Baseline
    print("\n" + "=" * 70)
    print("1. PROPHET BASELINE")
    print("=" * 70)
    for city in df["city"].unique()[:2]:  # Limit to 2 cities for speed
        try:
            r = train_prophet(df, city=city)
            results.append({
                "Model": f"Prophet-{city}",
                "Type": "Baseline",
                "MAE": round(r["mae"], 2),
                "RMSE": round(r["rmse"], 2),
                "MAPE": round(r["mape"], 2),
                "R2": "N/A"
            })
        except Exception as e:
            print(f"Prophet failed for {city}: {e}")
    
    # 2. XGBoost
    print("\n" + "=" * 70)
    print("2. XGBOOST (Classical ML)")
    print("=" * 70)
    try:
        _, xgb_metrics = train_xgboost(df, horizon=24, n_splits=3)
        results.append({
            "Model": "XGBoost",
            "Type": "Classical ML",
            "MAE": round(xgb_metrics["avg_mae"], 2),
            "RMSE": round(xgb_metrics["avg_rmse"], 2),
            "MAPE": round(xgb_metrics["avg_mape"], 2),
            "R2": round(xgb_metrics["avg_r2"], 3)
        })
    except Exception as e:
        print(f"XGBoost failed: {e}")
    
    # 3. Simple Quantum Hybrid
    print("\n" + "=" * 70)
    print("3. QUANTUM HYBRID (PennyLane QAOA + XGBoost)")
    print("=" * 70)
    try:
        _, q_metrics = train_simple_quantum(df)
        results.append({
            "Model": "Quantum Hybrid",
            "Type": "Quantum-Classical",
            "MAE": round(q_metrics["mae"], 2),
            "RMSE": round(q_metrics["rmse"], 2),
            "MAPE": round(q_metrics["mape"], 2),
            "R2": round(q_metrics["r2"], 3)
        })
    except Exception as e:
        print(f"Quantum failed: {e}")
    
    # Summary Table
    print("\n" + "=" * 70)
    print("FINAL RESULTS SUMMARY")
    print("=" * 70)
    
    summary = pd.DataFrame(results)
    print(summary.to_string(index=False))
    
    # Find winner by MAE
    best = summary.loc[summary["MAE"].idxmin()]
    print(f"\n" + "=" * 70)
    print(f"🏆 BEST MODEL: {best['Model']}")
    print(f"   MAE:  {best['MAE']}")
    print(f"   RMSE: {best['RMSE']}")
    print(f"   R²:   {best['R2']}")
    print(f"   Type: {best['Type']}")
    print("=" * 70)
    
    # Save
    os.makedirs("models_saved", exist_ok=True)
    with open("models_saved/final_comparison.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved to models_saved/final_comparison.json")
    
    return summary


if __name__ == "__main__":
    compare_all_models()