import nbformat as nbf

nb = nbf.v4.new_notebook()

# 1. Title Cell
md_cell = """# 🌍 VayuGuard AI/ML Dashboard
## Quantum-Classical Hybrid AQI Forecasting System
**Capstone Project | AI/ML Track**"""

# 2. Setup Cell
code_setup = """# Cell 1: Setup & Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import requests
import os
import sys

sys.path.append('../src')
from utils import load_data, aqi_category

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("Set2")
print("✅ Dashboard setup complete")"""

# 3. Metrics Cell
code_metrics = """# Cell 2: Load All Model Metrics
models_data = []
configs = [
    ('Prophet Baseline', 'Baseline', '../models_saved/prophet_Delhi_metrics.json'),
    ('XGBoost Classical', 'Classical ML', '../models_saved/xgboost_24h_metrics.json'),
    ('Quantum Hybrid', 'Quantum-Classical', '../models_saved/simple_quantum_metrics.json')
]

for name, mtype, path in configs:
    if os.path.exists(path):
        with open(path) as f:
            m = json.load(f)
        models_data.append({
            'Model': name, 'Type': mtype, 
            'MAE': round(m.get('mae', m.get('avg_mae', 0)), 2),
            'R²': round(m.get('r2', m.get('avg_r2', 0)), 3)
        })

df_models = pd.DataFrame(models_data)
print(df_models.to_string(index=False) if not df_models.empty else "⚠️ No metrics found.")"""

# 4. Charts Cell
code_charts = """# Cell 3: Model Comparison Charts
if not df_models.empty:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    colors = ['#e74c3c' if 'Quantum' in m else '#3498db' for m in df_models['Model']]
    
    axes[0].barh(df_models['Model'], df_models['MAE'], color=colors)
    axes[0].set_title('📉 MAE (Lower is Better)')
    
    axes[1].barh(df_models['Model'], df_models['R²'], color=colors)
    axes[1].set_title('🎯 R² Score (Higher is Better)')
    axes[1].set_xlim(0, 1)
    
    plt.tight_layout()
    plt.savefig('../models_saved/dashboard_comparison.png')
    plt.show()"""

# 5. API Cell
code_api = """# Cell 4: Live API Test
BASE = "http://localhost:8000"
try:
    r = requests.get(f"{BASE}/health", timeout=5)
    print(f"✅ API Status: {r.json()['status']}")
    
    req = {
        "city": "Delhi", "station_id": "station_0",
        "current_data": {"aqi": 180, "aqi_lag_1h": 175, "aqi_lag_24h": 190, "aqi_roll_mean_24h": 182, "aqi_roll_mean_168h": 178, "hour": 14, "humidity": 65, "wind_speed": 5, "temperature": 28},
        "horizons": [24, 48, 72], "model_type": "quantum_hybrid"
    }
    
    res = requests.post(f"{BASE}/forecast", json=req).json()
    print(f"\\n🔮 Forecast for {res['city']}:")
    for f in res['forecasts']:
        print(f"  +{f['horizon_hours']}h: AQI {f['predicted_aqi']} ({f['category']})")
except Exception as e:
    print(f"❌ API Error: Make sure your FastAPI server is running in another terminal!\\nError: {e}")"""

# Assemble the notebook
nb['cells'] = [
    nbf.v4.new_markdown_cell(md_cell),
    nbf.v4.new_code_cell(code_setup),
    nbf.v4.new_code_cell(code_metrics),
    nbf.v4.new_code_cell(code_charts),
    nbf.v4.new_code_cell(code_api)
]

# Save safely as standard JSON
with open('vayuguard_dashboard.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print("✅ Jupyter Notebook successfully created!")