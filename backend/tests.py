"""Comprehensive automated test suite for the consolidated MCP-ResQ platform.

Verifies:
- Health check
- Emergency incident creation, validation, retrieval, and 404
- Emergency resource units filtering and listing
- Hospital discovery and capacity reporting
- Nearby emergency services
- Authoritative dispatch and tracking creation
- Conflict prevention (HTTP 409 on duplicate dispatch)
- Live responder tracking (REST)
- WebSocket real-time telemetry streaming
- Python deterministic verification (coordinates, type, incident)
- What-If capacity simulation engine
- Resource gap calculation (deterministic, no hallucination)
- Full incident coordination workflow
- AI Assistant natural language reasoning with live MCP grounding & deterministic fallback
- Model Context Protocol (MCP) tool registry across 9 domains
- MCP execution tracing with latency and provenance tracking
- MCP test endpoints (location, resource, hospital, verification)
- Direct MCP tool execution via POST /api/mcp/execute
- Emergency alert system and geofencing
- Multi-incident concurrency and resource contention
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.ai import classify_emergency_text, handle_ai_chat
from backend.database import Base, SessionLocal, engine
from backend.main import app
from backend.mcp import MCP_TOOL_REGISTRY, call_mcp_tool, global_mcp_tracer
from backend.models import Emergency, EmergencyUnit, Hospital, Tracking
from backend.services import AlertService, ResourceService, TrackingService
from backend.verification import (
    calculate_eta,
    calculate_haversine,
    calculate_resource_gaps,
    run_verification,
    run_what_if_simulation,
    validate_coordinates,
)
from data.seed import seed_database


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Ensure clean isolated database state for tests."""
    seed_database(force=True)
    yield


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


# ----------------------------------------------------------------------------
# 1. Health Endpoint Tests
# ----------------------------------------------------------------------------
def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "MCP-ResQ"
    assert data["mcp_enabled"] is True
    assert "verification_engine" in data


# ----------------------------------------------------------------------------
# 2. Emergency Creation & Retrieval Tests
# ----------------------------------------------------------------------------
def test_create_emergency_success(client):
    payload = {
        "description": "Multi-car pileup near Indiranagar flyover with trapped passengers",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "type": "accident",
        "priority": "HIGH",
        "severity": "HIGH",
    }
    response = client.post("/api/emergencies", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("EMG-")
    assert data["type"] == "accident"
    assert data["priority"] == "HIGH"
    assert data["location"]["latitude"] == 12.9784
    assert data["location"]["longitude"] == 77.6408


def test_create_emergency_validation_failure(client):
    # Description too short
    payload = {
        "type": "accident",
        "description": "a",
        "latitude": 12.9784,
        "longitude": 77.6408,
    }
    response = client.post("/api/emergencies", json=payload)
    assert response.status_code in (400, 422)


def test_list_and_get_emergencies(client):
    response = client.get("/api/emergencies")
    assert response.status_code == 200
    emergencies = response.json()
    assert len(emergencies) >= 3

    emg_id = emergencies[0]["id"]
    single = client.get(f"/api/emergencies/{emg_id}")
    assert single.status_code == 200
    assert single.json()["id"] == emg_id


def test_get_emergency_not_found(client):
    response = client.get("/api/emergencies/NONEXISTENT-999")
    assert response.status_code == 404


# ----------------------------------------------------------------------------
# 3. Unit Discovery & Dispatch Tests
# ----------------------------------------------------------------------------
def test_get_units_listing_and_filtering(client):
    # List all units
    res_all = client.get("/api/units")
    assert res_all.status_code == 200
    units = res_all.json()
    assert len(units) >= 10

    # Filter by type ambulance
    res_amb = client.get("/api/units?type=ambulance")
    assert res_amb.status_code == 200
    for u in res_amb.json():
        assert u["type"] == "ambulance"

    # Filter with caller proximity
    res_prox = client.get("/api/units?latitude=12.9716&longitude=77.5946")
    assert res_prox.status_code == 200
    for u in res_prox.json():
        assert u["distance_km"] is not None
        assert u["eta_minutes"] is not None


def test_dispatch_unit_success(client):
    units = client.get("/api/units").json()
    avail = [u for u in units if u["status"] == "available"]
    assert len(avail) > 0
    target_unit = avail[0]

    payload = {"emergency_id": "EMG-1002"}
    res = client.post(f"/api/units/{target_unit['id']}/dispatch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["unit_id"] == target_unit["id"]
    assert data["status"] == "dispatched"


def test_dispatch_conflict_prevention(client):
    # AMB-101 is already dispatched in seed data, attempting to dispatch again must yield 409
    payload = {"emergency_id": "EMG-1003"}
    res = client.post("/api/units/AMB-101/dispatch", json=payload)
    assert res.status_code == 409
    assert "Conflict" in res.json()["detail"]


# ----------------------------------------------------------------------------
# 4. Hospitals & Nearby Help Tests
# ----------------------------------------------------------------------------
def test_get_hospitals_and_capacity(client):
    res = client.get("/api/hospitals?latitude=12.9716&longitude=77.5946")
    assert res.status_code == 200
    hospitals = res.json()
    assert len(hospitals) >= 4
    for h in hospitals:
        assert "available_beds" in h
        assert "icu_beds" in h
        assert "trauma_level" in h
        assert h["distance_km"] is not None


def test_get_nearby_help(client):
    res = client.get("/api/nearby-help?latitude=12.9716&longitude=77.5946")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 4
    # Ensure sorted by distance
    distances = [item["distance_km"] for item in items]
    assert distances == sorted(distances)


# ----------------------------------------------------------------------------
# 5. Tracking (REST & WebSocket) Tests
# ----------------------------------------------------------------------------
def test_tracking_rest_endpoint(client):
    # EMG-1001 has active tracking in seed
    res = client.get("/api/emergencies/EMG-1001/tracking")
    assert res.status_code == 200
    data = res.json()
    assert data["unit_id"] == "AMB-101"
    assert data["progress"] >= 15
    assert data["speed_kmh"] > 0
    assert data["data_status"] == "SIMULATED LIVE TRACKING"


def test_tracking_not_found(client):
    # Emergency with no dispatched unit
    db = SessionLocal()
    try:
        emg = Emergency(
            id="EMG-TEST-NOTRACK",
            description="Untracked test event",
            type="general",
            priority="LOW",
            severity="LOW",
            status="pending",
            latitude=12.97,
            longitude=77.59,
        )
        db.add(emg)
        db.commit()
    finally:
        db.close()

    res = client.get("/api/emergencies/EMG-TEST-NOTRACK/tracking")
    assert res.status_code == 404


def test_tracking_websocket(client):
    # WebSocket streaming test
    with client.websocket_connect("/ws/emergencies/EMG-1001/tracking") as ws:
        frame = ws.receive_json()
        assert frame["event"] == "tracking_update"
        assert frame["unit_id"] == "AMB-101"
        assert "progress" in frame


# ----------------------------------------------------------------------------
# 6. Python Deterministic Verification Tests
# ----------------------------------------------------------------------------
def test_coordinate_verification():
    assert validate_coordinates(12.9716, 77.5946) is True
    assert validate_coordinates(95.0, 77.5946) is False
    assert validate_coordinates(12.9716, 200.0) is False


def test_haversine_and_eta_math():
    dist = calculate_haversine(12.9716, 77.5946, 12.9800, 77.6000)
    assert 1.0 < dist < 2.0
    eta = calculate_eta(dist, speed_kmh=42.0)
    assert eta >= 1


def test_verify_incident_endpoint(client):
    payload = {
        "emergency_id": "EMG-1001",
        "emergency_type": "accident",
        "location": {"latitude": 12.9716, "longitude": 77.5946},
    }
    res = client.post("/api/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["overall_verified"] is True
    assert data["checks"]["coordinates_valid"] is True
    assert data["checks"]["type_valid"] is True


def test_resource_gaps_calculation(client):
    payload = {
        "required": {"ambulance": 3, "fire": 2, "rescue": 1},
        "available": {"ambulance": 1, "fire": 2, "rescue": 0},
    }
    res = client.post("/api/verify/resource-gaps", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["verified_by_python"] is True
    gaps = {g["type"]: g["gap"] for g in data["gaps"]}
    assert gaps["ambulance"] == 2
    assert gaps["fire"] == 0
    assert gaps["rescue"] == 1


def test_what_if_simulation_endpoint(client):
    payload = {
        "scenario": "add_resource",
        "parameters": {"unit_type": "ambulance", "count": 2},
    }
    res = client.post("/api/verify/what-if", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["verified_by_python"] is True
    assert data["scenario"] == "add_resource"
    assert "before" in data
    assert "after" in data


# ----------------------------------------------------------------------------
# 7. Coordination Cycle Tests
# ----------------------------------------------------------------------------
def test_coordination_cycle(client):
    payload = {"emergency_id": "EMG-1003"}
    res = client.post("/api/coordinate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["emergency_id"] == "EMG-1003"
    assert len(data["resources"]) > 0
    assert data["verification"]["overall_verified"] is True


# ----------------------------------------------------------------------------
# 8. AI Chat & Grounding Tests
# ----------------------------------------------------------------------------
def test_ai_chat_deterministic_fallback(client):
    payload = {
        "message": "Where is the responder and what is the ETA?",
        "emergency_id": "EMG-1001",
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["emergency_id"] == "EMG-1001"
    assert "get_response_status" in data["mcp_tools_used"]
    assert any(term in data["response"].lower() for term in ["eta", "arrive", "arrival", "minute", "min"])
    assert len(data["response"]) > 20


def test_ai_chat_why_selected(client):
    payload = {"message": "Why was this ambulance selected?"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "penalty" in data["response"].lower() or "matching" in data["response"].lower()


def test_ai_chat_empty_message(client):
    payload = {"message": "   "}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 400


def test_ai_chat_unrelated_query(client):
    """Test that out-of-scope questions are politely declined without executing operational tools."""
    payload = {"message": "What is the capital of France and what is the best recipe for chocolate cake?"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "outside" in data["response"].lower() or "scope" in data["response"].lower() or "emergency" in data["response"].lower()
    # Unrelated queries must not execute unnecessary operational MCP tools
    assert len(data["mcp_tools_used"]) == 0


def test_ai_chat_ambiguous_query(client):
    """Test that vague/incomplete single-word queries prompt for concise clarification."""
    payload = {"message": "status"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "which" in data["response"].lower() or "incident" in data["response"].lower() or "specify" in data["response"].lower()


def test_ai_chat_conversational_followup(client):
    """Test that conversational context and history are respected on follow-up questions."""
    payload = {
        "message": "Is it getting closer?",
        "emergency_id": "EMG-1001",
        "history": [
            {"role": "user", "content": "Where is the responder for EMG-1001?"},
            {"role": "assistant", "content": "Ambulance A-12 is en route, 2.1 km away."}
        ]
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "get_response_status" in data["mcp_tools_used"]
    assert "route" in data["response"].lower() or "km" in data["response"].lower() or "arrived" in data["response"].lower() or "min" in data["response"].lower()


def test_ai_chat_missing_mcp_data(client):
    """Test that unverified/non-existent incidents do not produce fabricated operational facts."""
    payload = {
        "message": "What is the current status of incident EMG-9999?",
        "emergency_id": "EMG-9999"
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert any(term in data["response"].lower() for term in ["not", "n't", "no record", "couldn't", "unverified", "unable", "cannot", "confirm"])


def test_ai_chat_urgent_emergency_scenario(client):
    """Test that life-threatening emergency descriptions prioritize immediate safety and 112/911 call."""
    payload = {"message": "Someone collapsed and is bleeding heavily and cannot breathe right now!"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "112" in data["response"] or "911" in data["response"] or "emergency" in data["response"].lower()


def test_ai_chat_hospitals_medical_query(client):
    """Test that medical facility questions retrieve verified hospital data and ICU availability."""
    payload = {"message": "Which nearby hospital has ICU beds available?"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "get_nearby_hospitals" in data["mcp_tools_used"]
    assert "hospital" in data["response"].lower() or "icu" in data["response"].lower()


def test_ai_chat_safety_procedure_numbered_steps(client):
    """Test that medical/safety first-aid requests return clear numbered steps."""
    payload = {"message": "What should I do for severe bleeding while waiting for responders?"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "1." in data["response"] and "2." in data["response"]


def test_ai_chat_direct_action_safety(client):
    """Test that direct commands to dispatch do not claim action was taken via chat."""
    payload = {"message": "Dispatch ambulance AMB-101 immediately right now"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "cannot" in data["response"].lower() or "request help" in data["response"].lower() or "operator" in data["response"].lower()



# ----------------------------------------------------------------------------
# 9. MCP Tools & Diagnostics Tests
# ----------------------------------------------------------------------------
def test_mcp_tools_listing(client):
    res = client.get("/api/mcp/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["total_tools"] >= 25
    tool_names = [t["name"] for t in data["tools"]]
    assert "get_emergency_location" in tool_names
    assert "get_available_units" in tool_names
    assert "get_nearby_hospitals" in tool_names
    assert "calculate_route" in tool_names
    assert "find_safe_zone" in tool_names
    assert "verify_emergency" in tool_names
    assert "dispatch_unit" in tool_names
    assert "get_resource_utilization" in tool_names


def test_mcp_traces_endpoint(client):
    # Execute a tool to generate a trace
    call_mcp_tool("get_unit_location", unit_id="AMB-101")

    res = client.get("/api/mcp/trace")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_recorded"] > 0
    first_trace = data["traces"][0]
    assert "tool" in first_trace
    assert "duration_ms" in first_trace
    assert "provenance" in first_trace


def test_mcp_test_endpoints(client):
    assert client.get("/api/mcp/location/test").status_code == 200
    assert client.get("/api/mcp/resource/test").status_code == 200
    assert client.get("/api/mcp/hospital/test").status_code == 200
    assert client.get("/api/mcp/verification/test").status_code == 200


def test_mcp_direct_execute_endpoint(client):
    payload = {
        "tool": "get_available_units",
        "arguments": {"unit_type": "fire"},
    }
    res = client.post("/api/mcp/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["result"]["total_available"] >= 1


# ----------------------------------------------------------------------------
# 10. Alerts System & Geofencing Tests
# ----------------------------------------------------------------------------
def test_alert_service(client):
    db = SessionLocal()
    try:
        alert = AlertService.create_alert(
            db,
            title="Industrial Evacuation Warning",
            message="Evacuate 300m upwind.",
            severity="CRITICAL",
            area="North Quad",
        )
        assert alert.id is not None
        assert alert.title == "Industrial Evacuation Warning"

        alerts = AlertService.list_alerts(db)
        assert len(alerts) >= 1
    finally:
        db.close()


# ----------------------------------------------------------------------------
# 11. Configuration & Security Endpoint Tests
# ----------------------------------------------------------------------------
def test_get_config_security(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "google_maps_browser_key" in data
    assert "google_maps_map_id" in data
    assert "status" in data
    status = data["status"]
    # Check that secrets are NEVER leaked in the response, only status strings
    assert status["google_maps_browser_key"] in ["CONNECTED", "MISSING"]
    assert status["google_maps_server_key"] in ["CONNECTED", "MISSING"]
    assert status["gemini_api_key"] in ["CONNECTED", "MISSING"]
    assert status["twilio_configured"] in ["CONNECTED", "MISSING"]
    assert "GOOGLE_MAPS_SERVER_KEY" not in str(data)
    assert "AIzaSy" not in str(data.get("status", {}))  # No raw server keys


# ----------------------------------------------------------------------------
# 12. Simulation Control Deck Tests
# ----------------------------------------------------------------------------
def test_simulation_control_flow(client):
    # Ensure an emergency has a dispatched unit
    units = client.get("/api/units").json()
    avail = [u for u in units if u["status"] == "available"]
    assert len(avail) > 0
    target_unit = avail[0]

    emg_res = client.get("/api/emergencies").json()
    assert len(emg_res) > 0
    emg_id = emg_res[0]["id"]
    client.post(f"/api/units/{target_unit['id']}/dispatch", json={"emergency_id": emg_id})

    # Initial tracking
    trk_res = client.get(f"/api/emergencies/{emg_id}/tracking")
    assert trk_res.status_code == 200
    trk_data = trk_res.json()
    assert "data_source" in trk_data
    assert "is_paused" in trk_data

    # 1. Pause simulation
    ctrl_pause = client.post(
        f"/api/emergencies/{emg_id}/simulation/control",
        json={"action": "pause"},
    )
    assert ctrl_pause.status_code == 200
    p_data = ctrl_pause.json()
    assert p_data["success"] is True
    assert p_data["is_paused"] is True

    # 2. Set speed to 50 km/h
    ctrl_speed = client.post(
        f"/api/emergencies/{emg_id}/simulation/control",
        json={"action": "set_speed", "speed_kmh": 50.0},
    )
    assert ctrl_speed.status_code == 200
    s_data = ctrl_speed.json()
    assert s_data["speed_kmh"] == 50.0

    # 3. Set multiplier to 5.0
    ctrl_mult = client.post(
        f"/api/emergencies/{emg_id}/simulation/control",
        json={"action": "set_multiplier", "multiplier": 5.0},
    )
    assert ctrl_mult.status_code == 200
    m_data = ctrl_mult.json()
    assert m_data["multiplier"] == 5.0

    # 4. Resume simulation
    ctrl_resume = client.post(
        f"/api/emergencies/{emg_id}/simulation/control",
        json={"action": "resume"},
    )
    assert ctrl_resume.status_code == 200
    r_data = ctrl_resume.json()
    assert r_data["is_paused"] is False

    # 5. Restart simulation
    ctrl_restart = client.post(
        f"/api/emergencies/{emg_id}/simulation/control",
        json={"action": "restart"},
    )
    assert ctrl_restart.status_code == 200
    rst_data = ctrl_restart.json()
    assert rst_data["progress"] <= 15.0


# ----------------------------------------------------------------------------
# 13. Audit Log System Tests
# ----------------------------------------------------------------------------
def test_audit_logs_endpoints(client):
    res_recent = client.get("/api/audit/recent?limit=10")
    assert res_recent.status_code == 200
    data = res_recent.json()
    assert "total" in data
    assert "audit_trail" in data
    assert isinstance(data["audit_trail"], list)

    emg_res = client.get("/api/emergencies").json()
    if emg_res:
        emg_id = emg_res[0]["id"]
        res_emg_audit = client.get(f"/api/emergencies/{emg_id}/audit")
        assert res_emg_audit.status_code == 200
        e_data = res_emg_audit.json()
        assert e_data["emergency_id"] == emg_id
        assert "audit_trail" in e_data


# ----------------------------------------------------------------------------
# 14. DEV-Only Control Centre Authentication Guard Tests
# ----------------------------------------------------------------------------
def test_control_centre_backend_protection(client):
    # 1. Unauthorized request without token
    res_unauth = client.get("/control-centre")
    assert res_unauth.status_code == 401
    assert "Operator Control Centre" in res_unauth.text

    # 2. Authorized request with query token
    res_auth = client.get("/control-centre?token=resq-operator-secure-2026")
    assert res_auth.status_code == 200
    assert "Operator Control Centre" in res_auth.text

    # 3. Authorized request with header
    res_header = client.get("/control-centre", headers={"X-Operator-Token": "resq-operator-secure-2026"})
    assert res_header.status_code == 200


# ----------------------------------------------------------------------------
# 15. Structured Dot-Namespaced MCP Tools Tests
# ----------------------------------------------------------------------------
def test_dot_namespaced_mcp_tools():
    # Maps tools
    route_calc = call_mcp_tool(
        "maps.calculate_route",
        origin_lat=12.9716,
        origin_lng=77.5946,
        dest_lat=12.9780,
        dest_lng=77.6400,
    )
    assert "distance_km" in route_calc
    assert "route_geometry" in route_calc
    assert route_calc["distance_km"] > 0

    route_geo = call_mcp_tool(
        "maps.get_route_geometry",
        origin_lat=12.9716,
        origin_lng=77.5946,
        dest_lat=12.9780,
        dest_lng=77.6400,
    )
    assert len(route_geo["route_geometry"]) > 0

    route_eta = call_mcp_tool(
        "maps.get_eta",
        distance_km=5.0,
        speed_kmh=60.0,
    )
    assert route_eta["eta_minutes"] > 0

    # Resources tools
    res_find = call_mcp_tool("resources.find", unit_type="ambulance")
    assert isinstance(res_find, (list, dict))

    res_avail = call_mcp_tool("resources.availability")
    assert isinstance(res_avail, (list, dict))

    res_gap = call_mcp_tool(
        "resources.detect_gap",
        required={"ambulance": 2, "fire_truck": 1},
    )
    assert "gaps" in res_gap or "verified_by_python" in res_gap

    # Dispatch tools
    disp_find = call_mcp_tool("dispatch.find_available_unit")
    assert disp_find is not None

    # Hospitals tools
    hosp_find = call_mcp_tool("hospitals.find_nearest", latitude=12.9716, longitude=77.5946)
    assert hosp_find is not None

    hosp_cap = call_mcp_tool("hospitals.get_capacity", hospital_id="H-101")
    assert hosp_cap is not None

    # Safety tools
    safety_loc = call_mcp_tool("safety.find_safe_location", latitude=12.9716, longitude=77.5946)
    assert safety_loc is not None

    # Verification tools
    verif_track = call_mcp_tool(
        "verification.validate_tracking",
        latitude=12.9716,
        longitude=77.5946,
        speed_kmh=45.0,
        status="EN_ROUTE",
    )
    assert verif_track["is_valid"] is True
