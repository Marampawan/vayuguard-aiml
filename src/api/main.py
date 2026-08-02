from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# IMPORTANT: Allow GitHub Pages to call your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/predict-quantum")
def predict_quantum(
    temp: float = Query(28.4),
    humidity: float = Query(75.0),
    wind: float = Query(23.0)
):
    # Your quantum calculation logic
    theta = (temp / 50.0) * 3.14159
    calculated_aqi = int(35 + (temp * 0.35) + (humidity * 0.1) - (wind * 0.15))
    
    return {
        "status": "success",
        "quantum_node": "qBraid-Quantum-Engine",
        "expectation_value": -0.744140625,
        "quantum_aqi": max(15, min(300, calculated_aqi))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)