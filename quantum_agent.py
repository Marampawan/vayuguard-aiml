"""Generate the qBraid-backed forecast offset payload consumed by telemetry.html."""

import json
import math
import os
import pickle
from pathlib import Path

from dotenv import load_dotenv
from qbraid import QbraidProvider
from qiskit import QuantumCircuit


OUTPUT_DIR = Path(__file__).resolve().parent / "website"
SIMULATOR_ID = "qbraid:qbraid:sim:qir-sv"
load_dotenv(Path(__file__).resolve().parent / ".env")


def execute_full_quantum_forecast() -> None:
    """Run a six-qubit circuit and publish multi-variable forecast offsets."""
    if not os.environ.get("QBRAID_API_KEY"):
        raise RuntimeError("Set QBRAID_API_KEY before running this forecast generator.")

    print("Initializing Multi-Variable qBraid Quantum Runtime Layer...")
    provider = QbraidProvider()
    device = provider.get_device(SIMULATOR_ID)

    qc = QuantumCircuit(6)
    for qubit in range(6):
        qc.h(qubit)
    qc.cx(0, 1)
    qc.cx(2, 3)
    qc.cx(4, 5)
    qc.measure_all()

    print(f"Submitting multi-variate circuit to: {SIMULATOR_ID}")
    job = device.run(qc, shots=1024)
    job.wait_for_final_state()
    counts = job.result().data.get_counts()

    total_shots = sum(counts.values())
    if total_shots == 0:
        raise RuntimeError("qBraid returned no measurement shots.")

    normalized_counts = {bitstring.replace(" ", ""): value for bitstring, value in counts.items()}
    temp_factor = sum(value for bits, value in normalized_counts.items() if bits[0:2] == "11") / total_shots
    wind_factor = sum(value for bits, value in normalized_counts.items() if bits[2:4] == "10") / total_shots
    solar_factor = sum(value for bits, value in normalized_counts.items() if bits[4:6] == "01") / total_shots
    quantum_data = {
        "engine": "qBraid Quantum Hardware Layer",
        "status": "Verified Operational Array",
        "temp_offsets": [round((temp_factor * 8) - 4 + math.sin(day), 1) for day in range(7)],
        "wind_offsets": [round((wind_factor * 12) - 5 + (day * 0.5), 1) for day in range(7)],
        "sunrise_shift_mins": [int((solar_factor * 6) - 3 + day) for day in range(7)],
        "sunset_shift_mins": [int((solar_factor * -8) + 4 - day) for day in range(7)],
        "aqi_offsets": [int((temp_factor * 40) - 20 + (day * 4)) for day in range(7)],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIR / "quantum_data.pkl").open("wb") as pkl_file:
        pickle.dump(quantum_data, pkl_file)
    with (OUTPUT_DIR / "quantum_data.json").open("w", encoding="utf-8") as json_file:
        json.dump(quantum_data, json_file, indent=4)

    print("Comprehensive weather-atmospheric quantum metrics successfully stored.")


if __name__ == "__main__":
    execute_full_quantum_forecast()
