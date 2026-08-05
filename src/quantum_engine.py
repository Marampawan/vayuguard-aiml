import os
import numpy as np
from typing import Optional

# Import qBraid and Qiskit
try:
    import qbraid
    from qiskit import QuantumCircuit
    QBRAD_AVAILABLE = True
except ImportError:
    QBRAD_AVAILABLE = False

# Import qBraid device functions (outside try-except for proper type checking)
if QBRAD_AVAILABLE:
    from qbraid import get_device  # type: ignore

# Import secure config
try:
    from src.config import QBRAID_API_KEY
except ImportError:
    from config import QBRAID_API_KEY

# Set qBraid API key from environment
if QBRAD_AVAILABLE and QBRAID_API_KEY:
    os.environ["QBRAID_API_KEY"] = QBRAID_API_KEY

def run_quantum_aqi_job(temp, wind, humidity, pm25):
    """
    Encodes atmospheric parameters into a 2-qubit quantum circuit,
    runs it on a qBraid device, and returns the quantum expectation value.
    """
    if not QBRAD_AVAILABLE:
        # Fallback to hybrid calculation if qBraid is not available
        return {
            "aqi": int(pm25 * 1.8 + (temp * 0.3)),
            "status": "HYBRID_SIMULATION",
            "error": "qBraid/Qiskit packages not installed"
        }
    
    # Create 2-qubit circuit for parameter rotation
    qc = QuantumCircuit(2, 2)
    
    # Encode weather parameters as qubit rotation angles (theta)
    theta_temp = (temp / 50.0) * np.pi
    theta_pm = (pm25 / 100.0) * np.pi
    
    qc.rx(theta_temp, 0)
    qc.ry(theta_pm, 1)
    qc.cx(0, 1)  # Entangle atmospheric features
    qc.measure([0, 1], [0, 1])

    try:
        # Dispatch job to qBraid device backend (e.g., AWS Braket SV1 / IBMQ)
        device = get_device("qbraid_qasm_simulator")  # type: ignore
        job = device.run(qc, shots=256)
        
        # Get result shots
        result = job.result()
        counts = result.measurement_counts()
        
        # Calculate quantum probability weighting for dynamic AQI shift
        prob_unhealthy = (counts.get('11', 0) + counts.get('10', 0)) / 256.0
        quantum_aqi = int(pm25 * 1.5 + (prob_unhealthy * 50))
        
        return {
            "aqi": quantum_aqi,
            "job_id": job.id,
            "status": "COMPLETED",
            "counts": counts
        }

    except Exception as e:
        # Fallback to hybrid calculation if qBraid queue/credits are unavailable
        return {
            "aqi": int(pm25 * 1.8 + (temp * 0.3)),
            "status": "HYBRID_SIMULATION",
            "error": str(e)
        }