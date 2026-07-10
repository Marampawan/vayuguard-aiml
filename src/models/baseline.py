"""
Baseline: Facebook Prophet
"""
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os
import sys

sys.path.append("src")
from utils import load_data


def train_prophet(df, city="Delhi", test_days=7):
    """Train Prophet baseline for one city"""
    city_df = df[df["city"] == city].copy().sort_values("timestamp")
    
    # Prophet needs 'ds' and 'y'
    prophet_df = city_df[["timestamp", "aqi"]].rename(
        columns={"timestamp": "ds", "aqi": "y"}
    )
    
    # Split: last 7 days for test
    split = len(prophet_df) - (test_days * 24)
    train = prophet_df.iloc[:split]
    test = prophet_df.iloc[split:]
    
    print(f"\n=== Prophet: {city} ===")
    print(f"Train: {len(train)}h, Test: {len(test)}h")
    
    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
    model.fit(train)
    
    # Predict
    future = model.make_future_dataframe(periods=len(test), freq="h")
    forecast = model.predict(future)
    preds = forecast.iloc[-len(test):]["yhat"].values
    actuals = test["y"].values
    
    # Metrics
    mae = mean_absolute_error(actuals, preds)
    rmse = np.sqrt(mean_squared_error(actuals, preds))
    mape = np.mean(np.abs((actuals - preds) / actuals)) * 100
    
    print(f"MAE: {mae:.2f} | RMSE: {rmse:.2f} | MAPE: {mape:.2f}%")
    
    # Save
    os.makedirs("models_saved", exist_ok=True)
    joblib.dump(model, f"models_saved/prophet_{city}.pkl")
    
    return {"city": city, "mae": mae, "rmse": rmse, "mape": mape}


if __name__ == "__main__":
    df = load_data()
    for city in df["city"].unique():
        train_prophet(df, city=city)