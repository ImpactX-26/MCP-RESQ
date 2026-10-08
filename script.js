const API_BASE_URL = "http://127.0.0.1:8000";

const state = {
    backendConnected: false,
    emergency: null,
    userLocation: null,
    tracking: null,
    units: [],
    nearby: [],
    currentFilter: "all",
    mapScale: 1
};

const pageData = {
    home: ["Emergency Assistance", "Get help quickly and track your response."],
    emergency: ["Report Emergency", "Tell us what happened and request assistance."],
    tracking: ["Track Response", "See where help is coming from and how far away it is."],
    nearby: ["Nearby Help", "Find hospitals, fire stations, police and rescue services."],
    assistant: ["AI Assistant", "Ask questions about your emergency and response."],
    control: ["Control Center", "Operational information for emergency coordinators."],
    resources: ["Emergency Resources", "Monitor and coordinate response units."],
    mcp: ["MCP Services", "Connect AI reasoning with emergency resources."],
    verification: ["Verification", "Validate emergency and response information."],
    system: ["System Status", "Monitor MCP-ResQ technical services."]
};

const demoUnits = [
    {
        id: "AMB-101",
        name: "Ambulance A-12",
        type: "ambulance",
        status: "available",
        location: "City Hospital Road",
        distance_km: 2.4,
        eta_minutes: 7
    },
    {
        id: "AMB-102",
        name: "Ambulance A-15",
        type: "ambulance",
        status: "available",
        location: "MG Road",
        distance_km: 4.1,
        eta_minutes: 12
    },
    {
        id: "FIRE-201",
        name: "Fire Unit F-04",
        type: "fire",
        status: "available",
        location: "Yelahanka Fire Station",
        distance_km: 3.1,
        eta_minutes: 9
    },
    {
        id: "FIRE-202",
        name: "Fire Unit F-08",
        type: "fire",
        status: "busy",
        location: "Hebbal",
        distance_km: 6.4,
        eta_minutes: 18
    },
    {
        id: "RES-301",
        name: "Rescue Team R-02",
        type: "rescue",
        status: "available",
        location: "Central Rescue Base",
        distance_km: 1.8,
        eta_minutes: 5
    }
];

const demoNearby = [
    {
        id: "H-101",
        name: "City Emergency Hospital",
        type: "hospital",
        distance_km: 3.2,
        eta_minutes: 8,
        status: "Emergency Available",
        address: "Central Bengaluru",
        phone: "Emergency Desk"
    },
    {
        id: "H-102",
        name: "Metro Care Hospital",
        type: "hospital",
        distance_km: 4.5,
        eta_minutes: 12,
        status: "Emergency Available",
        address: "North Bengaluru",
        phone: "Emergency Desk"
    },
    {
        id: "F-101",
        name: "Yelahanka Fire Station",
        type: "fire",
        distance_km: 3.1,
        eta_minutes: 9,
        status: "Operational",
        address: "Yelahanka",
        phone: "Fire Department"
    },
    {
        id: "P-101",
        name: "Central Police Station",
        type: "police",
        distance_km: 2.7,
        eta_minutes: 7,
        status: "Operational",
        address: "Central Bengaluru",
        phone: "Police"
    },
    {
        id: "R-101",
        name: "City Rescue Base",
        type: "rescue",
        distance_km: 1.8,
        eta_minutes: 5,
        status: "Available",
        address: "Central Bengaluru",
        phone: "Rescue Team"
    }
];

async function apiRequest(endpoint, options = {}) {
    const controller = new AbortController();

    const timeout = setTimeout(() => {
        controller.abort();
    }, 10000);

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            signal: controller.signal,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        });

        clearTimeout(timeout);

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const contentType = response.headers.get("content-type");

        if (contentType && contentType.includes("application/json")) {
            return await response.json();
        }

        return await response.text();

    } catch (error) {
        clearTimeout(timeout);
        throw error;
    }
}

async function checkBackend() {
    try {
        await apiRequest("/api/health");

        state.backendConnected = true;

        updateConnectionUI();
        addMCPLog("FastAPI backend connected", true);

    } catch (error) {
        state.backendConnected = false;

        updateConnectionUI();
        addMCPLog("Backend unavailable - demo mode active", false);
    }
}

function updateConnectionUI() {
    const dot = document.getElementById("connectionDot");
    const text = document.getElementById("connectionText");
    const backendStatus = document.getElementById("backendStatus");

    if (state.backendConnected) {
        dot.style.background = "#16a34a";
        text.textContent = "Backend connected";

        if (backendStatus) {
            backendStatus.textContent = "ONLINE";
        }
    } else {
        dot.style.background = "#f59e0b";
        text.textContent = "Demo mode";

        if (backendStatus) {
            backendStatus.textContent = "OFFLINE";
        }
    }
}

async function getUnits() {
    try {
        const data = await apiRequest("/api/units");

        state.units = Array.isArray(data) ? data : data.units || [];

        return state.units;

    } catch (error) {
        state.units = [...demoUnits];
        return state.units;
    }
}

async function getNearbyHelp() {
    try {
        const data = await apiRequest("/api/nearby-help");

        state.nearby = Array.isArray(data) ? data : data.results || [];

        return state.nearby;

    } catch (error) {
        state.nearby = [...demoNearby];
        return state.nearby;
    }
}

async function createEmergency(emergencyData) {
    return await apiRequest("/api/emergencies", {
        method: "POST",
        body: JSON.stringify(emergencyData)
    });
}

async function getEmergency(emergencyId) {
    return await apiRequest(`/api/emergencies/${emergencyId}`);
}

async function getTracking(emergencyId) {
    return await apiRequest(`/api/emergencies/${emergencyId}/tracking`);
}

async function dispatchUnit(unitId, emergencyId) {
    return await apiRequest(`/api/units/${unitId}/dispatch`, {
        method: "POST",
        body: JSON.stringify({
            emergency_id: emergencyId
        })
    });
}

async function verifyEmergency(emergencyData) {
    return await apiRequest("/api/verify", {
        method: "POST",
        body: JSON.stringify(emergencyData)
    });
}

async function coordinateResponse(emergencyId) {
    return await apiRequest("/api/coordinate", {
        method: "POST",
        body: JSON.stringify({
            emergency_id: emergencyId
        })
    });
}

async function sendChatMessage(message) {
    return await apiRequest("/api/chat", {
        method: "POST",
        body: JSON.stringify({
            message,
            emergency_id: state.emergency?.id || null
        })
    });
}

async function testMCPService(service) {
    return await apiRequest(`/api/mcp/${service}/test`);
}

function classifyEmergency(text) {
    const value = text.toLowerCase();

    if (
        value.includes("gas") ||
        value.includes("leak") ||
        value.includes("chemical") ||
        value.includes("toxic") ||
        value.includes("hazard") ||
        value.includes("propane")
    ) {
        return "gas";
    }

    if (
        value.includes("fire") ||
        value.includes("burning") ||
        value.includes("smoke") ||
        value.includes("flame")
    ) {
        return "fire";
    }

    if (
        value.includes("accident") ||
        value.includes("crash") ||
        value.includes("collision")
    ) {
        return "accident";
    }

    if (
        value.includes("ambulance") ||
        value.includes("injured") ||
        value.includes("medical") ||
        value.includes("unconscious") ||
        value.includes("bleed") ||
        value.includes("chok")
    ) {
        return "medical";
    }

    if (
        value.includes("trapped") ||
        value.includes("rescue") ||
        value.includes("stuck")
    ) {
        return "rescue";
    }

    if (
        value.includes("flood") ||
        value.includes("earthquake") ||
        value.includes("disaster")
    ) {
        return "disaster";
    }

    return "other";
}

function getEmergencyIcon(type) {
    const icons = {
        medical: "🚑",
        fire: "🔥",
        accident: "🚗",
        rescue: "🛟",
        disaster: "🌊",
        other: "⚠️"
    };

    return icons[type] || "🚨";
}

function getEmergencyName(type) {
    const names = {
        medical: "Medical Emergency",
        fire: "Fire Emergency",
        accident: "Road Accident",
        rescue: "Rescue Emergency",
        disaster: "Natural Disaster",
        other: "Emergency"
    };

    return names[type] || "Emergency";
}

function getPriority(type) {
    if (["medical", "fire", "accident", "rescue"].includes(type)) {
        return "HIGH";
    }

    return "MEDIUM";
}

async function detectEmergency() {
    const description = document.getElementById("emergencyDescription").value.trim();

    if (!description) {
        showNotification("Please describe what happened.");
        return;
    }

    const type = classifyEmergency(description);

    const emergencyData = {
        description,
        type,
        priority: getPriority(type),
        location: state.userLocation,
        source: "web"
    };

    updateEmergencyAnalysis(type, emergencyData);

    addActivity("Emergency description received");

    try {
        const response = await createEmergency(emergencyData);

        state.emergency = response.emergency || response;

        updateEmergencyFromBackend(state.emergency);

        addActivity("Emergency created by backend");
        addMCPLog("Emergency sent to FastAPI", true);

    } catch (error) {
        state.emergency = {
            id: `DEMO-${Date.now()}`,
            ...emergencyData,
            status: "detected"
        };

        addActivity("Demo emergency created");
        addMCPLog("Backend unavailable - demo emergency created", false);
    }

    document.getElementById("emergencyStatus").textContent = "DETECTED";

    showNotification("Emergency detected successfully.");

    await loadTracking();

    showPage("tracking");
}

function updateEmergencyAnalysis(type, data) {
    document.getElementById("detectedType").textContent = getEmergencyName(type);
    document.getElementById("detectedPriority").textContent = data.priority;
    document.getElementById("detectedLocation").textContent =
        data.location?.address || "Location pending";

    document.getElementById("emergencyStatus").textContent = "ANALYZING";
}

function updateEmergencyFromBackend(emergency) {
    if (!emergency) {
        return;
    }

    document.getElementById("emergencyId").textContent =
        emergency.id || "--";

    document.getElementById("detectedType").textContent =
        getEmergencyName(emergency.type);

    document.getElementById("detectedPriority").textContent =
        emergency.priority || "HIGH";

    document.getElementById("controlEmergencyId").textContent =
        emergency.id || "--";

    document.getElementById("controlEmergencyType").textContent =
        getEmergencyName(emergency.type);

    document.getElementById("controlEmergencyPriority").textContent =
        emergency.priority || "--";

    document.getElementById("controlEmergencyStatus").textContent =
        emergency.status || "DETECTED";

    document.getElementById("responseIcon").textContent =
        getEmergencyIcon(emergency.type);

    document.getElementById("responseName").textContent =
        getEmergencyName(emergency.type);
}

// --- LIVE TRACKING & GOOGLE MAPS ANIMATION ENGINE ---
const trackingAnim = {
    timer: null,
    isPlaying: true,
    speed: 1,
    progress: 20,
    initialDistance: 3.5,
    initialEta: 8,
    unitName: "Ambulance A-12",
    unitType: "ambulance",
    gmapsApiKey: "",
    gmap: null,
    gmapResponderMarker: null,
    gmapVictimMarker: null,
    gmapPolyline: null,
    responderCoords: { lat: 13.0827, lng: 77.5877 },
    victimCoords: { lat: 12.9716, lng: 77.5946 }
};

function initMapTrackingControls() {
    const toggleBtn = document.getElementById("toggleAnim");
    const speedBtn = document.getElementById("speedAnim");
    const resetBtn = document.getElementById("resetAnim");
    const gmapsBtn = document.getElementById("gmapsToggleBtn");
    const hazardBtn = document.getElementById("toggleHazardBtn");
    const responseMap = document.getElementById("responseMap");
    const unitBar = document.getElementById("unitSelectorBar");

    if (toggleBtn) {
        toggleBtn.onclick = () => {
            trackingAnim.isPlaying = !trackingAnim.isPlaying;
            toggleBtn.textContent = trackingAnim.isPlaying ? "⏸️" : "▶️";
            toggleBtn.classList.toggle("active", !trackingAnim.isPlaying);
            showNotification(trackingAnim.isPlaying ? "Response movement resumed." : "Response movement paused.");
        };
    }

    if (speedBtn) {
        speedBtn.onclick = () => {
            if (trackingAnim.speed === 1) trackingAnim.speed = 2;
            else if (trackingAnim.speed === 2) trackingAnim.speed = 5;
            else trackingAnim.speed = 1;
            speedBtn.textContent = `${trackingAnim.speed}x`;
            showNotification(`Tracking animation speed set to ${trackingAnim.speed}x`);
        };
    }

    if (hazardBtn) {
        hazardBtn.onclick = () => {
            const overlay = document.getElementById("hazardZoneOverlay");
            if (overlay) {
                const isHidden = overlay.style.display === "none";
                overlay.style.display = isHidden ? "block" : "none";
                hazardBtn.classList.toggle("layer-active", isHidden);
                showNotification(isHidden ? "⚠️ Hazard perimeter risk radius visible." : "Hazard overlay hidden.");
            }
        };
    }

    if (resetBtn) {
        resetBtn.onclick = () => {
            trackingAnim.progress = 0;
            trackingAnim.isPlaying = true;
            if (toggleBtn) {
                toggleBtn.textContent = "⏸️";
                toggleBtn.classList.remove("active");
            }
            const statusBadge = document.getElementById("responseStatus");
            if (statusBadge) {
                statusBadge.textContent = "EN ROUTE";
                statusBadge.className = "status-badge responding";
            }
            startVehicleTrackingAnimation();
            showNotification("Reset vehicle route animation to 0%.");
        };
    }

    if (gmapsBtn) {
        gmapsBtn.onclick = () => {
            promptGoogleMapsApiKey();
        };
    }

    // --- Interactive Unit Selector Chips ---
    if (unitBar) {
        const chips = unitBar.querySelectorAll(".unit-chip");
        chips.forEach(chip => {
            chip.onclick = (e) => {
                chips.forEach(c => c.classList.remove("active"));
                chip.classList.add("active");

                const unitName = chip.getAttribute("data-name");
                const unitType = chip.getAttribute("data-type");
                const dist = Number(chip.getAttribute("data-dist")) || 3.0;
                const eta = Number(chip.getAttribute("data-eta")) || 7;

                trackingAnim.unitName = unitName;
                trackingAnim.unitType = unitType;
                trackingAnim.initialDistance = dist;
                trackingAnim.initialEta = eta;
                trackingAnim.progress = 0;
                trackingAnim.isPlaying = true;

                const vehicleIconEl = document.getElementById("vehicleIcon");
                const vehicleLabelEl = document.getElementById("vehicleLabel");
                const popTitle = document.getElementById("popoverTitle");
                const popEquip = document.getElementById("popoverEquipment");

                if (vehicleIconEl) vehicleIconEl.textContent = getVehicleIcon(unitType);
                if (vehicleLabelEl) vehicleLabelEl.textContent = unitName;
                if (popTitle) popTitle.textContent = unitName;
                if (popEquip) {
                    if (unitType === "fire") popEquip.textContent = "Water Cannon • Thermal Camera • Ladders";
                    else if (unitType === "rescue") popEquip.textContent = "Jaws of Life • Search Drone • Rope Rescue";
                    else if (unitType === "police") popEquip.textContent = "Patrol Cruiser • Traffic Control • SWAT";
                    else popEquip.textContent = "Defibrillator • Oxygen • Ventilator";
                }

                document.getElementById("responseName").textContent = unitName;
                document.getElementById("responseIcon").textContent = getVehicleIcon(unitType);

                const statusBadge = document.getElementById("responseStatus");
                if (statusBadge) {
                    statusBadge.textContent = "EN ROUTE";
                    statusBadge.className = "status-badge responding";
                }

                startVehicleTrackingAnimation();
                showNotification(`Dispatched & tracking ${unitName}`);
            };
        });
    }

    // --- Interactive Click Map to Set Victim Coordinates ---
    if (responseMap) {
        responseMap.onclick = (e) => {
            // Ignore if clicked directly on marker popover or controls
            if (e.target.closest(".map-controls") || e.target.closest(".marker-popover")) return;

            const rect = responseMap.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;

            const pctX = Math.round(Math.max(10, Math.min(90, (clickX / rect.width) * 100)));
            const pctY = Math.round(Math.max(10, Math.min(90, (clickY / rect.height) * 100)));

            // Relocate Victim Marker
            const userMarker = document.getElementById("userMarker");
            const hazardOverlay = document.getElementById("hazardZoneOverlay");

            if (userMarker) {
                userMarker.style.left = `${pctX}%`;
                userMarker.style.top = `${pctY}%`;
            }

            if (hazardOverlay) {
                hazardOverlay.style.left = `${pctX}%`;
                hazardOverlay.style.top = `${pctY}%`;
            }

            // Update SVG Route Path
            const routePath = document.getElementById("routePath");
            if (routePath) {
                const midX = (20 + pctX) / 2;
                const midY = (25 + pctY) / 2;
                routePath.setAttribute("d", `M 20 25 Q ${midX} ${midY} ${pctX} ${pctY}`);
            }

            // Update state
            trackingAnim.victimPos = { x: pctX, y: pctY };
            trackingAnim.progress = 0;

            document.getElementById("locationText").textContent = `Sector (${pctX}°, ${pctY}°)`;
            document.getElementById("detectedLocation").textContent = `Map Point (${pctX}%, ${pctY}%)`;

            startVehicleTrackingAnimation();
            showNotification(`📍 Relocated emergency victim marker to Sector (${pctX}%, ${pctY}%). Vehicle rerouted.`);
        };
    }

    // --- Marker Tooltip Popovers ---
    const vehicleMarker = document.getElementById("responseMarker");
    const hospitalMarker = document.getElementById("hospitalMarker");
    const vehiclePopover = document.getElementById("vehiclePopover");
    const hospitalPopover = document.getElementById("hospitalPopover");

    if (vehicleMarker && vehiclePopover) {
        vehicleMarker.onclick = (e) => {
            e.stopPropagation();
            const isVis = vehiclePopover.style.display === "block";
            vehiclePopover.style.display = isVis ? "none" : "block";
        };
    }

    if (hospitalMarker && hospitalPopover) {
        hospitalMarker.onclick = (e) => {
            e.stopPropagation();
            const isVis = hospitalPopover.style.display === "block";
            hospitalPopover.style.display = isVis ? "none" : "block";
        };
    }
}

function promptGoogleMapsApiKey() {
    const key = prompt("Enter your Google Maps JavaScript API Key:\n(Leave empty to use simulated interactive Google Map view)", trackingAnim.gmapsApiKey);
    if (key !== null) {
        trackingAnim.gmapsApiKey = key.trim();
        if (trackingAnim.gmapsApiKey) {
            loadGoogleMapsScript(trackingAnim.gmapsApiKey);
        } else {
            showNotification("Switched to Simulated Interactive Map.");
            const gCanvas = document.getElementById("googleMapCanvas");
            const simLayer = document.getElementById("mapSimulationLayer");
            if (gCanvas) gCanvas.style.display = "none";
            if (simLayer) simLayer.style.display = "block";
        }
    }
}

function loadGoogleMapsScript(apiKey) {
    if (window.google && window.google.maps) {
        initGoogleMapInstance();
        return;
    }

    showNotification("Loading Google Maps JS API...");
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=onGoogleMapsLoaded`;
    script.async = true;
    script.defer = true;
    script.onerror = () => {
        showNotification("Could not load Google Maps API. Using Simulated Interactive Map.", "error");
    };
    document.head.appendChild(script);
}

window.onGoogleMapsLoaded = function() {
    showNotification("Google Maps API loaded successfully!");
    initGoogleMapInstance();
};

function initGoogleMapInstance() {
    const container = document.getElementById("googleMapCanvas");
    const simLayer = document.getElementById("mapSimulationLayer");
    if (!container) return;

    container.style.display = "block";
    if (simLayer) simLayer.style.display = "none";

    const victimLatLng = trackingAnim.victimCoords;
    const responderLatLng = trackingAnim.responderCoords;

    trackingAnim.gmap = new google.maps.Map(container, {
        zoom: 13,
        center: {
            lat: (victimLatLng.lat + responderLatLng.lat) / 2,
            lng: (victimLatLng.lng + responderLatLng.lng) / 2
        },
        styles: [
            { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
            { featureType: "road", elementType: "geometry", stylers: [{ color: "#38414e" }] },
            { featureType: "water", elementType: "geometry", stylers: [{ color: "#17263c" }] }
        ]
    });

    trackingAnim.gmapVictimMarker = new google.maps.Marker({
        position: victimLatLng,
        map: trackingAnim.gmap,
        title: "Victim Location",
        label: "📍"
    });

    trackingAnim.gmapResponderMarker = new google.maps.Marker({
        position: responderLatLng,
        map: trackingAnim.gmap,
        title: trackingAnim.unitName,
        label: getVehicleIcon(trackingAnim.unitType)
    });

    trackingAnim.gmapPolyline = new google.maps.Polyline({
        path: [responderLatLng, victimLatLng],
        geodesic: true,
        strokeColor: "#E53935",
        strokeOpacity: 0.9,
        strokeWeight: 4,
        map: trackingAnim.gmap
    });
}

function getVehicleIcon(type) {
    if (type === "fire") return "🚒";
    if (type === "gas" || type === "hazmat" || type === "chemical") return "☣️";
    if (type === "rescue") return "🛟";
    if (type === "police") return "🚔";
    return "🚑";
}

function startVehicleTrackingAnimation() {
    if (trackingAnim.timer) {
        clearInterval(trackingAnim.timer);
    }

    trackingAnim.timer = setInterval(() => {
        if (!trackingAnim.isPlaying) return;

        if (trackingAnim.progress < 100) {
            trackingAnim.progress += 0.4 * trackingAnim.speed;
        }

        if (trackingAnim.progress >= 100) {
            trackingAnim.progress = 100;
            const statusBadge = document.getElementById("responseStatus");
            if (statusBadge) {
                statusBadge.textContent = "ARRIVED";
                statusBadge.className = "status-badge safe";
            }
            showNotification(`🚨 ${trackingAnim.unitName} has arrived at your location!`);
            clearInterval(trackingAnim.timer);
        }

        const p = trackingAnim.progress / 100;

        // Quadratic Bezier interpolation matching SVG M 20 25 Q 45 40 70 70
        const p0 = { x: 20, y: 25 };
        const p1 = { x: 45, y: 40 };
        const p2 = { x: 70, y: 70 };

        const currentX = (1-p)*(1-p)*p0.x + 2*(1-p)*p*p1.x + p*p*p2.x;
        const currentY = (1-p)*(1-p)*p0.y + 2*(1-p)*p*p1.y + p*p*p2.y;

        const resMarker = document.getElementById("responseMarker");
        if (resMarker) {
            resMarker.style.left = `${currentX}%`;
            resMarker.style.top = `${currentY}%`;
        }

        const remainingDist = Math.max(0, trackingAnim.initialDistance * (1 - p)).toFixed(1);
        const remainingEta = Math.max(0, Math.ceil(trackingAnim.initialEta * (1 - p)));

        document.getElementById("responseDistance").textContent = trackingAnim.progress >= 100 ? "0.0 km (Arrived)" : `${remainingDist} km`;
        document.getElementById("responseEta").textContent = trackingAnim.progress >= 100 ? "0 min (Arrived)" : `${remainingEta} min`;
        document.getElementById("responseProgress").style.width = `${Math.floor(trackingAnim.progress)}%`;
        document.getElementById("responseProgressText").textContent = `${Math.floor(trackingAnim.progress)}%`;
        
        document.getElementById("mapStatus").textContent = trackingAnim.progress >= 100
            ? `${trackingAnim.unitName} has arrived`
            : `${trackingAnim.unitName} is ${remainingDist} km away • ETA ${remainingEta} min`;

        // Update Google Maps marker position if active
        if (trackingAnim.gmap && trackingAnim.gmapResponderMarker) {
            const startLat = trackingAnim.responderCoords.lat;
            const startLng = trackingAnim.responderCoords.lng;
            const endLat = trackingAnim.victimCoords.lat;
            const endLng = trackingAnim.victimCoords.lng;

            const curLat = startLat + (endLat - startLat) * p;
            const curLng = startLng + (endLng - startLng) * p;

            trackingAnim.gmapResponderMarker.setPosition({ lat: curLat, lng: curLng });
        }
    }, 250);
}

async function loadTracking() {
    if (!state.emergency?.id) {
        return;
    }

    try {
        const response = await getTracking(state.emergency.id);

        state.tracking = response.tracking || response;

        updateTrackingUI(state.tracking);

        addMCPLog("Tracking information updated", true);

    } catch (error) {
        const unit = findBestDemoUnit(state.emergency.type);

        state.tracking = {
            unit_name: unit.name,
            unit_type: unit.type,
            distance_km: unit.distance_km,
            eta_minutes: unit.eta_minutes,
            status: "en_route",
            progress: 20,
            from: unit.location,
            destination: "Your location",
            updated_at: new Date().toISOString()
        };

        updateTrackingUI(state.tracking);

        addMCPLog("Demo tracking data displayed", false);
    }
}

function findBestDemoUnit(type) {
    if (type === "fire") {
        return demoUnits.find(unit => unit.type === "fire");
    }

    if (type === "rescue") {
        return demoUnits.find(unit => unit.type === "rescue");
    }

    return demoUnits.find(unit => unit.type === "ambulance");
}

function updateTrackingUI(tracking) {
    if (!tracking) {
        return;
    }

    trackingAnim.unitName = tracking.unit_name || tracking.name || "Emergency Response";
    trackingAnim.unitType = tracking.unit_type || state.emergency?.type || "ambulance";
    trackingAnim.initialDistance = Number(tracking.distance_km) || 3.5;
    trackingAnim.initialEta = Number(tracking.eta_minutes) || 8;
    trackingAnim.progress = Number(tracking.progress || 20);

    const vehicleIconEl = document.getElementById("vehicleIcon");
    const vehicleLabelEl = document.getElementById("vehicleLabel");
    if (vehicleIconEl) vehicleIconEl.textContent = getVehicleIcon(trackingAnim.unitType);
    if (vehicleLabelEl) vehicleLabelEl.textContent = trackingAnim.unitName;

    document.getElementById("responseName").textContent = trackingAnim.unitName;
    document.getElementById("responseIcon").textContent = getVehicleIcon(trackingAnim.unitType);

    document.getElementById("responseFrom").textContent =
        tracking.from || tracking.location || "Responder location";

    document.getElementById("responseDestination").textContent =
        tracking.destination || "Your location";

    document.getElementById("responseStatus").textContent =
        formatStatus(tracking.status || "en_route");

    document.getElementById("trackingUpdated").textContent =
        formatTime(tracking.updated_at);

    // Initialize animation controls and start vehicle movement toward victim
    initMapTrackingControls();
    startVehicleTrackingAnimation();
}

async function loadNearby() {
    const data = await getNearbyHelp();

    renderNearby(data);
}

function renderNearby(data) {
    const container = document.getElementById("nearbyList");

    const filtered =
        state.currentFilter === "all"
            ? data
            : data.filter(item => item.type === state.currentFilter);

    if (!filtered.length) {
        container.innerHTML = `
            <div class="card" style="padding:25px">
                <p>No nearby services found.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(item => `
        <div class="nearby-card">
            <div class="nearby-icon">${getNearbyIcon(item.type)}</div>

            <div class="nearby-info">
                <h3>${escapeHTML(item.name)}</h3>

                <p>${escapeHTML(item.address || "Location available")}</p>

                <div class="nearby-meta">
                    <span>📍 ${item.distance_km ?? "--"} km</span>
                    <span>⏱️ ${item.eta_minutes ?? "--"} min</span>
                </div>
            </div>

            <div class="nearby-actions">
                <button class="small-button primary" onclick="selectNearby('${item.id}')">
                    Select
                </button>

                <button class="small-button" onclick="trackNearby('${item.id}')">
                    Track
                </button>
            </div>
        </div>
    `).join("");
}

function getNearbyIcon(type) {
    const icons = {
        hospital: "🏥",
        fire: "🔥",
        police: "🚓",
        rescue: "🛟"
    };

    return icons[type] || "📍";
}

function selectNearby(id) {
    const item = state.nearby.find(place => place.id === id);

    if (!item) {
        return;
    }

    showNotification(`${item.name} selected.`);
}

function trackNearby(id) {
    const item = state.nearby.find(place => place.id === id);

    if (!item) {
        return;
    }

    showNotification(`Tracking ${item.name}.`);
}

async function loadResources() {
    const units = await getUnits();

    renderResources(units);
    updateResourceStats(units);
}

function renderResources(units) {
    const container = document.getElementById("resourceList");

    container.innerHTML = units.map(unit => `
        <div class="resource-row">
            <strong>${escapeHTML(unit.name)}</strong>

            <span>${escapeHTML(unit.type)}</span>

            <span class="resource-status ${unit.status}">
                ${formatStatus(unit.status)}
            </span>

            <span>${escapeHTML(unit.location || "Unknown")}</span>

            <button class="small-button primary"
                onclick="dispatchResource('${unit.id}')">
                Dispatch
            </button>
        </div>
    `).join("");
}

function updateResourceStats(units) {
    const ambulances = units.filter(
        unit => unit.type === "ambulance" && unit.status === "available"
    ).length;

    const fire = units.filter(
        unit => unit.type === "fire" && unit.status === "available"
    ).length;

    const rescue = units.filter(
        unit => unit.type === "rescue" && unit.status === "available"
    ).length;

    document.getElementById("availableAmbulances").textContent = ambulances;
    document.getElementById("availableFireUnits").textContent = fire;
    document.getElementById("availableRescue").textContent = rescue;
    document.getElementById("hospitalCount").textContent = state.nearby.filter(
        item => item.type === "hospital"
    ).length;
}

async function dispatchResource(unitId) {
    if (!state.emergency?.id) {
        showNotification("Create an emergency first.");
        return;
    }

    try {
        await dispatchUnit(unitId, state.emergency.id);

        showNotification("Emergency unit dispatched.");
        addActivity("Response unit dispatched");
        addMCPLog(`Dispatch request sent for ${unitId}`, true);

        await loadResources();

    } catch (error) {
        showNotification("Unable to dispatch unit.");
        addMCPLog(`Dispatch failed for ${unitId}`, false);
    }
}

async function verifyCurrentEmergency() {
    if (!state.emergency) {
        showNotification("No emergency available for verification.");
        return;
    }

    try {
        const result = await verifyEmergency(state.emergency);

        document.getElementById("verifyLocation").textContent =
            result.location_verified ? "Verified" : "Needs review";

        document.getElementById("verifyEmergencyType").textContent =
            result.emergency_verified ? "Verified" : "Needs review";

        document.getElementById("verifyResources").textContent =
            result.resources_verified ? "Verified" : "Needs review";

        document.getElementById("verifyAI").textContent =
            result.ai_verified ? "Verified" : "Needs review";

        addActivity("Emergency data verified");
        addMCPLog("Verification service completed", true);

        showNotification("Verification completed.");

    } catch (error) {
        showNotification("Verification service unavailable.");
        addMCPLog("Verification service unavailable", false);
    }
}

async function coordinateCurrentResponse() {
    if (!state.emergency?.id) {
        return;
    }

    try {
        await coordinateResponse(state.emergency.id);

        addActivity("Response coordination completed");
        addMCPLog("Coordination request sent", true);

    } catch (error) {
        addMCPLog("Coordination request failed", false);
    }
}

async function sendChat() {
    const input = document.getElementById("chatInput");
    const message = input.value.trim();

    if (!message) {
        return;
    }

    addChatMessage(message, "user");
    input.value = "";

    try {
        const response = await sendChatMessage(message);

        const reply =
            response.reply ||
            response.message ||
            "I received your request.";

        addChatMessage(reply, "bot");

    } catch (error) {
        addChatMessage(
            "The backend assistant is currently unavailable. Please use the emergency options or tracking section.",
            "bot"
        );
    }
}

function addChatMessage(message, sender) {
    const container = document.getElementById("chatMessages");

    const wrapper = document.createElement("div");
    wrapper.className = `chat-message ${sender}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = sender === "bot" ? "🤖" : "A";

    const content = document.createElement("div");
    content.className = "message-content";

    const paragraph = document.createElement("p");
    paragraph.textContent = message;

    content.appendChild(paragraph);
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);

    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
}

function showPage(pageId) {
    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });

    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("active");
    });

    const page = document.getElementById(pageId);

    if (!page) {
        return;
    }

    page.classList.add("active");

    const navItem = document.querySelector(
        `.nav-item[data-page="${pageId}"]`
    );

    if (navItem) {
        navItem.classList.add("active");
    }

    const data = pageData[pageId];

    if (data) {
        document.getElementById("pageTitle").textContent = data[0];
        document.getElementById("pageSubtitle").textContent = data[1];
    }

    if (pageId === "nearby") {
        loadNearby();
    }

    if (pageId === "resources" || pageId === "control") {
        loadResources();
    }

    if (pageId === "tracking") {
        loadTracking();
    }
}

function updateLocation() {
    if (!navigator.geolocation) {
        showNotification("Location services are not supported.");
        return;
    }

    navigator.geolocation.getCurrentPosition(
        position => {
            state.userLocation = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy
            };

            document.getElementById("locationText").textContent =
                `${position.coords.latitude.toFixed(5)}, ${position.coords.longitude.toFixed(5)}`;

            addMCPLog("Browser location received", true);
            showNotification("Location detected.");
        },
        () => {
            showNotification("Unable to access your location.");
        }
    );
}

function formatStatus(status) {
    if (!status) {
        return "--";
    }

    return status
        .replaceAll("_", " ")
        .replace(/\b\w/g, letter => letter.toUpperCase());
}

function formatTime(value) {
    if (!value) {
        return "Just now";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Just now";
    }

    return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });
}

function addActivity(message) {
    const list = document.getElementById("activityList");

    const item = document.createElement("div");
    item.className = "activity-item";

    item.innerHTML = `
        <span>🟢</span>
        <div>
            <strong>${escapeHTML(message)}</strong>
            <small>${new Date().toLocaleTimeString()}</small>
        </div>
    `;

    list.prepend(item);
}

function addMCPLog(message, success) {
    const container = document.getElementById("mcpLog");

    const entry = document.createElement("div");
    entry.className = "log-entry";

    const time = new Date().toLocaleTimeString();

    entry.innerHTML = `
        <span class="time">[${time}]</span>
        ${escapeHTML(message)}
        <span class="${success ? "success" : ""}">
            ${success ? " ✓" : ""}
        </span>
    `;

    container.prepend(entry);
}

function showNotification(message) {
    const container = document.getElementById("toastContainer");

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function escapeHTML(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

document.querySelectorAll(".nav-item").forEach(button => {
    button.addEventListener("click", () => {
        showPage(button.dataset.page);
    });
});

document.querySelectorAll("[data-page-target]").forEach(button => {
    button.addEventListener("click", () => {
        showPage(button.dataset.pageTarget);
    });
});

document.querySelectorAll(".emergency-type").forEach(button => {
    button.addEventListener("click", () => {
        const type = button.dataset.type;

        const descriptions = {
            medical: "Someone needs urgent medical assistance.",
            fire: "There is a fire and people may need assistance.",
            accident: "There has been a road accident and people are injured.",
            rescue: "A person is trapped and needs rescue assistance.",
            disaster: "There is a natural disaster emergency.",
            other: "There is an emergency requiring immediate assistance."
        };

        document.getElementById("emergencyDescription").value =
            descriptions[type];

        showPage("emergency");
    });
});

document.querySelectorAll("[data-suggestion]").forEach(button => {
    button.addEventListener("click", () => {
        document.getElementById("emergencyDescription").value =
            button.dataset.suggestion;
    });
});

document.getElementById("detectEmergency").addEventListener(
    "click",
    detectEmergency
);

document.getElementById("locationButton").addEventListener(
    "click",
    updateLocation
);

document.getElementById("refreshTracking").addEventListener(
    "click",
    loadTracking
);

document.getElementById("refreshNearby").addEventListener(
    "click",
    loadNearby
);

document.getElementById("refreshResources").addEventListener(
    "click",
    loadResources
);

document.getElementById("verifyEmergency").addEventListener(
    "click",
    verifyCurrentEmergency
);

document.getElementById("sendChat").addEventListener(
    "click",
    sendChat
);

document.getElementById("chatInput").addEventListener(
    "keydown",
    event => {
        if (event.key === "Enter") {
            sendChat();
        }
    }
);

document.querySelectorAll(".chat-suggestions button").forEach(button => {
    button.addEventListener("click", () => {
        document.getElementById("chatInput").value =
            button.dataset.chat;

        sendChat();
    });
});

document.querySelectorAll(".filter-button").forEach(button => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".filter-button").forEach(item => {
            item.classList.remove("active");
        });

        button.classList.add("active");

        state.currentFilter = button.dataset.filter;

        renderNearby(state.nearby);
    });
});

document.querySelectorAll("[data-service]").forEach(button => {
    button.addEventListener("click", async () => {
        const service = button.dataset.service;

        try {
            await testMCPService(service);

            document.getElementById(
                `${service}ServiceStatus`
            ).textContent = "ONLINE";

            addMCPLog(`${service} MCP service responded`, true);

        } catch (error) {
            addMCPLog(`${service} MCP service unavailable`, false);
        }
    });
});

document.getElementById("notificationButton").addEventListener(
    "click",
    () => {
        showNotification("No new emergency notifications.");
    }
);

document.getElementById("zoomIn").addEventListener(
    "click",
    () => {
        state.mapScale += 0.1;
        document.getElementById("responseMap").style.transform =
            `scale(${state.mapScale})`;
    }
);

document.getElementById("zoomOut").addEventListener(
    "click",
    () => {
        state.mapScale = Math.max(0.7, state.mapScale - 0.1);
        document.getElementById("responseMap").style.transform =
            `scale(${state.mapScale})`;
    }
);

document.getElementById("resetMap").addEventListener(
    "click",
    () => {
        state.mapScale = 1;
        document.getElementById("responseMap").style.transform =
            "scale(1)";
    }
);

async function initializeApp() {
    await checkBackend();
    await getNearbyHelp();
    await getUnits();
    updateResourceStats(state.units);
}

initializeApp();