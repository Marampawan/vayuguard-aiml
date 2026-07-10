"""
Simplified Quantum Hybrid — works with small datasets
Updated to read from the validated dataset and preserve true target alignment.
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pennylane as qml
import joblib
import json
import sys
import os

sys.path.append("src")
from utils import load_data


# Only 8 most important features (manually selected, avoid leakage)
KEY_FEATURES = [
    "aqi_lag_1h",      # Most recent
    "aqi_lag_24h",     # Same time yesterday
    "aqi_roll_mean_24h",  # Daily average
    "aqi_roll_mean_168h", # Weekly average
    "hour",            # Time of day
    "temperature",     # Weather
    "humidity",
    "wind_speed",
]


def simple_feature_engineering(df, horizon=24):
    """Minimal features, no leakage, using pre-validated target alignment"""
    df = df.copy()
    df = df.sort_values(["station_id", "timestamp"])
    
    # Basic time
    df["hour"] = df["timestamp"].dt.hour
    
    # Only safe lags (must exist in data)
    df["aqi_lag_1h"] = df.groupby("station_id")["aqi"].shift(1)
    df["aqi_lag_24h"] = df.groupby("station_id")["aqi"].shift(24)
    
    # Rolling (past only)
    df["aqi_roll_mean_24h"] = (
        df.groupby("station_id")["aqi"]
        .rolling(24, min_periods=1).mean()
        .reset_index(0, drop=True)
    )
    df["aqi_roll_mean_168h"] = (
        df.groupby("station_id")["aqi"]
        .rolling(168, min_periods=1).mean()
        .reset_index(0, drop=True)
    )
    
    # Use the bulletproof target column dynamically based on horizon
    target_col = f"target_aqi_{horizon}h"
    if target_col in df.columns:
        df["target"] = df[target_col]
    else:
        df["target"] = df.groupby("station_id")["aqi"].shift(-horizon)
    
    # Drop rows where lag features or targets have NaNs
    df = df.dropna(subset=["target", "aqi_lag_1h", "aqi_lag_24h"])
    
    return df


def quantum_select_features(X, y, n_select=6):
    """Tiny quantum circuit for feature selection"""
    n = X.shape[1]
    
    # Normalize
    scores = np.abs(np.corrcoef(X.T, y)[:-1, -1])
    scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    
    # PennyLane circuit
    dev = qml.device("default.qubit", wires=n)
    
    @qml.qnode(dev)
    def circuit(params):
        for i in range(n):
            qml.Hadamard(i)
        for i in range(n):
            qml.RZ(-scores[i] * params[0], wires=i)
        for i in range(n):
            qml.RX(params[1], wires=i)
        return [qml.expval(qml.PauliZ(i)) for i in range(n)]
    
    # Simple grid search
    best_energy = float('inf')
    best_params = [0, 0]
    
    for beta in np.linspace(0, np.pi, 10):
        for gamma in np.linspace(0, 2*np.pi, 10):
            expvals = circuit([beta, gamma])
            probs = [(1-e)/2 for e in expvals]
            energy = -sum(scores[i]*probs[i] for i in range(n)) + 0.3*sum(probs)
            if energy < best_energy:
                best_energy = energy
                best_params = [beta, gamma]
    
    # Select top by probability
    final = circuit(best_params)
    final_probs = [(1-e)/2 for e in final]
    selected = np.argsort(final_probs)[-n_select:][::-1]
    
    return selected.tolist()


def train_simple_quantum(df, horizon=24):
    """Train with minimal features + quantum selection"""
    print(f"\n{'='*60}")
    print(f"SIMPLE QUANTUM HYBRID ({horizon}h ahead)")
    print(f"{'='*60}")
    
    df = simple_feature_engineering(df, horizon=horizon)
    print(f"Samples after engineering: {len(df)}")
    
    # Use only available key features
    available = [f for f in KEY_FEATURES if f in df.columns]
    print(f"Available features: {available}")
    
    X = df[available].values
    y = df["target"].values
    
    # Quantum selection
    print("\nRunning quantum feature selection..." )
    selected_idx = quantum_select_features(X, y, n_select=min(6, len(available)))
    selected_features = [available[i] for i in selected_idx]
    print(f"Selected: {selected_features}")
    
    X_sel = X[:, selected_idx]
    
    # Simple train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_sel, y, test_size=0.2, random_state=42
    )
    
    # Train
    model = xgb.XGBRegressor(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    
    print(f"\nResults:")
    print(f"  MAE:  {mae:.2f}")
    print(f"  RMSE: {rmse:.2f}")
    print(f"  R²:   {r2:.3f}")
    print(f"  MAPE: {mape:.2f}%")
    
    # Save the models cleanly based on the specific horizon
    os.makedirs("models_saved", exist_ok=True)
    joblib.dump(model, f"models_saved/quantum_hybrid_{horizon}h.pkl")
    
    metrics = {
        "model": "simple_quantum",
        "horizon": horizon,
        "mae": mae, "rmse": rmse, "r2": r2, "mape": mape,
        "features": selected_features
    }
    with open("models_saved/simple_quantum_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    # Also save the features list json separate for API serving consistency
    with open(f"models_saved/quantum_hybrid_{horizon}h_features.json", "w") as f:
        json.dump({"features": selected_features}, f, indent=2)
    
    return model, metrics


if __name__ == "__main__":
    processed_path = "data/processed/clean_delhi.csv"
    if os.path.exists(processed_path):
        print(f"📂 Loading validated dataset from: {processed_path}")
        df = pd.read_csv(processed_path, parse_dates=["timestamp"])
    else:
        print("⚠️ Validated dataset not found. Falling back to sample data.")
        df = load_data()
        
    # Train for all three target horizons sequentially
    for horizon in [24, 48, 72]:
        train_simple_quantum(df, horizon=horizon)