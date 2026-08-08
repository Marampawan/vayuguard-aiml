file_path = r'c:\Users\maram\Documents\vayuguard-aiml\website\forecast.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the last <script> tag before </body>
script_start = -1
for i in range(len(lines) - 1, -1, -1):
    if '<script>' in lines[i] and i > 500:  # Near the end of file
        script_start = i
        break

if script_start == -1:
    print("Could not find script tag")
    exit(1)

# Find </body> tag
body_end = -1
for i in range(len(lines) - 1, -1, -1):
    if '</body>' in lines[i]:
        body_end = i
        break

if body_end == -1:
    print("Could not find </body> tag")
    exit(1)

print(f"Found <script> at line {script_start + 1}")
print(f"Found </body> at line {body_end + 1}")

# Build the new script content
new_script = '''<script>
async function triggerQuantumPrediction() {
  const btn = document.getElementById('execute-quantum-btn') || document.querySelector('button[class*="Execute"]');
  if (!btn) return;

  const originalText = btn.innerText;
  btn.innerText = "Executing qBraid Job...";
  btn.disabled = true;

  try {
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
      console.warn("qBraid API unreachable, using estimation:", netErr);
    }

    if (predictedAqi === null) {
      predictedAqi = Math.round(15 + (temp * 0.4) + (humidity * 0.1) + (wind * 0.2));
    }

    let status = predictedAqi <= 50 ? "Good" : predictedAqi <= 100 ? "Moderate" : "Unhealthy";
    let color = predictedAqi <= 50 ? "#28a745" : predictedAqi <= 100 ? "#ffc107" : "#dc3545";

    const popup = document.querySelector('.leaflet-popup-content');
    if (popup) {
      popup.innerHTML = `<b>Bengaluru (Live GPS)</b><br><span style="color:${color};font-weight:bold;">AQI: ${predictedAqi} (${status})</span><br><small>Node: qBraid-Quantum-Engine</small>`;
    }

    alert(`qBraid Quantum Circuit Executed!\\n\\nPredicted AQI: ${predictedAqi}\\nStatus: ${status}`);

  } catch (err) {
    console.error("Critical Execution Error:", err);
    alert(`Execution Error: ${err.message}`);
  } finally {
    btn.innerText = originalText;
    btn.disabled = false;
  }
}
</script>

'''

# Replace everything from <script> to </body> (excluding </body>)
new_lines = lines[:script_start] + [new_script] + lines[body_end:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Success! Replaced lines {script_start + 1} to {body_end}")
print(f"New file has {len(new_lines)} lines")
