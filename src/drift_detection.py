"""
Model Drift Detection for VayuGuard
Alerts when model accuracy drops below threshold
"""
import json
import os
import numpy as np
from datetime import datetime

def check_drift(current_metrics, threshold_mape=25.0, threshold_r2=0.75):
    """
    Check if model performance has degraded.
    
    Args:
        current_metrics: dict with 'mape', 'r2', 'mae'
        threshold_mape: alert if MAPE > this %
        threshold_r2: alert if R² < this
    
    Returns:
        dict with drift status and alerts
    """
    alerts = []
    
    mape = current_metrics.get('mape', current_metrics.get('avg_mape', 0))
    r2 = current_metrics.get('r2', current_metrics.get('avg_r2', 0))
    mae = current_metrics.get('mae', current_metrics.get('avg_mae', 0))
    
    if mape > threshold_mape:
        alerts.append(f"⚠️ HIGH MAPE: {mape:.2f}% (threshold: {threshold_mape}%)")
    if r2 < threshold_r2:
        alerts.append(f"⚠️ LOW R²: {r2:.3f} (threshold: {threshold_r2})")
        
    drift_detected = len(alerts) > 0
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "drift_detected": drift_detected,
        "metrics": {
            "mape": mape,
            "r2": r2,
            "mae": mae
        },
        "thresholds": {
            "mape_max": threshold_mape,
            "r2_min": threshold_r2
        },
        "alerts": alerts,
        "recommendation": "Retrain model" if drift_detected else "Model healthy"
    }
    
    # Save to file
    os.makedirs("models_saved", exist_ok=True)
    with open("models_saved/drift_report.json", "w") as f:
        json.dump(result, f, indent=2)
        
    return result

def compare_with_baseline(current_metrics, baseline_file="models_saved/simple_quantum_metrics.json"):
    """
    Compare current metrics with original training metrics.
    """
    if not os.path.exists(baseline_file):
        return {"error": "Baseline metrics not found"}
        
    with open(baseline_file) as f:
        baseline = json.load(f)
        
    baseline_mape = baseline.get('mape', 0)
    current_mape = current_metrics.get('mape', current_metrics.get('avg_mape', 0))
    
    mape_increase = ((current_mape - baseline_mape) / baseline_mape * 100) if baseline_mape > 0 else 0
    
    return {
        "baseline_mape": baseline_mape,
        "current_mape": current_mape,
        "mape_increase_percent": mape_increase,
        "significant_drift": mape_increase > 20  # 20% increase = significant
    }

if __name__ == "__main__":
    # Test with current metrics
    test_metrics = {
        "mape": 30.5,  # High - should trigger alert
        "r2": 0.65,    # Low - should trigger alert
        "mae": 45.0
    }
    
    result = check_drift(test_metrics)
    print(json.dumps(result, indent=2))
    
    # Compare with baseline
    comparison = compare_with_baseline(test_metrics)
    print(f"\nBaseline comparison: {json.dumps(comparison, indent=2)}")