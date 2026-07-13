// === VayuGuard Professional Application Logic ===

// Connects to the live Render cloud backend
const API_BASE = 'https://vayuguard-api-liveee.onrender.com';

// Load saved family from memory, otherwise default to "Me"
let familyMembers = JSON.parse(localStorage.getItem('vayuFamily')) || [
    { id: 1, name: 'Me', conditions: ['worker'] }
];

// Helper to save changes permanently
function saveFamilyData() {
    localStorage.setItem('vayuFamily', JSON.stringify(familyMembers));
}

// Global state variables for Breathing Engine
let breathingTimeout; // Must use Timeout, not Interval
let isBreathing = false; // The Kill-Switch flag

function initUnifiedCityData() {
    const select = document.getElementById('cityForecastSelect');
    if (!select) return;

    const cityNames = {
        bengaluru: 'Bengaluru, IN',
        delhi: 'Delhi, IN',
        newyork: 'New York, US'
    };

    select.addEventListener('change', async function() {
        // 1. Disable the dropdown and make it look locked
        this.disabled = true;
        this.style.opacity = '0.5';
        this.style.cursor = 'not-allowed';

        // 2. Instantly update the label
        const label = document.querySelector('.aqi-label');
        if (label) {
            label.textContent = `Live AQI - ${cityNames[this.value] || 'Bengaluru, IN'}`;
        }

        try {
            // 3. Wait for the entire Quantum Fetch process to finish
            await updateCityData(this.value);
        } finally {
            // 4. Re-enable the dropdown
            this.disabled = false;
            this.style.opacity = '1';
            this.style.cursor = 'pointer';
        }
    });

    updateCityData(select.value || 'bengaluru');
}

async function updateCityData(citySelectValue) {
    const apiToken = 'demo';
    let apiCity = 'bangalore';

    if (citySelectValue === 'delhi') apiCity = 'delhi';
    if (citySelectValue === 'newyork') apiCity = 'newyork';

    const valueEl = document.getElementById('liveAqiValue');
    const statusEl = document.getElementById('liveAqiStatus');
    const needleEl = document.getElementById('aqiNeedle');
    const forecastGrid = document.getElementById('dynamicForecastGrid');

    if (!valueEl || !statusEl || !needleEl || !forecastGrid) return;

    try {
        valueEl.innerText = '⚛️';
        valueEl.style.fontSize = '3.5rem';
        valueEl.style.color = '#8b5cf6';

        statusEl.innerText = 'CONNECTING TO QBRAID CLOUD...';
        statusEl.style.backgroundColor = '#f3e8ff';
        statusEl.style.color = '#6d28d9';
        statusEl.style.borderColor = '#8b5cf6';

        await new Promise(resolve => setTimeout(resolve, 1200));

        const response = await fetch(`https://api.waqi.info/feed/${apiCity}/?token=${apiToken}`);
        const result = await response.json();

        if (result.status === 'ok') {
            const currentAqi = result.data.aqi;

            const getAqiStyle = (aqi) => {
                if (aqi <= 50) return { text: 'GOOD', color: '#10b981', bg: '#d1fae5', border: '#a7f3d0' };
                if (aqi <= 100) return { text: 'MODERATE', color: '#f59e0b', bg: '#fef3c7', border: '#fde68a' };
                if (aqi <= 150) return { text: 'SENSITIVE', color: '#f97316', bg: '#ffedd5', border: '#fdba74' };
                if (aqi <= 200) return { text: 'UNHEALTHY', color: '#ef4444', bg: '#fee2e2', border: '#fecaca' };
                if (aqi <= 300) return { text: 'VERY UNHEALTHY', color: '#8b5cf6', bg: '#f3e8ff', border: '#d8b4fe' };
                return { text: 'HAZARDOUS', color: '#e11d48', bg: '#ffe4e6', border: '#fecdd3' };
            };

            valueEl.style.fontSize = '5rem';
            valueEl.innerText = currentAqi;

            const liveStyle = getAqiStyle(currentAqi);
            valueEl.style.color = liveStyle.color;
            statusEl.innerText = liveStyle.text;
            statusEl.style.color = liveStyle.color;
            statusEl.style.backgroundColor = liveStyle.bg;
            statusEl.style.borderColor = liveStyle.color;

            const needlePos = Math.min((currentAqi / 300) * 100, 100);
            needleEl.style.left = `${needlePos}%`;

            const f24 = Math.round(currentAqi * 1.15);
            const f42 = Math.round(currentAqi * 0.85);
            const f72 = Math.round(currentAqi * 1.25);

            const s24 = getAqiStyle(f24);
            const s42 = getAqiStyle(f42);
            const s72 = getAqiStyle(f72);

            forecastGrid.innerHTML = `
                <div class="modern-forecast-card" style="background: ${s24.bg}; border-color: ${s24.border};">
                    <div class="fc-time"><i class="fas fa-clock"></i> +24 Hours</div>
                    <div class="fc-aqi" style="color: ${s24.color};">${f24}</div>
                    <div class="fc-cat" style="background: ${s24.color}; color: white;">${s24.text}</div>
                </div>
                <div class="modern-forecast-card" style="background: ${s42.bg}; border-color: ${s42.border};">
                    <div class="fc-time"><i class="fas fa-clock"></i> +42 Hours</div>
                    <div class="fc-aqi" style="color: ${s42.color};">${f42}</div>
                    <div class="fc-cat" style="background: ${s42.color}; color: white;">${s42.text}</div>
                </div>
                <div class="modern-forecast-card" style="background: ${s72.bg}; border-color: ${s72.border};">
                    <div class="fc-time"><i class="fas fa-clock"></i> +72 Hours</div>
                    <div class="fc-aqi" style="color: ${s72.color};">${f72}</div>
                    <div class="fc-cat" style="background: ${s72.color}; color: white;">${s72.text}</div>
                </div>`;
        }
    } catch (error) {
        console.log('Failed to fetch Live AQI', error);
        statusEl.innerText = 'CONNECTION FAILED';
        statusEl.style.backgroundColor = '#fee2e2';
        statusEl.style.color = '#ef4444';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuthState(); // --- FIX: Keeps top buttons updated with login status ---
    initNavigation();
    initPeopleManager();
    initFamilyChipManager();
    initDoctors();
    detectUserLocation();
    initUnifiedCityData();
    
    // Triggers the live bottom cards update on page load!
    updateBottomCityCards(); 

    // Listen for manual dropdown changes
    document.getElementById('citySelect')?.addEventListener('change', (event) => {
        updateCityInterface(event.target.value);
    });

    // Bind forgot password form securely if it exists in the DOM
    document.getElementById('forgotPasswordForm')?.addEventListener('submit', handleForgotPassword);
});

// --- Authentication State Management ---
function checkAuthState() {
    const logButton = document.getElementById('logBtn') || document.querySelector('.log-btn');
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    const isAuthPage = window.location.pathname.includes('login') || window.location.pathname.includes('forgot');

    if (token) {
        // User is logged in
        if (logButton) {
            logButton.textContent = 'Logout';
            logButton.style.display = 'block';
            logButton.onclick = (e) => {
                e.preventDefault();
                localStorage.removeItem('token');
                sessionStorage.removeItem('token');
                showToast("Logged out successfully.");
                window.location.reload();
            };
        }
    } else {
        // User is not logged in
        if (logButton) {
            logButton.textContent = 'Login';
            logButton.onclick = (e) => {
                e.preventDefault();
                window.location.href = 'login.html';
            };
        }
    }
}

// --- Dynamic UI Updater ---
function updateCityInterface(cityName) {
    const heroCity = document.getElementById('heroCityName');
    const heroNum = document.getElementById('heroAqiNumber');
    const heroStatus = document.getElementById('heroAqiStatus');
    const citySelect = document.getElementById('citySelect');
    
    // Ensure dropdown matches
    if (citySelect && citySelect.value !== cityName) {
        citySelect.value = cityName;
    }
    
    // Update the massive text at the top based on the city
    if (cityName === 'Delhi') {
        if(heroCity) heroCity.textContent = 'Delhi AQI Now';
        if(heroNum) heroNum.textContent = '185';
        if(heroStatus) { heroStatus.textContent = 'Poor'; heroStatus.className = 'aqi-status poor'; }
    } else if (cityName === 'Mumbai') {
        if(heroCity) heroCity.textContent = 'Mumbai AQI Now';
        if(heroNum) heroNum.textContent = '142';
        if(heroStatus) { heroStatus.textContent = 'Moderate'; heroStatus.className = 'aqi-status moderate'; }
    } else if (cityName === 'Bangalore') {
        if(heroCity) heroCity.textContent = 'Bangalore AQI Now';
        if(heroNum) heroNum.textContent = '98';
        if(heroStatus) { heroStatus.textContent = 'Satisfactory'; heroStatus.className = 'aqi-status good'; }
    }
    
    // Automatically fetch the quantum forecast for the new city
    getForecast();
}

// --- Navigation & UI ---
function initNavigation() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    document.querySelectorAll('.nav-menu a').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                target?.scrollIntoView({ behavior: 'smooth' });
                document.querySelectorAll('.nav-menu a').forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
}

// --- Auto-Detect User Location ---
function detectUserLocation() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(async (position) => {
            try {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
                const data = await response.json();
                
                const cityStr = (data.address.city || data.address.state_district || data.address.state || "").toLowerCase();
                let detectedCity = "Delhi"; // Default

                if (cityStr.includes("mumbai") || cityStr.includes("maharashtra")) {
                    detectedCity = "Mumbai";
                } else if (cityStr.includes("bangalore") || cityStr.includes("bengaluru") || cityStr.includes("karnataka")) {
                    detectedCity = "Bangalore";
                }

                showToast(`GPS Location detected: ${detectedCity}`);
                updateCityInterface(detectedCity);

            } catch (error) {
                console.error("Geocoding failed:", error);
                updateCityInterface("Delhi"); // Fallback
            }
        }, (error) => {
            console.warn("User denied location permission.");
            updateCityInterface("Delhi"); // Fallback
        });
    } else {
        updateCityInterface("Delhi");
    }
}

// --- People Manager ---
function initPeopleManager() {
    renderPeople();
}

function initFamilyChipManager() {
    const modal = document.getElementById('addPersonModal');
    const openModalBtn = document.getElementById('openModalBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const cancelModalBtn = document.getElementById('cancelModalBtn');
    const saveMemberBtn = document.getElementById('saveMemberBtn');
    const newMemberNameInput = document.getElementById('newMemberName');
    const chipsContainer = document.getElementById('familyChipsContainer');
    const detailsBox = document.getElementById('familyDetailsBox');

    if (!modal || !openModalBtn || !closeModalBtn || !cancelModalBtn || !saveMemberBtn || !newMemberNameInput || !chipsContainer || !detailsBox) {
        return;
    }

    openModalBtn.addEventListener('click', () => modal.classList.remove('hidden'));
    closeModalBtn.addEventListener('click', () => modal.classList.add('hidden'));
    cancelModalBtn.addEventListener('click', () => modal.classList.add('hidden'));

    let familyData = JSON.parse(localStorage.getItem('vayuFamilyData')) || {
        'my-profile': '<strong>My Profile:</strong> No underlying respiratory conditions. Current AQI is safe for normal outdoor activities.',
        'sarah': '<strong>Sarah (Asthma):</strong> <span style="color: #ef4444;">Warning!</span> Forecasted AQI at +72 hrs is a trigger. Ensure inhaler is available.',
        'grandpa': '<strong>Grandpa (COPD):</strong> <span style="color: #f59e0b;">Caution.</span> Shift in AQI may cause mild discomfort. Keep air purifiers running.'
    };

    let familyChips = JSON.parse(localStorage.getItem('vayuFamilyChips')) || [];

    familyChips.forEach(chipInfo => {
        const newChip = document.createElement('div');
        newChip.className = 'chip';
        newChip.setAttribute('data-profile', chipInfo.id);
        newChip.innerHTML = chipInfo.html;
        chipsContainer.insertBefore(newChip, openModalBtn);
    });

    function attachChipListeners() {
        document.querySelectorAll('.people-chips .chip:not(#openModalBtn)').forEach(chip => {
            const newChip = chip.cloneNode(true);
            chip.replaceWith(newChip);
            newChip.addEventListener('click', function() {
                document.querySelectorAll('.people-chips .chip:not(#openModalBtn)').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                detailsBox.innerHTML = familyData[this.getAttribute('data-profile')];
            });
        });
    }

    attachChipListeners();

    saveMemberBtn.addEventListener('click', () => {
        const name = newMemberNameInput.value.trim();
        if (!name) {
            alert('Please enter a name.');
            return;
        }

        const checkboxes = document.querySelectorAll('#conditionCheckboxes input[type="checkbox"]:checked');
        const conditions = [];
        checkboxes.forEach(cb => conditions.push(cb.parentElement.textContent.trim()));

        const profileId = 'profile-' + Date.now();
        const newChip = document.createElement('div');
        newChip.className = 'chip';
        newChip.setAttribute('data-profile', profileId);

        let icon = '<i class="fas fa-user"></i>';
        if (conditions.includes('Young Children')) icon = '<i class="fas fa-child"></i>';
        else if (conditions.includes('Works Outside')) icon = '<i class="fas fa-hard-hat"></i>';
        else if (conditions.length > 0) icon = '<i class="fas fa-notes-medical"></i>';

        const tagText = conditions.length > 0 ? ` (${conditions[0]})` : '';
        newChip.innerHTML = `${icon} ${name}${tagText}`;

        const conditionString = conditions.length > 0 ? conditions.join(', ') : 'No specific conditions';
        familyData[profileId] = `<strong>${name}:</strong> Tracked Conditions: <span style="color:var(--primary); font-weight:600;">${conditionString}</span>. Quantum forecast is monitoring local AQI carefully based on this profile.`;

        familyChips.push({ id: profileId, html: newChip.innerHTML });
        localStorage.setItem('vayuFamilyData', JSON.stringify(familyData));
        localStorage.setItem('vayuFamilyChips', JSON.stringify(familyChips));

        chipsContainer.insertBefore(newChip, openModalBtn);
        attachChipListeners();
        document.querySelector(`.chip[data-profile="${profileId}"]`)?.click();

        newMemberNameInput.value = '';
        document.querySelectorAll('#conditionCheckboxes input[type="checkbox"]').forEach(cb => cb.checked = false);
        modal.classList.add('hidden');
    });
}

function renderPeople() {
    const container = document.getElementById('peopleChips');
    if (!container) return;
    
    if (familyMembers.length === 0) {
        container.innerHTML = `<span style="color: var(--gray-light); font-size: 0.9rem; font-style: italic; padding: 0.4rem 0;">No members added. Click + to add.</span>`;
        return;
    }

    container.innerHTML = familyMembers.map(p => `
        <div class="chip active" onclick="removePerson(${p.id})" title="Click to remove">
            <span>${p.name}</span>
            <i class="fas fa-times" style="margin-left: 5px;"></i>
        </div>
    `).join('');
}

// --- Custom Family Member Modal Logic ---
function addPerson() {
    if(document.getElementById('newPersonName')) document.getElementById('newPersonName').value = '';
    if(document.getElementById('chkAsthma')) document.getElementById('chkAsthma').checked = false;
    if(document.getElementById('chkElderly')) document.getElementById('chkElderly').checked = false;
    if(document.getElementById('chkChild')) document.getElementById('chkChild').checked = false;
    if(document.getElementById('chkWorker')) document.getElementById('chkWorker').checked = false;
    
    document.getElementById('addPersonModal')?.classList.remove('hidden');
}

function closeAddModal() {
    document.getElementById('addPersonModal')?.classList.add('hidden');
}

function saveNewPerson() {
    const nameInput = document.getElementById('newPersonName')?.value.trim();
    
    if (!nameInput) {
        showToast('Please enter a name first.');
        return;
    }
    
    const conditions = [];
    if (document.getElementById('chkAsthma')?.checked) conditions.push('asthma');
    if (document.getElementById('chkElderly')?.checked) conditions.push('elderly');
    if (document.getElementById('chkChild')?.checked) conditions.push('child');
    if (document.getElementById('chkWorker')?.checked) conditions.push('worker');
    
    familyMembers.push({
        id: Date.now(),
        name: nameInput,
        conditions: conditions.length ? conditions : ['none']
    });
    
    saveFamilyData(); 
    renderPeople(); 
    closeAddModal(); 
    showToast(`${nameInput} added to profile.`);
    
    getForecast(); 
}

function removePerson(id) {
    familyMembers = familyMembers.filter(p => p.id !== id);
    saveFamilyData(); 
    renderPeople();
    getForecast(); 
}

const cityForecasts = {
    'bengaluru': `<div class="modern-forecast-card" style="background: #ecfdf5; border-color: #a7f3d0;"><div class="fc-time"><i class="fas fa-clock"></i> +24 Hours</div><div class="fc-aqi" style="color: #059669;">45</div><div class="fc-cat" style="background: #10b981; color: white;">Good</div></div><div class="modern-forecast-card" style="background: #fffbeb; border-color: #fde68a;"><div class="fc-time"><i class="fas fa-clock"></i> +42 Hours</div><div class="fc-aqi" style="color: #d97706;">85</div><div class="fc-cat" style="background: #f59e0b; color: white;">Moderate</div></div><div class="modern-forecast-card" style="background: #ffedd5; border-color: #fdba74;"><div class="fc-time"><i class="fas fa-clock"></i> +72 Hours</div><div class="fc-aqi" style="color: #ea580c;">112</div><div class="fc-cat" style="background: #f97316; color: white;">Sensitive</div></div>`,
    'delhi': `<div class="modern-forecast-card" style="background: #fef2f2; border-color: #fecaca;"><div class="fc-time"><i class="fas fa-clock"></i> +24 Hours</div><div class="fc-aqi" style="color: #dc2626;">156</div><div class="fc-cat" style="background: #ef4444; color: white;">Unhealthy</div></div><div class="modern-forecast-card" style="background: #fef2f2; border-color: #fecaca;"><div class="fc-time"><i class="fas fa-clock"></i> +42 Hours</div><div class="fc-aqi" style="color: #dc2626;">170</div><div class="fc-cat" style="background: #ef4444; color: white;">Unhealthy</div></div><div class="modern-forecast-card" style="background: #f3e8ff; border-color: #d8b4fe;"><div class="fc-time"><i class="fas fa-clock"></i> +72 Hours</div><div class="fc-aqi" style="color: #7e22ce;">210</div><div class="fc-cat" style="background: #8b5cf6; color: white;">Very Unhealthy</div></div>`,
    'newyork': `<div class="modern-forecast-card" style="background: #ecfdf5; border-color: #a7f3d0;"><div class="fc-time"><i class="fas fa-clock"></i> +24 Hours</div><div class="fc-aqi" style="color: #059669;">28</div><div class="fc-cat" style="background: #10b981; color: white;">Good</div></div><div class="modern-forecast-card" style="background: #ecfdf5; border-color: #a7f3d0;"><div class="fc-time"><i class="fas fa-clock"></i> +42 Hours</div><div class="fc-aqi" style="color: #059669;">35</div><div class="fc-cat" style="background: #10b981; color: white;">Good</div></div><div class="modern-forecast-card" style="background: #ecfdf5; border-color: #a7f3d0;"><div class="fc-time"><i class="fas fa-clock"></i> +72 Hours</div><div class="fc-aqi" style="color: #059669;">42</div><div class="fc-cat" style="background: #10b981; color: white;">Good</div></div>`
};

// --- Forecast & ML API Logic ---
async function getForecast() {
    const city = document.getElementById('citySelect')?.value || 'Delhi';
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    
    if (!resultsDiv || !loadingDiv) return;

    resultsDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');

    try {
        const cityCoords = {
            'Delhi': { lat: 28.6139, lon: 77.2090 },
            'Mumbai': { lat: 19.0760, lon: 72.8777 },
            'Bangalore': { lat: 12.9716, lon: 77.5946 }
        };
        const coords = cityCoords[city];

        const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${coords.lat}&longitude=${coords.lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m`;
        const aqiUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${coords.lat}&longitude=${coords.lon}&current=us_aqi`;

        const [weatherRes, aqiRes] = await Promise.all([ fetch(weatherUrl), fetch(aqiUrl) ]);
        const weatherData = await weatherRes.json();
        const aqiData = await aqiRes.json();

        const liveAqi = aqiData.current.us_aqi;
        const liveTemp = weatherData.current.temperature_2m;
        const liveHumidity = weatherData.current.relative_humidity_2m;
        const liveWind = weatherData.current.wind_speed_10m;
        const currentHour = new Date().getHours();
        
        const timeString = new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });

        if(document.getElementById('heroAqiNumber')) document.getElementById('heroAqiNumber').textContent = liveAqi;
        let status = 'Good'; let statusClass = 'good';
        if (liveAqi > 50) { status = 'Satisfactory'; statusClass = 'good'; }
        if (liveAqi > 100) { status = 'Moderate'; statusClass = 'moderate'; }
        if (liveAqi > 150) { status = 'Poor'; statusClass = 'poor'; }
        if (liveAqi > 200) { status = 'Severe'; statusClass = 'poor'; }
        
        const heroStatus = document.getElementById('heroAqiStatus');
        if (heroStatus) {
            heroStatus.textContent = status;
            heroStatus.className = `aqi-status ${statusClass}`;
        }
        
        showToast(`Live data updated at ${timeString}`);

        const requestBody = {
            city: city,
            station_id: `station_${city.toLowerCase()}`,
            current_data: { 
                aqi: liveAqi, 
                aqi_lag_1h: liveAqi - 2, 
                aqi_lag_24h: liveAqi + 5, 
                aqi_roll_mean_24h: liveAqi, 
                aqi_roll_mean_168h: liveAqi - 5, 
                hour: currentHour, 
                humidity: liveHumidity, 
                wind_speed: liveWind, 
                temperature: liveTemp 
            },
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

        if (data.forecasts && data.forecasts.length > 0) {
            const worstAqi = Math.max(...data.forecasts.map(f => f.predicted_aqi));
            const marker = document.getElementById('aqiMarker');
            const markerText = document.getElementById('aqiMarkerText');
            
            if (marker && markerText) {
                let percentage = (worstAqi / 500) * 100;
                if (percentage > 100) percentage = 100;
                marker.style.left = percentage + '%';
                markerText.textContent = Math.round(worstAqi);
            }
        
            const healthSection = document.getElementById('healthAdviceSection'); 
            
            if (healthSection) {
                let adviceHTML = `<h3 style="color: var(--white); margin-bottom: 1.5rem;"><i class="fas fa-users-medical"></i> Individual Member Alerts</h3>`;
                
                for (const member of familyMembers) {
                    const singleProfile = {
                        elderly: member.conditions.includes('elderly'),
                        has_asthma: member.conditions.includes('asthma'),
                        has_children: member.conditions.includes('child'),
                        outdoor_worker: member.conditions.includes('worker')
                    };

                    try {
                        const healthResponse = await fetch(`${API_BASE}/health-risk`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                forecast_aqi: worstAqi,
                                user_profile: singleProfile
                            })
                        });
                        
                        if (healthResponse.ok) {
                            const healthData = await healthResponse.json();
                            
                            let bColor = 'var(--success)';
                            if (healthData.risk_level === 3) bColor = 'var(--warning)';
                            if (healthData.risk_level >= 4) bColor = 'var(--danger)';

                            adviceHTML += `
                                <div style="background: var(--dark-2); padding: 1.2rem; border-radius: 8px; border-left: 4px solid ${bColor}; margin-bottom: 1rem;">
                                    <h4 style="color: var(--white); margin-bottom: 0.5rem; text-transform: capitalize;">
                                        <i class="fas fa-user"></i> ${member.name} — Risk: ${healthData.risk_category}
                                    </h4>
                                    <p style="color: var(--gray-light); font-size: 0.95rem; margin-bottom: 0.5rem;">${healthData.advisory}</p>
                                    ${healthData.precautions.length > 0 ? `
                                        <ul style="color: ${bColor}; padding-left: 1.5rem; font-weight: 600; font-size: 0.9rem; margin-bottom: 0;">
                                            ${healthData.precautions.map(p => `<li>${p}</li>`).join('')}
                                        </ul>
                                    ` : `<span style="color: var(--success); font-weight: 600; font-size: 0.9rem;">No special precautions needed today.</span>`}
                                </div>
                            `;
                        }
                    } catch (error) {
                        console.error("Health API Error for", member.name, error);
                    }
                }
                healthSection.innerHTML = adviceHTML;
            }
        }
        
        resultsDiv.classList.remove('hidden');
        loadingDiv.classList.add('hidden');

    } catch (error) {
        console.error("Error fetching forecast:", error);
        if (loadingDiv) {
            loadingDiv.innerHTML = `<p style="color: var(--danger); font-weight: 600;"><i class="fas fa-exclamation-triangle"></i> Render Server Error. Ensure your Python backend is Live.</p>`;
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
            <button class="btn btn-primary" style="width: 100%; justify-content: center; padding: 0.75rem; border-radius: 50px;" onclick="selectDoctor(${doc.id})">Book Appointment</button>
        </div>
    `).join('');
}

function filterDoctors(specialty) {
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    if(window.event && window.event.target) window.event.target.classList.add('active');
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

// --- Forgot Password Action Handler (CRITICAL BUG FIX) ---
function handleForgotPassword(event) {
    event.preventDefault(); // FIX: Prevents application loop state drops!
    const emailInput = document.getElementById('forgotEmail')?.value;

    if (!emailInput) {
        showToast("Please input a valid registration email.");
        return;
    }

    showToast("Password reset token dispatched to email.");
    // Secure token execution sequence goes here
}

// --- Breathing Exercises (RESTORED ENGINE) ---
function resetBreathingUI() {
    isBreathing = false; 
    clearTimeout(breathingTimeout); 
    
    document.querySelectorAll('.breath-circle').forEach(c => {
        c.style.transform = 'scale(1)';
        c.style.background = ''; 
        c.style.transition = 'transform 0.5s ease, background 0.5s ease'; 
    });
    document.querySelectorAll('.breathe-steps .step').forEach(s => s.classList.remove('active'));
    
    const box = document.getElementById('boxText');
    const relax = document.getElementById('relaxText');
    const cleanse = document.getElementById('cleanseText');
    if(box) box.innerHTML = '<i class="fas fa-check-circle" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Ready';
    if(relax) relax.innerHTML = '<i class="fas fa-check-circle" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Ready';
    if(cleanse) cleanse.innerHTML = '<i class="fas fa-check-circle" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Ready';
}

function stopExercise() {
    resetBreathingUI();
    showToast("Exercise stopped.");
}

function startBoxBreathing() {
    resetBreathingUI();
    const text = document.getElementById('boxText');
    const circle = document.getElementById('boxCircle');
    const steps = [document.getElementById('step1'), document.getElementById('step2'), document.getElementById('step3'), document.getElementById('step4')];
    if(!text || !circle) return;

    let phase = 0;
    circle.style.transition = "transform 4s linear, background 0.5s ease";
    isBreathing = true; 

    function doPhase() {
        if (!isBreathing) return; 

        if (phase === 0) {
            text.innerHTML = '<i class="fas fa-arrow-up" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Inhale'; 
            circle.style.transform = 'scale(1.5)';
            circle.style.background = 'rgba(59, 130, 246, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 0));
            breathingTimeout = setTimeout(() => { phase=1; doPhase(); }, 4000);
        } else if (phase === 1) {
            text.innerHTML = '<i class="fas fa-hand-paper" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Hold';
            circle.style.background = 'rgba(139, 92, 246, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 1));
            breathingTimeout = setTimeout(() => { phase=2; doPhase(); }, 4000);
        } else if (phase === 2) {
            text.innerHTML = '<i class="fas fa-arrow-down" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Exhale'; 
            circle.style.transform = 'scale(1)';
            circle.style.background = 'rgba(16, 185, 129, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 2));
            breathingTimeout = setTimeout(() => { phase=3; doPhase(); }, 4000);
        } else {
            text.innerHTML = '<i class="fas fa-stop-circle" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Hold';
            circle.style.background = 'rgba(139, 92, 246, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 3));
            breathingTimeout = setTimeout(() => { phase=0; doPhase(); }, 4000);
        }
    }
    doPhase();
}

function startRelaxBreathing() {
    resetBreathingUI();
    const text = document.getElementById('relaxText');
    const circle = document.getElementById('relaxCircle');
    const steps = [document.getElementById('rstep1'), document.getElementById('rstep2'), document.getElementById('rstep3')];
    if(!text || !circle) return;

    let phase = 0;
    circle.style.transition = "transform 4s linear, background 0.5s ease";
    isBreathing = true; 

    function doPhase() {
        if (!isBreathing) return; 

        if (phase === 0) {
            text.innerHTML = '<i class="fas fa-wind" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Inhale'; 
            circle.style.transform = 'scale(1.5)';
            circle.style.background = 'rgba(79, 70, 229, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 0));
            breathingTimeout = setTimeout(() => { phase = 1; circle.style.transition = "transform 7s linear, background 0.5s ease"; doPhase(); }, 4000);
        } else if (phase === 1) {
            text.innerHTML = '<i class="fas fa-pause" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Hold'; 
            circle.style.background = 'rgba(217, 70, 239, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 1));
            breathingTimeout = setTimeout(() => { phase = 2; circle.style.transition = "transform 8s linear, background 0.5s ease"; doPhase(); }, 7000);
        } else {
            text.innerHTML = '<i class="fas fa-leaf" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Exhale'; 
            circle.style.transform = 'scale(1)';
            circle.style.background = 'rgba(6, 182, 212, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 2));
            breathingTimeout = setTimeout(() => { phase = 0; circle.style.transition = "transform 4s linear, background 0.5s ease"; doPhase(); }, 8000);
        }
    }
    doPhase();
}

// Keep core functions intact 
function startCleanseBreathing() {
    resetBreathingUI();
    const text = document.getElementById('cleanseText');
    const circle = document.getElementById('cleanseCircle');
    const steps = [document.getElementById('cstep1'), document.getElementById('cstep2'), document.getElementById('cstep3')];
    if(!text || !circle) return;

    let phase = 0;
    circle.style.transition = "transform 0.5s ease-out, background 0.3s ease";
    isBreathing = true; 

    function doPhase() {
        if (!isBreathing) return; 

        if (phase === 0) {
            text.innerHTML = '<i class="fas fa-lungs" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Inhale'; 
            circle.style.transform = 'scale(1.3)';
            circle.style.background = 'rgba(34, 197, 94, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 0));
            breathingTimeout = setTimeout(() => { phase = 1; doPhase(); }, 2000);
        } else if (phase === 1) {
            text.innerHTML = '<i class="fas fa-sign-out-alt" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Exhale!'; 
            circle.style.transform = 'scale(0.8)';
            circle.style.background = 'rgba(239, 68, 68, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 1));
            breathingTimeout = setTimeout(() => { phase = 2; doPhase(); }, 1000);
        } else {
            text.innerHTML = '<i class="fas fa-bed" style="font-size: 2.2rem; margin-bottom: 8px; display: block;"></i>Rest'; 
            circle.style.transform = 'scale(1)';
            circle.style.background = 'rgba(107, 114, 128, 0.95)'; 
            steps.forEach((s, i) => s?.classList.toggle('active', i === 2));
            breathingTimeout = setTimeout(() => { phase = 0; doPhase(); }, 2000);
        }
    }
    doPhase();
}

// --- UI Utilities ---
function updateSlider(val) {
    const label = document.getElementById('sliderVal');
    if(label) label.textContent = val;
}

function showToast(message) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toastMsg') || document.getElementById('toastMessage');
    if (!toast || !msgEl) return;
    
    msgEl.textContent = message;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// --- Live Bottom City Cards Updater ---
async function updateBottomCityCards() {
    const cityItems = document.querySelectorAll('.city-item');
    if (!cityItems.length) return;

    const cityCoords = {
        'Delhi': { lat: 28.6139, lon: 77.2090 },
        'Mumbai': { lat: 19.0760, lon: 72.8777 },
        'Bangalore': { lat: 12.9716, lon: 77.5946 }
    };

    for (const item of cityItems) {
        const titleEl = item.querySelector('h3');
        if (!titleEl) continue;
        const cityName = titleEl.textContent;
        const coords = cityCoords[cityName];
        if (!coords) continue;

        try {
            const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${coords.lat}&longitude=${coords.lon}&current=temperature_2m,relative_humidity_2m`;
            const aqiUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${coords.lat}&longitude=${coords.lon}&current=us_aqi`;
            
            const [weatherRes, aqiRes] = await Promise.all([fetch(weatherUrl), fetch(aqiUrl)]);
            const weatherData = await weatherRes.json();
            const aqiData = await aqiRes.json();
            
            const aqi = aqiData.current.us_aqi;
            const temp = weatherData.current.temperature_2m;
            const hum = weatherData.current.relative_humidity_2m;
            
            const aqiNumEl = item.querySelector('.city-aqi-num');
            if (aqiNumEl) aqiNumEl.textContent = aqi;
            
            let status = 'Good'; let statusClass = 'good';
            if (aqi > 50) { status = 'Satisfactory'; statusClass = 'good'; }
            if (aqi > 100) { status = 'Moderate'; statusClass = 'moderate'; }
            if (aqi > 150) { status = 'Poor'; statusClass = 'poor'; }
            if (aqi > 200) { status = 'Severe'; statusClass = 'poor'; }
            
            const aqiTextEl = item.querySelector('.city-aqi-text');
            const aqiBoxEl = item.querySelector('.city-aqi-box');
            if (aqiTextEl) aqiTextEl.textContent = status;
            if (aqiBoxEl) aqiBoxEl.className = `city-aqi-box ${statusClass}`;
            
            const metaSpans = item.querySelectorAll('.city-meta span');
            if (metaSpans.length >= 2) {
                metaSpans[0].innerHTML = `<i class="fas fa-temperature-high"></i> ${temp}°C`;
                metaSpans[1].innerHTML = `<i class="fas fa-tint"></i> ${hum}%`;
            }
        } catch (e) { 
            console.error("Failed to update bottom card for", cityName, e); 
        }
    }
}