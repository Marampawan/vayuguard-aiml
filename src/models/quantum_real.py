"""
Quantum Hybrid — Real IBM Quantum Hardware via qBraid
"""
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pennylane as qml
import joblib
import json
import os
import sys

sys.path.append("src")
from utils import load_data
from models.simple_quantum import simple_feature_engineering, KEY_FEATURES

def quantum_select_real_hardware(X, y, n_select=6, api_key=None, backend_name=None):
    n = X.shape[1]
    scores = np.abs(np.corrcoef(X.T, y)[:-1, -1])
    scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    
    print(f"\n{'='*60}")
    print("QUANTUM FEATURE SELECTION — REAL HARDWARE")
    print(f"{'='*60}")
    
    backend_used = "local_simulator"
    
    if api_key:
        try:
            from qbraid import QbraidProvider
            print("Connecting to qBraid cloud...")
            provider = QbraidProvider(api_key=api_key)
            devices = provider.get_devices()
            
            ibm_devices = [d for d in devices if d.id.startswith('ibm_') and d.status == 'ONLINE']
            
            if ibm_devices:
                if backend_name:
                    device = provider.get_device(backend_name)
                else:
                    device = max(ibm_devices, key=lambda d: d.num_qubits)
                
                backend_name = device.id
                print(f"Selected: {device.id} ({device.num_qubits} qubits)")
                
                from pennylane_qiskit import IBMQDevice
                dev = IBMQDevice(wires=n, backend=backend_name, ibqx_token=api_key, shots=1024)
                backend_used = device.id
                print("Running on REAL quantum hardware!")
            else:
                print("No IBM devices online. Using simulator.")
                dev = qml.device("default.qubit", wires=n)
                
        except Exception as e:
            print(f"qBraid error: {e}")
            print("Falling back to simulator.")
            dev = qml.device("default.qubit", wires=n)
    else:
        print("No API key. Using local simulator.")
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

    best_energy = float('inf')
    best_params = [0, 0]
    
    for beta in np.linspace(0, np.pi, 10):
        for gamma in np.linspace(0, 2 * np.pi, 10):
            try:
                expvals = circuit([beta, gamma])
                probs = [(1 - e) / 2 for e in expvals]
                energy = -sum(scores[i] * probs[i] for i in range(n)) + 0.3 * sum(probs)
                
                if energy < best_energy:
                    best_energy = energy
                    best_params = [beta, gamma]
            except Exception as e:
                continue
                
    final = circuit(best_params)
    final_probs = [(1 - e) / 2 for e in final]
    selected = np.argsort(final_probs)[-n_select:][::-1]
    
    print(f"\nBackend: {backend_used}")
    print(f"Selected: {len(selected)} features")
    return selected.tolist(), backend_used

def train_quantum_real(df, api_key=None, backend_name=None):
    print(f"\n{'='*60}")
    print("TRAINING WITH REAL QUANTUM HARDWARE")
    print(f"{'='*60}")
    
    df = simple_feature_engineering(df)
    available = [f for f in KEY_FEATURES if f in df.columns]
    X = df[available].values
    y = df["target"].values
    
    selected_idx, backend = quantum_select_real_hardware(
        X, y, n_select=6, api_key=api_key, backend_name=backend_name
    )
    
    selected_features = [available[i] for i in selected_idx]
    print(f"Selected: {selected_features}")
    
    X_sel = X[:, selected_idx]
    X_train, X_test, y_train, y_test = train_test_split(X_sel, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    
    print(f"\nResults:")
    print(f"  MAE: {mae:.2f}")
    print(f"  RMSE: {rmse:.2f}")
    print(f"  R²: {r2:.3f}")
    print(f"  MAPE: {mape:.2f}%")
    
    os.makedirs("models_saved", exist_ok=True)
    joblib.dump(model, "models_saved/quantum_real.pkl")
    
    metrics = {
        "model": "quantum_real_hardware",
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "mape": mape,
        "features": selected_features,
        "quantum_backend": backend,
        "api_used": api_key is not None
    }
    with open("models_saved/quantum_real_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    return model, metrics

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--backend", default=None)
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("QBRAID_API_KEY")
    df = load_data()
    train_quantum_real(df, api_key=api_key, backend_name=args.backend)