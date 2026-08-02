# VayuGuard Quantum API Deployment Guide

This guide explains how to deploy the qBraid quantum prediction API and connect it to your GitHub Pages frontend.

## 🔒 Security First

**NEVER expose your qBraid API key in:**
- Client-side JavaScript
- Public repositories
- HTML files
- Chat messages or emails

The API key should ONLY exist in:
- Your local `.env` file (gitignored)
- Environment variables on your deployment platform

## 📁 Project Structure

```
vayuguard-aiml/
├── .env                          # Your API keys (gitignored, create locally)
├── .env.example                  # Template for environment variables
├── src/
│   ├── config.py                 # Secure config loader
│   ├── quantum_integration.py    # qBraid quantum circuit implementation
│   └── api/
│       ├── main.py               # Main ML API
│       └── quantum_predict.py    # Lightweight quantum prediction endpoint
├── requirements.txt              # Python dependencies
├── Procfile                      # Heroku/Render deployment
├── render.yaml                   # Render.com configuration
└── website/                      # GitHub Pages static files
    ├── forecast.html
    └── forecast-details.html
```

## 🚀 Deployment Options

### Option 1: Render.com (Recommended - Free Tier Available)

1. **Push your code to GitHub** (make sure `.env` is in `.gitignore`)

2. **Sign up at [Render.com](https://render.com)** and connect your GitHub account

3. **Create a new Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the branch to deploy

4. **Configure the service:**
   - **Name:** `vayuguard-quantum-api`
   - **Runtime:** Python 3.11
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.api.quantum_predict:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (or Starter for production)

5. **Add Environment Variables:**
   - Go to "Environment" tab
   - Add `QBRAID_API_KEY` with your actual API key value
   - Add `PYTHON_VERSION` = `3.11.0`

6. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment to complete (~2-3 minutes)
   - Your API will be available at: `https://vayuguard-quantum-api.onrender.com`

7. **Test the deployment:**
   ```bash
   curl https://vayuguard-quantum-api.onrender.com/health
   ```

### Option 2: Vercel

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Create `vercel.json` in project root:**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "src/api/quantum_predict.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "src/api/quantum_predict.py"
       }
     ],
     "env": {
       "QBRAID_API_KEY": "@qbraid_api_key"
     }
   }
   ```

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Set environment variable:**
   ```bash
   vercel env add QBRAID_API_KEY production
   ```

### Option 3: PythonAnywhere

1. **Sign up at [PythonAnywhere.com](https://www.pythonanywhere.com)**

2. **Upload your code** via Git or file upload

3. **Create a new Web App:**
   - Framework: Flask/FastAPI
   - Python version: 3.11

4. **Configure WSGI file** (`/var/www/yourusername_pythonanywhere_com_wsgi.py`):
   ```python
   import sys
   sys.path.insert(0, '/home/yourusername/vayuguard-aiml')
   
   from src.api.quantum_predict import app as application
   ```

5. **Set environment variables** in the "Web" tab:
   - `QBRAID_API_KEY` = your key

6. **Reload the web app**

## 🔗 Connect Frontend to Backend

### Update Frontend JavaScript

In `website/forecast-details.html`, update the `fetchDynamic7DayForecast` function to call your deployed API:

```javascript
// Replace the quantum bias calculation with API call
async function fetchDynamic7DayForecast(lat, lon, cityName) {
    // ... existing code ...
    
    // Fetch weather data from Open-Meteo
    const weatherRes = await fetch(`https://api.open-meteo.com/v1/forecast?...`);
    const weatherData = await weatherRes.json();
    
    for (let i = 0; i < 7; i++) {
        const temp = weatherData.daily?.temperature_2m_max?.[i] ?? 28;
        const humidity = weatherData.daily?.relative_humidity_2m_max?.[i] ?? 70;
        const wind = weatherData.daily?.wind_speed_10m_max?.[i] ?? 20;
        
        // Call your deployed quantum API
        try {
            const quantumRes = await fetch(
                `https://vayuguard-quantum-api.onrender.com/api/qbraid-predict?temp=${temp}&humidity=${humidity}&wind=${wind}`
            );
            const quantumData = await quantumRes.json();
            const quantumBias = quantumData.aqi - (45 + temp * 0.7 + humidity * 0.15 - wind * 0.3);
            
            // Apply quantum bias to AQI
            dayAqi = Math.max(10, dayAqi + quantumBias);
        } catch (err) {
            console.error('Quantum API error:', err);
            // Continue with classical prediction
        }
    }
}
```

**Important:** Replace `https://vayuguard-quantum-api.onrender.com` with your actual API URL.

## 🧪 Testing Locally

1. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

2. **Add your qBraid API key to `.env`:**
   ```
   QBRAID_API_KEY=your_actual_key_here
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the API locally:**
   ```bash
   python src/api/quantum_predict.py
   ```

5. **Test the endpoint:**
   ```bash
   curl "http://localhost:8000/api/qbraid-predict?temp=28.0&humidity=98.0&wind=18.0"
   ```

6. **View interactive docs:**
   - Open browser to `http://localhost:8000/docs`
   - Test the API directly from Swagger UI

## 📊 Monitoring & Logs

### Render.com
- View logs in the Render dashboard under "Logs" tab
- Monitor API usage and response times
- Set up alerts for downtime

### Health Checks
- `GET /health` - Basic health check
- `GET /quantum-status` - qBraid connection status
- Both endpoints return JSON with status information

## 🔧 Troubleshooting

### qBraid Connection Issues

1. **"QBRAID_API_KEY not configured"**
   - Ensure environment variable is set in deployment platform
   - Check that `.env` file exists locally

2. **"qBraid packages not installed"**
   - Run: `pip install qbraid qiskit qiskit-aer`

3. **"No qBraid backends available"**
   - Check your qBraid account status
   - Verify API key is valid
   - Ensure you have credits or free tier access

### CORS Errors

If frontend can't access API:
1. Check CORS configuration in `quantum_predict.py`
2. Add your GitHub Pages URL to `allow_origins`
3. Remove the wildcard `"*"` in production

### API Timeout

- Free tier platforms have cold starts (30+ seconds)
- Consider upgrading to paid tier for production
- Implement retry logic in frontend

## 🎯 Production Checklist

- [ ] Revoke any exposed API keys and generate new ones
- [ ] Set `QBRAID_API_KEY` in deployment platform environment variables
- [ ] Update CORS origins to your actual GitHub Pages URL
- [ ] Remove wildcard `"*"` from CORS configuration
- [ ] Enable HTTPS (automatic on Render/Vercel)
- [ ] Set up monitoring and alerts
- [ ] Test all endpoints before sharing URL
- [ ] Document your API URL for frontend integration

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check with qBraid status |
| `/quantum-status` | GET | Check qBraid device availability |
| `/api/qbraid-predict` | POST | Quantum AQI prediction |

### Example API Call

```bash
curl -X POST "https://your-api.onrender.com/api/qbraid-predict" \
  -H "Content-Type: application/json" \
  -d '{"temp": 28.0, "humidity": 98.0, "wind": 18.0}'
```

### Example Response

```json
{
  "aqi": 87,
  "status": "qBraid Job Complete",
  "device": "qbraid_qasm_simulator",
  "execution_time_ms": 1234.56
}
```

## 🔐 Security Best Practices

1. **Never commit `.env` file** - it's in `.gitignore`
2. **Rotate API keys regularly** - especially if exposed
3. **Use environment variables** - never hardcode secrets
4. **Enable HTTPS** - automatic on most platforms
5. **Monitor usage** - check qBraid dashboard for unusual activity
6. **Set spending limits** - in your qBraid account settings
7. **Use CORS properly** - specify exact origins in production

## 📖 Additional Resources

- [qBraid Documentation](https://docs.qbraid.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Render Documentation](https://render.com/docs)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)

## 🆘 Support

If you encounter issues:
1. Check the logs in your deployment platform
2. Verify qBraid API key is valid
3. Test locally first before deploying
4. Check CORS configuration
5. Ensure all dependencies are installed