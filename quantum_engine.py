import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qbraid import QbraidProvider
from typing import cast

# Initialize qBraid Simulator or fallback to Aer
_provider = None
_qpu_device = None

def _get_qbraid_device():
    global _provider, _qpu_device
    if _qpu_device is not None:
        return _qpu_device
    try:
        _provider = QbraidProvider()
        _qpu_device = _provider.get_device("qbraid:qbraid:sim:qir-sv")
        print("Connected to qBraid QIR Simulator")
    except Exception as e:
        print(f"qBraid QRN fallback activated: {e}")
        _qpu_device = None
    return _qpu_device


def run_quantum_aqi_job(temp, wind, humidity, pm25):
    """
    Run a 2-qubit quantum circuit to compute a quantum shift applied to a base AQI.

    Parameters
    ----------
    temp : float
        Temperature in degrees Celsius.
    wind : float
        Wind speed (arbitrary units matching training scale, ~0-50).
    humidity : float
        Relative humidity percentage (0-100).
    pm25 : float
        PM2.5 concentration used as the base AQI estimate.

    Returns
    -------
    dict
        A dictionary with keys:
        - status: "success" or "error"
        - quantumShift: integer shift computed from quantum measurement probabilities
        - predictions: dict with h24, h42, h72 horizon predictions
        - message: error message if status is "error"
    """
    try:
        current_aqi = int(pm25)

        # 1. Map atmospheric readings to quantum rotation angles
        theta1 = (float(temp) / 50.0) * np.pi
        theta2 = (float(humidity) / 100.0) * np.pi
        # pressure is not provided in the Flask payload; approximate from wind/humidity
        pressure = 1000.0 + (float(wind) * 2.0)
        theta3 = (pressure / 1100.0) * np.pi
        theta4 = (float(wind) / 50.0) * np.pi

        # 2. Build 2-Qubit Entangled Quantum Circuit
        qc = QuantumCircuit(2, 2)
        qc.ry(theta1, 0)
        qc.ry(theta2, 1)
        qc.cx(0, 1)  # Entanglement
        qc.rz(theta3 - theta4, 1)
        qc.measure([0, 1], [0, 1])

        counts: dict[str, int] = {}

        # 3. Execute Quantum Simulation
        qpu_device = _get_qbraid_device()
        if qpu_device:
            try:
                jobs = qpu_device.run(qc, shots=1000)
                # qBraid run() returns a list of jobs; use the first job
                job = jobs[0] if isinstance(jobs, list) else jobs
                res = job.result()
                get_counts_fn = getattr(res, "get_counts", None)
                if callable(get_counts_fn):
                    counts = cast(dict[str, int], get_counts_fn())
                else:
                    counts = cast(dict[str, int], getattr(res, "counts", {"00": 500, "11": 500}))
            except Exception as qerr:
                print(f"qBraid runtime job error: {qerr}, falling back to local Aer simulator")
                sim = AerSimulator()
                counts = sim.run(qc, shots=1000).result().get_counts()
        else:
            sim = AerSimulator()
            counts = sim.run(qc, shots=1000).result().get_counts()

        # 4. Extract Quantum Shift & Expectation Values
        total_shots = sum(counts.values()) if counts else 1000
        prob_00 = counts.get("00", 0) / total_shots
        prob_11 = counts.get("11", 0) / total_shots

        quantum_shift = int((prob_00 - prob_11) * 25)

        return {
            "status": "success",
            "quantumShift": quantum_shift,
            "predictions": {
                "h24": max(15, min(500, current_aqi + quantum_shift)),
                "h42": max(15, min(500, int(current_aqi * 0.9) + quantum_shift)),
                "h72": max(15, min(500, int(current_aqi * 1.2) + quantum_shift)),
            },
        }
    except Exception as err:
        print(f"Error processing quantum job: {err}")
        return {"status": "error", "message": str(err)}
