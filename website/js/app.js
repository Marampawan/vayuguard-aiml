// === VayuGuard Professional Application Logic ===

// If you want to connect to your live Render backend, change this to 'https://vayuguard-ml.onrender.com'
const API_BASE = 'https://vayuguard-aiml.onrender.com';

let familyMembers = [
    { id: 1, name: 'Me', conditions: ['worker'] }
];

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initPeopleManager();
    initDoctors();
    checkApiHealth();
});

// --- Navigation & UI ---
function initNavigation() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // Smooth scroll
    document.querySelectorAll('.nav-menu a').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            target?.scrollIntoView({ behavior: 'smooth' });
            document.querySelectorAll('.nav-menu a').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// --- People Manager ---
function initPeopleManager() {
    renderPeople();
}

function renderPeople() {
    const container = document.getElementById('peopleChips');
    if (!container) return;
    container.innerHTML = familyMembers.map(p => `
        <div class="chip active" onclick="removePerson(${p.id})" title="Click to remove">
            <span>${p.name}</span>
            <i class="fas fa-times" style="margin-left: 5px;"></i>
        </div>
    `).join('');
}

function addPerson() {
    const name = prompt('Enter family member name:');
    if (!name) return;
    
    const conditions = [];
    if (confirm('Does this person have asthma?')) conditions.push('asthma');
    if (confirm('Is this person elderly (60+)?')) conditions.push('elderly');
    if (confirm('Is this person a child?')) conditions.push('child');
    if (confirm('Does this person work outdoors?')) conditions.push('worker');
    
    familyMembers.push({
        id: Date.now(),
        name: name,
        conditions: conditions.length ? conditions : ['none']
    });
    
    renderPeople();
    showToast(`${name} added to profile.`);
}

function removePerson(id) {
    familyMembers = familyMembers.filter(p => p.id !== id);
    renderPeople();
}

// --- Forecast & ML API Logic ---
async function checkApiHealth() {
    try {
        await fetch(`${API_BASE}/health`);
    } catch (e) {
        console.warn("API is not running. Start it with: python src/api/main.py");
    }
}

async function getForecast() {
    const city = document.getElementById('citySelect')?.value || 'Delhi';
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    
    if (!resultsDiv || !loadingDiv) return;

    resultsDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');

    try {
        // Dynamic city data
        let currentData = {};
        const currentHour = new Date().getHours();
        
        if (city === 'Delhi') {
            currentData = { aqi: 185, aqi_lag_1h: 180, aqi_lag_24h: 190, aqi_roll_mean_24h: 182, aqi_roll_mean_168h: 178, hour: currentHour, humidity: 45, wind_speed: 4, temperature: 32 };
        } else if (city === 'Mumbai') {
            currentData = { aqi: 142, aqi_lag_1h: 140, aqi_lag_24h: 145, aqi_roll_mean_24h: 140, aqi_roll_mean_168h: 135, hour: currentHour, humidity: 78, wind_speed: 8, temperature: 29 };
        } else if (city === 'Bangalore') {
            currentData = { aqi: 98, aqi_lag_1h: 95, aqi_lag_24h: 100, aqi_roll_mean_24h: 96, aqi_roll_mean_168h: 90, hour: currentHour, humidity: 62, wind_speed: 12, temperature: 24 };
        }

        const requestBody = {
            city: city,
            station_id: `station_${city.toLowerCase()}`,
            current_data: currentData,
            horizons: [24, 48, 72],
            model_type: "quantum_hybrid"
        };

        const response = await fetch(`${API_BASE}/forecast`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        // Render Forecast Cards
        const grid = document.getElementById('forecastGrid');
        if (grid) {
            grid.innerHTML = data.forecasts.map(f => {
                const cat = f.category.toLowerCase().replace(' ', '-');
                let color = 'var(--success)';
                let bg = 'rgba(34, 197, 94, 0.15)';
                if (cat.includes('moderate')) { color = 'var(--warning)'; bg = 'rgba(245, 158, 11, 0.15)'; }
                if (cat.includes('poor')) { color = 'var(--danger)'; bg = 'rgba(239, 68, 68, 0.15)'; }
                if (cat.includes('severe')) { color = 'var(--quantum)'; bg = 'rgba(168, 85, 247, 0.15)'; }

                return `
                <div style="background: var(--dark-2); border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid ${color}; transition: transform 0.3s;">
                    <div style="color: var(--gray-light); margin-bottom: 0.5rem; font-size: 0.9rem; font-weight: 600;">+${f.horizon_hours} Hours</div>
                    <div style="font-size: 3rem; font-weight: 800; color: var(--white); margin-bottom: 0.5rem; line-height: 1;">${f.predicted_aqi.toFixed(1)}</div>
                    <span style="display: inline-block; padding: 0.35rem 1.25rem; border-radius: 50px; font-size: 0.85rem; font-weight: 600; background: ${bg}; color: ${color}; margin-top: 0.5rem;">${f.category}</span>
                </div>`;
            }).join('');
        }

        // Render Health Alerts
        const alertsBox = document.getElementById('alertsBox');
        if (alertsBox) {
            let alertsHTML = '<h3 style="color: var(--white); margin-bottom: 1.5rem; width: 100%; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">Personalized Health Risk</h3>';
            
            for (const person of familyMembers) {
                const riskResponse = await fetch(`${API_BASE}/health-risk`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        forecast_aqi: data.forecasts[0].predicted_aqi,
                        user_profile: {
                            has_asthma: person.conditions.includes('asthma'),
                            elderly: person.conditions.includes('elderly'),
                            has_children: person.conditions.includes('child'),
                            outdoor_worker: person.conditions.includes('worker')
                        }
                    })
                });
                const riskData = await riskResponse.json();
                
                let riskColor = 'var(--success)';
                if(riskData.risk_level === 2) riskColor = 'var(--warning)';
                if(riskData.risk_level >= 3) riskColor = 'var(--danger)';
                if(riskData.risk_level === 5) riskColor = 'var(--quantum)';

                let riskBg = riskColor.replace('var(--', 'rgba(').replace(')', ', 0.15)');

                alertsHTML += `
                <div style="background: var(--dark-2); padding: 1.5rem; border-radius: 12px; border-left: 4px solid ${riskColor}; margin-bottom: 1rem; box-shadow: var(--shadow-md);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1rem; align-items: center;">
                        <strong style="color: var(--white); font-size: 1.1rem;"><i class="fas fa-user" style="color: var(--gray-light); margin-right: 0.5rem;"></i> ${person.name}</strong>
                        <span style="background: ${riskBg}; color: ${riskColor}; padding: 0.25rem 1rem; border-radius: 50px; font-weight: 600; font-size: 0.85rem;">${riskData.risk_category}</span>
                    </div>
                    <p style="color: var(--gray-light); font-size: 0.95rem; margin-bottom: 1rem; line-height: 1.5;">${riskData.advisory}</p>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                        ${riskData.precautions.map(p => `<span style="background: rgba(255,255,255,0.05); color: var(--light); padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.8rem; border: 1px solid rgba(255,255,255,0.1);"><i class="fas fa-shield-alt" style="margin-right: 0.25rem; color: ${riskColor};"></i>${p}</span>`).join('')}
                    </div>
                </div>`;
            }
            alertsBox.innerHTML = alertsHTML;
        }
        
        loadingDiv.classList.add('hidden');
        resultsDiv.classList.remove('hidden');
        showToast(`Quantum Forecast Successfully Generated for ${city}!`);

    } catch (error) {
        console.error("Error fetching forecast:", error);
        if (loadingDiv) {
            loadingDiv.innerHTML = `<p style="color: var(--danger); font-weight: 600;"><i class="fas fa-exclamation-triangle"></i> Failed to connect to Python API. Ensure backend is running.</p>`;
        }
    }
}

// --- Doctors Network ---
const doctorsList = [
    { id: 1, name: 'Dr. Rajesh Sharma', specialty: 'pulmonologist', hospital: 'AIIMS Delhi', experience: '15 years', rating: 4.9, available: 'Today' },
    { id: 2, name: 'Dr. Priya Patel', specialty: 'allergist', hospital: 'Fortis Mumbai', experience: '12 years', rating: 4.8, available: 'Tomorrow' },
    { id: 3, name: 'Dr. Anand Kumar', specialty: 'pediatric', hospital: 'Apollo Bangalore', experience: '10 years', rating: 4.7, available: 'Today' },
    { id: 4, name: 'Dr. Sunita Reddy', specialty: 'general', hospital: 'Max Healthcare', experience: '8 years', rating: 4.6, available: 'Today' }
];

function initDoctors() {
    renderDoctors('all');
    const select = document.getElementById('docSelect');
    if (select) {
        select.innerHTML = '<option value="">Choose a specialist...</option>' + 
            doctorsList.map(d => `<option value="${d.id}">${d.name} - ${d.specialty}</option>`).join('');
    }
}

function renderDoctors(filter) {
    const container = document.getElementById('doctorList');
    if (!container) return;
    const filtered = filter === 'all' ? doctorsList : doctorsList.filter(d => d.specialty === filter);
    
    container.innerHTML = filtered.map(doc => `
        <div style="background: var(--dark-2); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.05); transition: transform 0.2s;">
            <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
                <div style="width: 50px; height: 50px; border-radius: 50%; background: var(--primary); display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 1.2rem;">${doc.name.split(' ')[1].charAt(0)}</div>
                <div>
                    <h4 style="color: var(--white); margin-bottom: 0.2rem; font-size: 1.1rem;">${doc.name}</h4>
                    <span style="color: var(--gray-light); font-size: 0.85rem;">${doc.hospital}</span>
                </div>
            </div>
            <span style="display: inline-block; background: rgba(79, 70, 229, 0.15); color: var(--primary-light); padding: 0.25rem 0.75rem; border-radius: 50px; font-size: 0.8rem; font-weight: 600; margin-bottom: 1rem; text-transform: capitalize;">${doc.specialty}</span>
            <p style="color: var(--gray-light); font-size: 0.9rem; margin-bottom: 1.5rem;"><i class="fas fa-briefcase" style="width: 20px; color: var(--primary-light);"></i> Exp: ${doc.experience}<br><i class="fas fa-calendar" style="width: 20px; margin-top: 0.5rem; color: var(--primary-light);"></i> Avail: ${doc.available}</p>
            <button class="btn btn-primary" style="width: 100%; justify-content: center; padding: 0.75rem;" onclick="selectDoctor(${doc.id})">Book Appointment</button>
        </div>
    `).join('');
}

function filterDoctors(specialty) {
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    if(event && event.target) event.target.classList.add('active');
    renderDoctors(specialty);
}

function selectDoctor(id) {
    const select = document.getElementById('docSelect');
    if (select) select.value = id;
    showToast('Doctor selected. Complete the form to book.');
}

function bookDoctor(event) {
    event.preventDefault();
    showToast("Appointment request sent successfully!");
    event.target.reset();
}

// --- Breathing Exercises ---
let breathingInterval;

function startBoxBreathing() {
    clearInterval(breathingInterval);
    const text = document.getElementById('boxText');
    const circle = document.getElementById('boxCircle');
    const steps = [document.getElementById('step1'), document.getElementById('step2'), document.getElementById('step3'), document.getElementById('step4')];
    if(!text || !circle) return;

    let phase = 0;
    circle.style.transition = "transform 4s linear";

    function doPhase() {
        if (phase === 0) {
            text.textContent = 'Inhale'; circle.style.transform = 'scale(1.5)';
            steps.forEach((s, i) => s?.classList.toggle('active', i === 0));
            breathingInterval = setTimeout(() => { phase=1; doPhase(); }, 4000);
        } else if (phase === 1) {
            text.textContent = 'Hold';
            steps.forEach((s, i) => s?.classList.toggle('active', i === 1));
            breathingInterval = setTimeout(() => { phase=2; doPhase(); }, 4000);
        } else if (phase === 2) {
            text.textContent = 'Exhale'; circle.style.transform = 'scale(1)';
            steps.forEach((s, i) => s?.classList.toggle('active', i === 2));
            breathingInterval = setTimeout(() => { phase=3; doPhase(); }, 4000);
        } else {
            text.textContent = 'Hold';
            steps.forEach((s, i) => s?.classList.toggle('active', i === 3));
            breathingInterval = setTimeout(() => { phase=0; doPhase(); }, 4000);
        }
    }
    doPhase();
}

function startRelaxBreathing() { showToast("4-7-8 Relaxation technique started."); }
function startCleanseBreathing() { showToast("Lung Cleansing technique started."); }

// --- UI Utilities ---
function updateSlider(val) {
    const label = document.getElementById('sliderVal');
    if(label) label.textContent = val;
}

function showToast(message) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toastMsg');
    if (!toast || !msgEl) return;
    
    msgEl.textContent = message;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}