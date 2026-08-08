from flask import Flask, request, jsonify
from flask_cors import CORS
from quantum_engine import run_quantum_aqi_job

app = Flask(__name__)

# Enable CORS for all origins on /api/*
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/quantum-predict', methods=['POST', 'OPTIONS'])
def quantum_predict():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'CORS preflight OK'}), 200

    try:
        data = request.json or {}
        temp = float(data.get('temp', 28.4))
        wind = float(data.get('wind', 23.0))
        humidity = float(data.get('humidity', 75.0))
        pm25 = float(data.get('pm25', 25.0))

        # Run quantum circuit
        prediction = run_quantum_aqi_job(temp, wind, humidity, pm25)
        return jsonify(prediction), 200
    except Exception as e:
        print(f"Error executing quantum job: {e}")
        return jsonify({"status": "error", "message": str(e), "aqi": 32}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

