"""
Quantum-Classical Hybrid: QAOA + XGBoost
FIXED: Pre-filter features + PennyLane for speed
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.feature_selection import mutual_info_regression
import joblib
import json
import os
import sys
import time

sys.path.append("src")
from features import engineer_features, get_feature_columns
from utils import load_data


# ========== PENNYLANE QUANTUM CIRCUIT ==========
import pennylane as qml

def quantum_feature_selector_pennylane(feature_scores, max_features=12, n_layers=2, steps=30):
    """
    Use PennyLane QAOA-inspired circuit for feature selection.
    Much faster than Qiskit for small problems.
    
    feature_scores: array of scores (higher = more important)
    max_features: how many features to select
    n_layers: QAOA layers (keep low for speed)
    steps: optimization steps
    """
    n = len(feature_scores)
    
    # Normalize scores to [0, 1]
    scores = np.array(feature_scores)
    scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    
    # Device: statevector simulator (fastest)
    dev = qml.device("default.qubit", wires=n)
    
    @qml.qnode(dev)
    def circuit(params):
        """
        Variational quantum circuit.
        params[0] = mixer angles (beta)
        params[1] = problem angles (gamma)
        """
        # Initialize superposition
        for i in range(n):
            qml.Hadamard(wires=i)
        
        # QAOA layers
        for layer in range(n_layers):
            # Problem Hamiltonian (cost) - encode feature scores
            for i in range(n):
                # Higher score = lower energy when selected
                qml.RZ(-scores[i] * params[1][layer], wires=i)
            
            # Mixer Hamiltonian
            for i in range(n):
                qml.RX(params[0][layer], wires=i)
        
        # Measure in Z basis
        return qml.expval(qml.PauliZ(0))  # We measure all, but return first
    
    # We actually need to measure all qubits to get selection
    @qml.qnode(dev)
    def circuit_probs(params):
        for i in range(n):
            qml.Hadamard(wires=i)
        
        for layer in range(n_layers):
            for i in range(n):
                qml.RZ(-scores[i] * params[1][layer], wires=i)
            for i in range(n):
                qml.RX(params[0][layer], wires=i)
        
        # Return probabilities of |1> for each qubit
        return [qml.expval(qml.PauliZ(i)) for i in range(n)]
    
    # Initialize parameters
    beta = np.random.uniform(0, np.pi, n_layers)
    gamma = np.random.uniform(0, 2*np.pi, n_layers)
    params = np.array([beta, gamma])
    
    # Simple gradient-free optimization
    best_params = params.copy()
    best_energy = float('inf')
    
    print(f"  Optimizing quantum circuit ({n} qubits, {n_layers} layers)...")
    
    for step in range(steps):
        # Random perturbation
        new_beta = best_params[0] + np.random.normal(0, 0.1, n_layers)
        new_gamma = best_params[1] + np.random.normal(0, 0.1, n_layers)
        new_params = np.array([new_beta, new_gamma])
        
        # Evaluate
        expvals = circuit_probs(new_params)
        # expval of Z: +1 = |0>, -1 = |1>. We want |1> (selected)
        probs = [(1 - e) / 2 for e in expvals]  # Probability of |1>
        
        # Objective: maximize score of selected, penalize too many
        energy = -sum(scores[i] * probs[i] for i in range(n)) + 0.3 * sum(probs)
        
        if energy < best_energy:
            best_energy = energy
            best_params = new_params.copy()
        
        if step % 10 == 0:
            print(f"    Step {step}/{steps}, energy={best_energy:.4f}")
    
    # Final selection: top features by probability
    final_expvals = circuit_probs(best_params)
    final_probs = [(1 - e) / 2 for e in final_expvals]
    
    # Select top max_features by probability
    selected_idx = np.argsort(final_probs)[-max_features:][::-1]
    
    print(f"  Quantum circuit selected {len(selected_idx)} features")
    print(f"  Selection probabilities: {[round(final_probs[i], 3) for i in selected_idx]}")
    
    return selected_idx.tolist()


def classical_feature_selector(feature_scores, max_features=12):
    """
    Pure classical fallback: just pick top features by score.
    Use this if quantum is too slow.
    """
    scores = np.array(feature_scores)
    selected_idx = np.argsort(scores)[-max_features:][::-1]
    print(f"  Classical selection: top {max_features} features by mutual information")
    return selected_idx.tolist()


def compute_feature_scores(X, y, sample_size=2000):
    """Compute mutual information scores"""
    if len(X) > sample_size:
        idx = np.random.choice(len(X), sample_size, replace=False)
        X, y = X.iloc[idx], y.iloc[idx]
    scores = mutual_info_regression(X, y, random_state=42)
    scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    return scores


def train_quantum_hybrid(df, horizon=24, max_features=12, n_splits=5, use_quantum=True):
    """
    Full quantum-classical hybrid pipeline.
    use_quantum=True: uses PennyLane (fast)
    use_quantum=False: classical fallback (even faster)
    """
    print(f"\n{'='*60}")
    print(f"QUANTUM HYBRID {horizon}h ahead")
    print(f"{'='*60}")
    
    df = engineer_features(df)
    target = f"target_aqi_{horizon}h"
    features = get_feature_columns(df, target)
    
    X, y = df[features], df[target]
    print(f"Total features: {len(features)}, Samples: {len(df)}")
    
    # Step 1: Compute classical feature scores
    print("\n[1/3] Computing feature importance scores...")
    scores = compute_feature_scores(X, y)
    
    score_df = pd.DataFrame({
        "feature": features,
        "score": scores
    }).sort_values("score", ascending=False)
    
    print("  Top 10 features by mutual information:")
    for _, row in score_df.head(10).iterrows():
        print(f"    {row['feature']}: {row['score']:.3f}")
    
    # Step 2: Feature selection (quantum or classical)
    print("\n[2/3] Feature selection...")
    start_time = time.time()
    
    if use_quantum and len(features) <= 20:
        # Quantum for small feature sets (fast)
        selected_idx = quantum_feature_selector_pennylane(
            scores, max_features=max_features, n_layers=1, steps=20
        )
        method = "pennylane_quantum"
    elif use_quantum:
        # Too many features: pre-filter to top 20, then quantum
        print(f"  Pre-filtering to top 20 features (from {len(features)})...")
        top20_idx = np.argsort(scores)[-20:][::-1]
        top20_scores = scores[top20_idx]
        
        selected_sub_idx = quantum_feature_selector_pennylane(
            top20_scores, max_features=max_features, n_layers=1, steps=20
        )
        selected_idx = [top20_idx[i] for i in selected_sub_idx]
        method = "pennylane_quantum_prefilter"
    else:
        # Classical fallback
        selected_idx = classical_feature_selector(scores, max_features=max_features)
        method = "classical_topk"
    
    elapsed = time.time() - start_time
    print(f"  Selection took {elapsed:.1f} seconds (method: {method})")
    
    selected_features = [features[i] for i in selected_idx]
    print(f"\n  Selected features ({len(selected_features)}):")
    for feat in selected_features:
        print(f"    • {feat}")
    
    # Step 3: Train XGBoost
    print(f"\n[3/3] Training XGBoost on selected features...")
    X_sel = X[selected_features]
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_results = []
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X_sel)):
        X_train, X_val = X_sel.iloc[train_idx], X_sel.iloc[val_idx]
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
    
    avg = {k: np.mean([f[k] for f in fold_results]) for k in ["mae", "rmse", "r2", "mape"]}
    print(f"\nAverage: MAE={avg['mae']:.2f}, RMSE={avg['rmse']:.2f}, R²={avg['r2']:.3f}, MAPE={avg['mape']:.2f}%")
    
    # Final model
    final = xgb.XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1
    )
    final.fit(X_sel, y)
    
    # Save
    os.makedirs("models_saved", exist_ok=True)
    joblib.dump(final, f"models_saved/quantum_hybrid_{horizon}h.pkl")
    
    with open(f"models_saved/quantum_hybrid_{horizon}h_features.json", "w") as f:
        json.dump(selected_features, f)
    
    metrics = {
        "model": "quantum_hybrid", "horizon": horizon,
        "avg_mae": float(avg["mae"]), "avg_rmse": float(avg["rmse"]),
        "avg_r2": float(avg["r2"]), "avg_mape": float(avg["mape"]),
        "total_features": len(features), "selected_features": len(selected_features),
        "selected_feature_names": selected_features,
        "selection_method": method,
        "selection_time_sec": elapsed,
        "qaoa_layers": 1 if use_quantum else 0,
        "quantum_backend": "pennylane_statevector_simulator",
        "fold_results": fold_results
    }
    with open(f"models_saved/quantum_hybrid_{horizon}h_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    return final, selected_features, metrics


if __name__ == "__main__":
    df = load_data()
    
    # Run with quantum (PennyLane - fast!)
    for h in [24, 48, 72]:
    	train_quantum_hybrid(df, horizon=h)
    
    # Or run classical fallback for comparison:
    # train_quantum_hybrid(df, horizon=24, use_quantum=False)