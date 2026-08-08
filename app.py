from flask import Flask, request, jsonify
from flask_cors import CORS
from quantum_engine import run_quantum_aqi_job

app = Flask(__name__)

# 1. Position CORS middleware globally at the top of the app stack
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "Accept"],
    methods=["GET", "POST", "OPTIONS"]
)

# 2. Intercept preflight OPTIONS requests explicitly across all endpoints
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        headers = response.headers
        headers['Access-Control-Allow-Origin'] = '*'
        headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
        return response, 200

# 3. Route handlers with full HTTP method support
@app.route('/api/quantum-predict', methods=['POST', 'GET', 'OPTIONS'])
@app.route('/predict-quantum', methods=['POST', 'GET', 'OPTIONS'])
@app.route('/quantum-predict', methods=['POST', 'GET', 'OPTIONS'])
def quantum_predict():
    try:
        if request.method == 'GET':
            temp = float(request.args.get('temp', 28.4))
            wind = float(request.args.get('wind', 23.0))
            humidity = float(request.args.get('humidity', 75.0))
            pm25 = float(request.args.get('pm25', 25.0))
        else:
            data = request.json or {}
            temp = float(data.get('temp', 28.4))
            wind = float(data.get('wind', 23.0))
            humidity = float(data.get('humidity', 75.0))
            pm25 = float(data.get('pm25', 25.0))

        prediction = run_quantum_aqi_job(temp, wind, humidity, pm25)
        return jsonify(prediction), 200

    except Exception as e:
        # Fallback payload to ensure valid JSON response
        return jsonify({"status": "error", "message": str(e), "aqi": 42}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

