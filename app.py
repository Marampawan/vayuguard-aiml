from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from quantum_engine import run_quantum_aqi_job

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin requests for all routes

@app.route('/api/quantum-predict', methods=['POST'])
def quantum_predict():
    try:
        data = request.json or {}
        temp = float(data.get('temp', 28.0))
        wind = float(data.get('wind', 21.0))
        humidity = float(data.get('humidity', 54.0))
        pm25 = float(data.get('pm25', 25.0))

        prediction = run_quantum_aqi_job(temp, wind, humidity, pm25)
        return jsonify(prediction), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT', 5000)))

