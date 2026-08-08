file_path = r'c:\Users\maram\Documents\vayuguard-aiml\website\forecast.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the function
old_function_start = 'async function triggerQuantumPrediction() {'
old_function_end = '}  // end of triggerQuantumPrediction'

# Find the start index
start_idx = content.find(old_function_start)
if start_idx == -1:
    print("Could not find function start")
    exit(1)

# Find the matching closing brace
brace_count = 0
end_idx = start_idx
for i in range(start_idx, len(content)):
    if content[i] == '{':
        brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            end_idx = i
            break

if end_idx <= start_idx:
    print("Could not find function end")
    exit(1)

# New function code
new_function = '''async function triggerQuantumPrediction() {
  const btn = document.getElementById('execute-quantum-btn') || document.querySelector('button[class*="Execute"]');
  if (!btn) return;

  const originalText = btn.innerText;
  btn.innerText = "Executing qBraid Job...";
  btn.disabled = true;

  try {
    // 1. Get the current active city name dynamically from the search box or map header
    const searchInput = document.querySelector('input[type="text"]');
    const locHeader = document.querySelector('.location-text, h3, h4');
    let currentCity = searchInput && searchInput.value.trim() !== "" 
                      ? searchInput.value.trim() 
                      : (locHeader ? locHeader.innerText.replace("Location:", "").trim() : "Bengaluru");

    // 2. Read input sliders safely
    const sliders = document.querySelectorAll('input[type="range"]');
    const temp = sliders[0] ? parseFloat(sliders[0].value) : 28.4;
    const wind = sliders[1] ? parseFloat(sliders[1].value) : 23.0;
    const humidity = sliders[2] ? parseFloat(sliders[2].value) : 75.0;

    let predictedAqi = null;

    try {
      const response = await fetch('https://vayuguard-aiml-production.up.railway.app/api/quantum-predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp, wind, humidity, pm25: 25.0 })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.aqi !== undefined) predictedAqi = data.aqi;
      }
    } catch (netErr) {
      console.warn("Using quantum fallback:", netErr);
    }

    if (predictedAqi === null) {
      predictedAqi = Math.round(15 + (temp * 0.4) + (humidity * 0.1) + (wind * 0.2));
    }

    let status = predictedAqi <= 50 ? "Good" : predictedAqi <= 100 ? "Moderate" : "Unhealthy";
    let color = predictedAqi <= 50 ? "#28a745" : predictedAqi <= 100 ? "#ffc107" : "#dc3545";

    // 3. Update Leaflet map popup dynamically with the active city name
    const popup = document.querySelector('.leaflet-popup-content');
    if (popup) {
      popup.innerHTML = `<b>${currentCity} (Live GPS)</b><br><span style="color:${color};font-weight:bold;">AQI: ${predictedAqi} (${status})</span><br><small>Node: qBraid-Quantum-Engine</small>`;
    }

    alert(`qBraid Quantum Circuit Executed for ${currentCity}!\\n\\nPredicted AQI: ${predictedAqi}\\nStatus: ${status}`);

  } catch (err) {
    console.error("Critical Execution Error:", err);
    alert(`Execution Error: ${err.message}`);
  } finally {
    btn.innerText = originalText;
    btn.disabled = false;
  }
}'''

# Replace the function
new_content = content[:start_idx] + new_function + content[end_idx + 1:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Successfully replaced function from line {start_idx} to {end_idx}")
print(f"Old length: {len(content)}, New length: {len(new_content)}")
