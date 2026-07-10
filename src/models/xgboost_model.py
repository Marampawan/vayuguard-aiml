"""
XGBoost Model for AQI Forecasting
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import json
import os
import sys

sys.path.append("src")
from features import engineer_features, get_feature_columns
from utils import load_data


def train_xgboost(df, horizon=24, n_splits=5):
    """Train XGBoost with time-series CV"""
    print(f"\n{'='*60}")
    print(f"XGBoost {horizon}h ahead")
    print(f"{'='*60}")
    
    df = engineer_features(df)
    target = f"target_aqi_{horizon}h"
    features = get_feature_columns(df, target)
    
    X, y = df[features], df[target]
    print(f"Features: {len(features)}, Samples: {len(df)}")
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_results = []
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        model = xgb.XGBRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1
        )
        model.fit(X_train, y_train, verbose=False)
        
        preds = model.predict(X_val)
        mae = mean_absolute_error(y_val, preds)
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        r2 = r2_score(y_val, preds)
        mape = np.mean(np.abs((y_val - preds) / y_val)) * 100
        
        print(f"  Fold {fold+1}: MAE={mae:.2f}, RMSE={rmse:.2f}, R²={r2:.3f}, MAPE={mape:.2f}%")
        fold_results.append({"fold": fold+1, "mae": mae, "rmse": rmse, "r2": r2, "mape": mape})
    
    # Averages
    avg = {k: np.mean([f[k] for f in fold_results]) for k in ["mae", "rmse", "r2", "mape"]}
    print(f"\nAverage: MAE={avg['mae']:.2f}, RMSE={avg['rmse']:.2f}, R²={avg['r2']:.3f}, MAPE={avg['mape']:.2f}%")
    
    # Final model on all data
    final = xgb.XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1
    )
    final.fit(X, y)
    
    # Feature importance
    importance = pd.DataFrame({
        "feature": features,
        "importance": final.feature_importances_
    }).sort_values("importance", ascending=False)
    print(f"\nTop 10 features:\n{importance.head(10).to_string(index=False)}")
    
    # Save
    os.makedirs("models_saved", exist_ok=True)
    joblib.dump(final, f"models_saved/xgboost_{horizon}h.pkl")
    
    with open(f"models_saved/xgboost_{horizon}h_features.json", "w") as f:
        json.dump(features, f)
    
    metrics = {
        "model": "xgboost", "horizon": horizon,
        "avg_mae": float(avg["mae"]), "avg_rmse": float(avg["rmse"]),
        "avg_r2": float(avg["r2"]), "avg_mape": float(avg["mape"]),
        "fold_results": fold_results,
        "top_features": importance.head(10).to_dict("records")
    }
    with open(f"models_saved/xgboost_{horizon}h_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    return final, metrics


if __name__ == "__main__":
    df = load_data()
    for h in [24, 48, 72]:
        train_xgboost(df, horizon=h)
        print("\n" + "="*70 + "\n")