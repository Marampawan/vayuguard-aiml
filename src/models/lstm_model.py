"""
Deep Learning (LSTM) Model for AQI Forecasting
Uses PyTorch to build a neural network that "remembers" time-series patterns.
"""
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
import json
import os
import sys

sys.path.append("src")
from features import engineer_features, get_feature_columns
from utils import load_data

# --- PyTorch Neural Network Definition ---
class AQILSTM(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2):
        super(AQILSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 1)
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        # Take the output from the last time step in the sequence
        last_time_step = lstm_out[:, -1, :] 
        out = self.relu(self.fc1(last_time_step))
        out = self.fc2(out)
        return out.squeeze()

def create_sequences(X, y, seq_length=24):
    """Convert flat 2D data into 3D sequences [samples, sequence_length, features] for LSTM"""
    X_seq, y_seq = [], []
    for i in range(len(X) - seq_length):
        X_seq.append(X[i:(i + seq_length)])
        y_seq.append(y[i + seq_length])
    return np.array(X_seq), np.array(y_seq)

def train_lstm(df, horizon=24, seq_length=24, epochs=30):
    print(f"\n{'='*60}")
    print(f"🧠 Training Deep Learning LSTM for {horizon}h ahead")
    print(f"{'='*60}")
    
    # 1. Prepare Data
    df = engineer_features(df)
    target_col = f"target_aqi_{horizon}h"
    feature_cols = get_feature_columns(df, target_col)
    
    # Drop NaNs so sequences are continuous
    df = df.dropna(subset=[target_col] + feature_cols)
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Scale features (Neural Networks NEED scaled data)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Create 3D Sequences
    print(f"[~] Building time sequences (Length: {seq_length}h)...")
    X_seq, y_seq = create_sequences(X_scaled, y, seq_length)
    
    # Split into Train/Test (80/20 time split)
    split_idx = int(len(X_seq) * 0.8)
    X_train, X_test = X_seq[:split_idx], X_seq[split_idx:]
    y_train, y_test = y_seq[:split_idx], y_seq[split_idx:]
    
    # Convert to PyTorch Tensors
    train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=False) # Don't shuffle time series!
    
    # 2. Build Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[+] Using hardware: {device}")
    
    model = AQILSTM(input_size=len(feature_cols)).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # 3. Train Model
    print(f"[~] Training for {epochs} epochs...")
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            predictions = model(batch_X)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        if (epoch + 1) % 10 == 0:
            print(f"    Epoch {epoch+1}/{epochs} | Loss: {epoch_loss/len(train_loader):.2f}")
            
    # 4. Evaluate
    model.eval()
    with torch.no_grad():
        test_preds = model(torch.FloatTensor(X_test).to(device)).cpu().numpy()
        
    mae = mean_absolute_error(y_test, test_preds)
    rmse = np.sqrt(mean_squared_error(y_test, test_preds))
    r2 = r2_score(y_test, test_preds)
    
    print(f"\n🏆 LSTM RESULTS:")
    print(f"  MAE:  {mae:.2f}")
    print(f"  RMSE: {rmse:.2f}")
    print(f"  R²:   {r2:.3f}")
    
    # 5. Save Artifacts
    os.makedirs("models_saved", exist_ok=True)
    
    # Save the PyTorch weights
    torch.save(model.state_dict(), f"models_saved/lstm_{horizon}h.pt")
    # Save the Scaler (crucial for live API predictions!)
    joblib.dump(scaler, f"models_saved/lstm_{horizon}h_scaler.pkl")
    # Save feature names
    with open(f"models_saved/lstm_{horizon}h_features.json", "w") as f:
        json.dump(feature_cols, f)
        
    print(f"\n[✔] Successfully saved LSTM models and scaler!")

if __name__ == "__main__":
    df = load_data()
    # Let's train just the 24h horizon first to see how it performs!
    train_lstm(df, horizon=24)