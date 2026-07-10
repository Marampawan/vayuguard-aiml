"""
Compare all trained models: Prophet, XGBoost, Quantum Hybrid
"""
import json
import pandas as pd

models = ["xgboost", "quantum_hybrid_qbraid"]
horizons = [24, 48, 72]

print("=" * 70)
print("MODEL COMPARISON DASHBOARD")
print("=" * 70)

results = []
for model in models:
    for h in horizons:
        path = f"models_saved/{model}_{h}h_metrics.json"
        try:
            with open(path) as f:
                m = json.load(f)
                results.append({
                    "Model": model,
                    "Horizon": f"{h}h",
                    "MAE": round(m.get("avg_mae", m.get("mae", 0)), 2),
                    "RMSE": round(m.get("avg_rmse", m.get("rmse", 0)), 2),
                    "R²": round(m.get("avg_r2", m.get("r2", 0)), 3),
                    "MAPE": round(m.get("avg_mape", m.get("mape", 0)), 2),
                    "Features": m.get("selected_features", m.get("feature_count", "N/A"))
                })
        except FileNotFoundError:
            print(f"  ⚠️  Missing: {path}")

df = pd.DataFrame(results)
print("\n" + df.to_string(index=False))
print("\n" + "=" * 70)

# Find best model per horizon
print("\n🏆 BEST MODEL PER HORIZON (by MAE):")
for h in horizons:
    h_df = df[df["Horizon"] == f"{h}h"]
    if not h_df.empty:
        best = h_df.loc[h_df["MAE"].idxmin()]
        print(f"  {h}h: {best['Model']} (MAE={best['MAE']}, R²={best['R²']})")