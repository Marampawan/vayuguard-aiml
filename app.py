import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qbraid import QbraidProvider

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = QbraidProvider()

# Initialize qBraid Simulator or fallback to Aer
try:
    qpu_device = provider.get_device("qbraid:qbraid:sim:qir-sv")
    print("✅ Connected to qBraid QIR Simulator")
except Exception as e:
    print(f"⚠️ qBraid QRN fallback activated: {e}")
    qpu_device = None

class TelemetryPayload(BaseModel):
    temp: float
    humidity: float
    pressure: float
    wind: float
    current_aqi: int

@app.post("/api/quantum-predict")
def run_quantum_prediction(data: TelemetryPayload):
    try:
        # 1. Map Live Atmospheric Readings to Quantum Rotation Angles
        theta1 = (data.temp / 50.0) * np.pi
        theta2 = (data.humidity / 100.0) * np.pi
        theta3 = (data.pressure / 1100.0) * np.pi
        theta4 = (data.wind / 50.0) * np.pi

        # 2. Build 2-Qubit Entangled Quantum Circuit
        qc = QuantumCircuit(2, 2)
        qc.ry(theta1, 0)
        qc.ry(theta2, 1)
        qc.cx(0, 1)  # Entanglement
        qc.rz(theta3 - theta4, 1)
        qc.measure([0, 1], [0, 1])

        counts = {}

        # 3. Execute Quantum Simulation
        if qpu_device:
            try:
                job = qpu_device.run(qc, shots=1000)
                res = job.result()
                counts = res.get_counts() if hasattr(res, 'get_counts') else getattr(res, 'counts', {'00': 500, '11': 500})
            except Exception as qerr:
                print(f"qBraid runtime job error: {qerr}, falling back to local Aer simulator")
                sim = AerSimulator()
                counts = sim.run(qc, shots=1000).result().get_counts()
        else:
            sim = AerSimulator()
            counts = sim.run(qc, shots=1000).result().get_counts()

        # 4. Extract Quantum Shift & Expectation Values
        total_shots = sum(counts.values()) if counts else 1000
        prob_00 = counts.get('00', 0) / total_shots
        prob_11 = counts.get('11', 0) / total_shots
        
        quantum_shift = int((prob_00 - prob_11) * 25)

        return {
            "status": "success",
            "quantumShift": quantum_shift,
            "predictions": {
                "h24": max(15, min(500, data.current_aqi + quantum_shift)),
                "h42": max(15, min(500, int(data.current_aqi * 0.9) + quantum_shift)),
                "h72": max(15, min(500, int(data.current_aqi * 1.2) + quantum_shift))
            }
        }
    except Exception as err:
        print(f"Error processing request: {err}")
        return {"status": "error", "message": str(err)}