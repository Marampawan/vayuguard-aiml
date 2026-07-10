from qbraid import QbraidProvider

MY_KEY = "qbr_835d0fbd72e64e47fb6f0d5b9947c030e595b5f114c35908a7950f83dad9dbcc"

try:
    provider = QbraidProvider(api_key=MY_KEY)
    devices = provider.get_devices()
    
    print("\n=== YOUR AVAILABLE QBRAID DEVICES ===")
    for d in devices:
        # Safely get status even if qBraid returns None
        status = getattr(d, 'status', 'UNKNOWN') 
        print(f"ID: {d.id} | Status: {status} | Qubits: {d.num_qubits}")
        
except Exception as e:
    print(f"Error connecting: {e}")