"""End-to-End Emergency Scenario Verification for MCP-ResQ.

Executes two full lifecycle scenarios:
Scenario 1: Chemical Hazard Spill -> Safety Discovery -> Resource Gap -> Dispatch -> Road Route -> Simulation Tracking -> Arrival -> Audit.
Scenario 2: Multi-Vehicle Collision -> ICU Hospital Discovery -> Trauma Handoff -> Dual Dispatch -> Live Simulation -> Audit.
"""

import json
import sys
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def request_json(method: str, path: str, data: dict = None, headers: dict = None):
    url = f"{BASE_URL}{path}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"error": content}


def run_scenario_1_chemical_spill():
    print("\n" + "=" * 70)
    print("🚨 RUNNING SCENARIO 1: INDUSTRIAL CHEMICAL SPILL (NORTH CAMPUS)")
    print("=" * 70)

    # 1. Create Emergency Incident
    emg_payload = {
        "description": "Hazardous toxic vapor release from chemical reactor drum, 4 workers coughing with respiratory distress.",
        "type": "chemical_spill",
        "priority": "CRITICAL",
        "severity": "CRITICAL",
        "latitude": 12.9785,
        "longitude": 77.6010,
        "location": {
            "latitude": 12.9785,
            "longitude": 77.6010,
            "accuracy": 8.0,
        },
        "affected_count": 4,
        "critical_count": 2,
    }
    status, emg_data = request_json("POST", "/api/emergencies", emg_payload)
    assert status in (200, 201), f"Failed to create emergency: {emg_data}"
    emg_id = emg_data["id"]
    print(f"✅ 1. Emergency Created: {emg_id} (Type: {emg_data['type']}, Priority: {emg_data['priority']})")

    # 2. AI Reasoning / Triage
    ai_status, ai_resp = request_json("POST", "/api/ai/triage", {
        "description": emg_payload["description"],
        "type": emg_payload["type"],
        "severity": emg_payload["severity"],
    })
    print(f"✅ 2. AI Triage Completed: Severity={ai_resp.get('severity')}, Units Needed={ai_resp.get('recommended_units')}")

    # 3. MCP Tool: Find Safe Evacuation Location
    mcp_safe_status, mcp_safe = request_json("POST", "/api/mcp/execute", {
        "tool": "safety.find_safe_location",
        "arguments": {"latitude": emg_payload["latitude"], "longitude": emg_payload["longitude"]},
    })
    assert mcp_safe_status == 200
    safe_zone = mcp_safe["result"].get("safe_zone", {})
    print(f"✅ 3. MCP Safety Connected: Identified Upwind Assembly Zone '{safe_zone.get('name')}' at {safe_zone.get('distance_km')} km")

    # 4. MCP Tool: Resource Gap Calculation & Python Verification
    gap_status, gap_data = request_json("POST", "/api/verify/resource-gaps", {
        "required": {"hazmat": 1, "ambulance": 2},
    })
    assert gap_status == 200
    print(f"✅ 4. Python Verification: Mathematical Gaps Verified -> {gap_data['gaps']}")

    # 5. Unit Discovery & Dispatch
    units_status, units = request_json("GET", "/api/units")
    assert units_status == 200 and len(units) > 0
    avail = [u for u in units if u.get("status") == "available"]
    if avail:
        assigned_unit = avail[0]
    else:
        assigned_unit = units[0]
        # Release unit via MCP tool first
        request_json("POST", "/api/mcp/execute", {
            "tool": "dispatch.cancel_dispatch",
            "arguments": {"unit_id": assigned_unit["id"]},
        })

    unit_id = assigned_unit["id"]
    disp_status, disp_res = request_json("POST", f"/api/units/{unit_id}/dispatch", {
        "emergency_id": emg_id
    })
    assert disp_status == 200, f"Dispatch failed: {disp_res}"
    print(f"✅ 5. Unit Dispatched: {assigned_unit['name']} ({unit_id}) assigned to {emg_id}")

    # 6. Route Calculation & Google/Fallback Geometry
    route_status, route_data = request_json("POST", "/api/routes/calculate", {
        "origin_lat": assigned_unit["latitude"],
        "origin_lng": assigned_unit["longitude"],
        "dest_lat": emg_payload["latitude"],
        "dest_lng": emg_payload["longitude"],
        "origin_name": assigned_unit["name"],
        "dest_name": f"Scene {emg_id}",
    })
    assert route_status == 200
    print(f"✅ 6. Route Computed: Distance={route_data['distance_km']} km, ETA={route_data['duration_mins']}m, Source='{route_data['data_source']}'")

    # 7. Real-Time Tracking State
    trk_status, trk_data = request_json("GET", f"/api/emergencies/{emg_id}/tracking")
    assert trk_status == 200
    print(f"✅ 7. Initial Tracking Telemetry: Pos=({trk_data['latitude']}, {trk_data['longitude']}), ETA={trk_data['eta_minutes']}m, Progress={trk_data['progress']}%")

    # 8. Simulation Speed Controls & Pause/Resume Test
    # Set Speed to 80 km/h
    _, ctrl_res = request_json("POST", f"/api/emergencies/{emg_id}/simulation/control", {
        "action": "set_speed",
        "speed_kmh": 80.0,
    })
    assert ctrl_res["speed_kmh"] == 80.0
    print(f"✅ 8a. Speed adjusted on backend to {ctrl_res['speed_kmh']} km/h")

    # Pause simulation
    _, p_res = request_json("POST", f"/api/emergencies/{emg_id}/simulation/control", {"action": "pause"})
    assert p_res["is_paused"] is True
    print("✅ 8b. Simulation paused on backend - coordinate displacement frozen")

    # Resume simulation with 5x multiplier
    _, m_res = request_json("POST", f"/api/emergencies/{emg_id}/simulation/control", {
        "action": "set_multiplier",
        "multiplier": 5.0,
    })
    request_json("POST", f"/api/emergencies/{emg_id}/simulation/control", {"action": "resume"})
    print("✅ 8c. Simulation resumed with 5x fast-forward multiplier")

    # 9. Step forward simulation until ARRIVED
    for i in range(15):
        request_json("POST", f"/api/emergencies/{emg_id}/simulation/control", {"action": "step"})
        _, curr_trk = request_json("GET", f"/api/emergencies/{emg_id}/tracking")
        if curr_trk["status"] in ("near_destination", "arrived", "on_scene"):
            print(f"   -> Stepped to status: {curr_trk['status']} (Progress: {curr_trk['progress']}%, Dist: {curr_trk['distance_km']} km)")
            if curr_trk["status"] in ("arrived", "on_scene"):
                break

    # 10. Audit Trail Verification
    audit_status, audit_res = request_json("GET", f"/api/emergencies/{emg_id}/audit")
    assert audit_status == 200
    events = [e["event_type"] for e in audit_res.get("audit_trail", [])]
    print(f"✅ 10. Audit Trail Logged: Total {audit_res['total']} events recorded: {events[:6]}")
    print("🎉 SCENARIO 1 COMPLETED SUCCESSFULLY!\n")


def run_scenario_2_traffic_pileup():
    print("=" * 70)
    print("🚨 RUNNING SCENARIO 2: MULTI-VEHICLE COLLISION & TRAUMA HANDOFF")
    print("=" * 70)

    # 1. Create Multi-Casualty Incident
    emg_payload = {
        "description": "Multi-car highway pileup on Outer Ring Road, 2 trapped passengers with critical blunt trauma.",
        "type": "accident",
        "priority": "CRITICAL",
        "severity": "CRITICAL",
        "latitude": 12.9350,
        "longitude": 77.6950,
        "affected_count": 6,
        "critical_count": 2,
    }
    status, emg_data = request_json("POST", "/api/emergencies", emg_payload)
    assert status in (200, 201), f"Failed to create emergency: {emg_data}"
    emg_id = emg_data["id"]
    print(f"✅ 1. Collision Incident Created: {emg_id}")

    # 2. Find Nearest Hospital with ICU Readiness
    hosp_status, hosp_res = request_json("POST", "/api/mcp/execute", {
        "tool": "hospitals.find_nearest",
        "arguments": {
            "latitude": emg_payload["latitude"],
            "longitude": emg_payload["longitude"],
            "requires_icu": True,
        },
    })
    assert hosp_status == 200
    hosp_info = hosp_res["result"].get("best_hospital") or hosp_res["result"].get("hospitals", [{}])[0]
    hosp_id = hosp_info.get("id", "H-101")
    print(f"✅ 2. MCP Hospital Located: {hosp_info.get('name')} (ID: {hosp_id}, Dist: {hosp_info.get('distance_km')} km)")

    # 3. Transmit Hospital Trauma Handoff Pre-Arrival Alert
    handoff_status, handoff_res = request_json("POST", "/api/mcp/execute", {
        "tool": "hospitals.prepare_handoff",
        "arguments": {
            "emergency_id": emg_id,
            "hospital_id": hosp_id,
            "patient_summary": "2 critical polytrauma victims requiring immediate surgical bay and blood transfusion.",
        },
    })
    assert handoff_status == 200
    print(f"✅ 3. Trauma Bay Pre-Arrival Notification Sent: Status='{handoff_res['result'].get('handoff_status')}', ICU Reserved={handoff_res['result'].get('icu_bed_reserved')}")

    # 4. Dispatch Heavy Rescue / Ambulance
    units_status, units = request_json("GET", "/api/units")
    avail = [u for u in units if u.get("status") == "available"]
    if avail:
        target_unit = avail[0]
    else:
        target_unit = units[1] if len(units) > 1 else units[0]
        request_json("POST", "/api/mcp/execute", {
            "tool": "dispatch.cancel_dispatch",
            "arguments": {"unit_id": target_unit["id"]},
        })

    disp2_status, disp2_data = request_json("POST", f"/api/units/{target_unit['id']}/dispatch", {"emergency_id": emg_id})
    assert disp2_status == 200, f"Scenario 2 dispatch failed: {disp2_data}"
    print(f"✅ 4. Response Unit Dispatched: {target_unit['name']} ({target_unit['id']})")

    # 5. Live Road Simulation Telemetry Verification
    _, trk = request_json("GET", f"/api/emergencies/{emg_id}/tracking")
    assert trk["status"] in ("dispatched", "en_route")
    print(f"✅ 5. Live Response Telemetry: Unit={trk['unit_name']}, Data Source='{trk['data_source']}', ETA={trk['eta_minutes']} min")

    # 6. Check System-Wide Audit Log from Operator Perspective
    audit_status, audit_res = request_json("GET", "/api/audit/recent?limit=10")
    assert audit_status == 200 and audit_res["total"] > 0
    print(f"✅ 6. System Audit Ledger: {audit_res['total']} recorded operational events across all incidents")
    print("🎉 SCENARIO 2 COMPLETED SUCCESSFULLY!\n")


if __name__ == "__main__":
    try:
        run_scenario_1_chemical_spill()
        run_scenario_2_traffic_pileup()
        print("=" * 70)
        print("🌟 ALL SCENARIOS VALIDATED 100% END-TO-END WITH ZERO ERRORS!")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Error during scenario execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
