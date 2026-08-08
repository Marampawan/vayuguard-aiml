"""
Quantum Machine Learning Integration with qBraid
Hybrid quantum-classical circuit for AQI prediction
"""
import os
import numpy as np
from typing import Optional, Dict, Any, cast

# Import qBraid and Qiskit
try:
    import qbraid
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    QBRAD_AVAILABLE = True
except ImportError:
    QBRAD_AVAILABLE = False
    print("Warning: qBraid or Qiskit not installed. Install with: pip install qbraid qiskit qiskit-aer")

# Import qBraid device functions (outside try-except for proper type checking)
if QBRAD_AVAILABLE:
    import qbraid
    from qbraid.providers import QuantumProvider


def get_qbraid_device(device_id="qbraid_qasm_simulator"):
    try:
        provider = QuantumProvider()
        return provider.get_device(device_id)
    except Exception as e:
        print(f"Error accessing qBraid device {device_id}: {e}")
        return None

# Import secure config
try:
    from src.config import QBRAID_API_KEY
except ImportError:
    from config import QBRAID_API_KEY

# Set qBraid API key from environment
if QBRAD_AVAILABLE and QBRAID_API_KEY:
    os.environ["QBRAID_API_KEY"] = QBRAID_API_KEY


def run_qbraid_prediction(temp: float, humidity: float, wind: float, use_simulator: bool = True) -> int:
    """
    Run hybrid quantum-classical prediction for AQI
    
    Args:
        temp: Temperature in Celsius
        humidity: Humidity percentage (0-100)
        wind: Wind speed in km/h
        use_simulator: If True, use qBraid simulator; if False, use real quantum hardware
    
    Returns:
        Predicted AQI value (10-500)
    """
    if not QBRAD_AVAILABLE:
        raise RuntimeError("qBraid/Qiskit not available. Please install required packages.")
    
    if not QBRAID_API_KEY:
        raise ValueError("QBRAID_API_KEY not configured. Please set it in .env file.")
    
    # 1. Encode parameters into qubit rotation angles (radians)
    theta_temp = (temp / 50.0) * np.pi
    theta_hum = (humidity / 100.0) * np.pi
    theta_wind = (wind / 100.0) * np.pi
    
    # 2. Build 2-qubit entangled circuit using Qiskit
    qc = QuantumCircuit(2)
    
    # Encode atmospheric parameters as rotation gates
    qc.rx(theta_temp, 0)  # Temperature on qubit 0
    qc.ry(theta_hum, 1)   # Humidity on qubit 1
    qc.rz(theta_wind, 0)  # Wind as additional rotation
    
    # Create quantum entanglement between parameters
    qc.cx(0, 1)  # CNOT gate creates entanglement
    qc.cy(1, 0)  # Additional entanglement for complexity
    
    # Add measurement
    qc.measure_all()
    
    # 3. Submit execution to qBraid quantum simulator/hardware
    try:
        if use_simulator:
            # Use qBraid's quantum simulator
            device = get_qbraid_device("qbraid_qasm_simulator")
        else:
            # Use real quantum hardware (requires credits)
            device = get_qbraid_device("qbraid_qpu")
        
        if device is None:
            raise RuntimeError("qBraid device unavailable")
        
        job = device.run(qc, shots=1024)
        
        # 4. Extract Measurement Results
        result = job.result()
        counts = result.get_counts()
        
        # Calculate expectation value from quantum measurement outcomes
        prob_00 = counts.get('00', 0) / 1024.0
        prob_01 = counts.get('01', 0) / 1024.0
        prob_10 = counts.get('10', 0) / 1024.0
        prob_11 = counts.get('11', 0) / 1024.0
        
        # Quantum bias calculation based on measurement probabilities
        quantum_bias = (prob_00 - prob_11) * 20.0 + (prob_01 - prob_10) * 10.0
        
        # Calculate quantum-corrected AQI
        # Base formula: temperature and humidity increase AQI, wind decreases it
        base_aqi = 45 + (temp * 0.7) + (humidity * 0.15) - (wind * 0.3)
        predicted_aqi = int(np.clip(base_aqi + quantum_bias, 10, 500))
        
        return predicted_aqi
        
    except Exception as e:
        print(f"qBraid execution error: {e}")
        # Fallback to classical calculation
        base_aqi = 45 + (temp * 0.7) + (humidity * 0.15) - (wind * 0.3)
        return int(np.clip(base_aqi, 10, 500))


def run_qbraid_batch_prediction(telemetry_data: list[Dict]) -> list[int]:
    """
    Run quantum predictions for multiple data points
    
    Args:
        telemetry_data: List of dicts with 'temp', 'humidity', 'wind' keys
    
    Returns:
        List of predicted AQI values
    """
    predictions = []
    for data in telemetry_data:
        aqi = run_qbraid_prediction(
            temp=data.get('temp', 25.0),
            humidity=data.get('humidity', 50.0),
            wind=data.get('wind', 20.0)
        )
        predictions.append(aqi)
    return predictions


def check_qbraid_connection() -> Dict[str, Any]:
    """
    Check qBraid connection and available devices
    
    Returns:
        Dict with connection status and available devices
    """
    if not QBRAD_AVAILABLE:
        return {
            "connected": False,
            "error": "qBraid packages not installed",
            "devices": []
        }
    
    if not QBRAID_API_KEY:
        return {
            "connected": False,
            "error": "QBRAID_API_KEY not configured",
            "devices": []
        }
    
    try:
        provider = QuantumProvider()
        devices = provider.get_devices()
        return {
            "connected": True,
            "error": None,
            "devices": [str(d) for d in devices]
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "devices": []
        }


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("VayuGuard Quantum Integration Test")
    print("=" * 60)
    
    # Check connection
    status = check_qbraid_connection()
    print(f"\nqBraid Connection Status: {'✓ Connected' if status['connected'] else '✗ Disconnected'}")
    if status['error']:
        print(f"Error: {status['error']}")
    if status['devices']:
        print(f"Available devices: {', '.join(status['devices'][:5])}")
    
    # Test prediction
    if status['connected']:
        print("\n" + "-" * 60)
        print("Testing Quantum Prediction:")
        print("-" * 60)
        
        test_cases = [
            {"temp": 28.0, "humidity": 98.0, "wind": 18.0},
            {"temp": 35.0, "humidity": 45.0, "wind": 25.0},
            {"temp": 20.0, "humidity": 80.0, "wind": 10.0},
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest {i}: Temp={test['temp']}°C, Humidity={test['humidity']}%, Wind={test['wind']}km/h")
            try:
                aqi = run_qbraid_prediction(
                    temp=test['temp'],
                    humidity=test['humidity'],
                    wind=test['wind'],
                    use_simulator=True
                )
                print(f"  → Quantum Predicted AQI: {aqi}")
            except Exception as e:
                print(f"  → Error: {e}")
    else:
        print("\n⚠️  Cannot run predictions - qBraid not connected")
        print("Please ensure:")
        print("  1. QBRAID_API_KEY is set in .env file")
        print("  2. qbraid package is installed: pip install qbraid")
        print("  3. You have an active qBraid account")