# MCP-ResQ — Consolidated Platform Documentation

> **Core Principle**:  
> **AI Reasons. MCP Connects. Python Verifies.**

---

## 1. Project Overview & Mission

**MCP-ResQ** is an AI-powered emergency resource coordination decision-support prototype built by **Team AGENTIX** for the Model Context Protocol (MCP) Hackathon.

In high-stress municipal or campus emergencies (chemical spills, industrial fires, mass-casualty collisions), decision-makers face fragmented data, conflicting fleet status reports, and communication latency. Conventional Large Language Models frequently hallucinate resource numbers, hospital bed availability, and travel ETAs when asked directly.

MCP-ResQ solves this through a strict architectural tri-partition:
1. **Gemini AI Reasons**: Interprets natural language reports, prioritizes tactical goals, selects MCP tools, and explains complex operational plans.
2. **MCP Connects**: The official Model Context Protocol standardizes structured, authenticated access to 29 tools across 9 operational domains.
3. **Deterministic Python Verifies**: Authoritatively computes all numerical gaps, Haversine/Google Routes distances, conflict checks, and what-if simulation outputs. The AI is strictly barred from inventing numbers.

---

## 2. System Architecture

```
                  ┌──────────────────────────────────────────┐
                  │          USER INTERFACE (Browser)        │
                  │       index.html | style.css | script.js │
                  └─────────────────────┬────────────────────┘
                                        │ HTTP / WebSocket
                                        ▼
                  ┌──────────────────────────────────────────┐
                  │          FASTAPI BACKEND SERVICE         │
                  │               (backend/main.py)          │
                  └──────┬──────────────────────┬────────────┘
                         │                      │
        ┌────────────────▼────────┐    ┌────────▼────────────────┐
        │     SERVICE LAYER       │    │     VERIFICATION LAYER  │
        │   (backend/services.py) │    │ (backend/verification.py│
        │  • Emergency Service    │    │  • Haversine & ETA math │
        │  • Resource Service     │    │  • Coordinate bounds    │
        │  • Hospital Service     │    │  • Resource gaps calc   │
        │  • Tracking Service     │    │  • What-If simulation   │
        │  • Alert Service        │    │  • Conflict detection   │
        └────────────────┬────────┘    └────────┬────────────────┘
                         │                      │
                         ▼                      ▼
                  ┌──────────────────────────────────────────┐
                  │         MODEL CONTEXT PROTOCOL           │
                  │           (backend/mcp.py)               │
                  │  Official MCPServer + 29 Tools + Tracer  │
                  └──────┬──────────────────────┬────────────┘
                         │                      │
        ┌────────────────▼────────┐    ┌────────▼────────────────┐
        │      AI ASSISTANT       │    │   SQLITE PERSISTENCE    │
        │    (backend/ai.py)      │    │  (backend/database.py)  │
        │  • Gemini 2.5 Flash     │    │  • Emergencies & Fleet  │
        │  • MCP Tool Retrieval   │    │  • Hospitals & Tracking │
        │  • Deterministic Engine │    │  • Alerts & Dispatches  │
        └─────────────────────────┘    └─────────────────────────┘
```

---

## 3. Project File Structure

The project has been consolidated into a clean, compact, and beginner-friendly structure:

```
MCP-ResQ/
│
├── index.html               # Civilian emergency intake & operator control center UI
├── style.css                # Dark mode, glassmorphic responsive styles
├── script.js                # Frontend controller (REST APIs, WebSockets, maps)
│
├── backend/
│   ├── main.py              # FastAPI application, CORS, all REST routes & WebSocket
│   ├── database.py          # SQLite engine, SessionLocal, Base, table definitions
│   ├── models.py            # Unified SQLAlchemy ORM models & Pydantic validation schemas
│   ├── services.py          # Consolidated business logic across 8 service domains
│   ├── mcp.py               # Official MCPServer, 29 tools, execution tracer, tool registry
│   ├── ai.py                # Gemini orchestration & deterministic fallback reasoning
│   ├── verification.py      # Deterministic Python math, gaps, and What-If engine
│   └── tests.py             # Complete automated test suite (27 unit/integration tests)
│
├── data/
│   ├── seed.py              # Synthetic 10-role fleet, facilities, and scenarios seed script
│   └── sources.md           # Dataset licenses, open provenance, and ethical guidelines
│
├── docs/
│   └── README.md            # Comprehensive system documentation (this file)
│
├── pytest.ini               # Pytest configuration with isolated import mode
├── .env.example             # Environment variable template
├── .gitignore               # Clean git exclusions (Python, SQLite, caches)
└── requirements.txt         # Pinned production dependencies
```

---

## 4. Quick Start & Setup

### Prerequisites
* Python 3.12+
* Virtual environment (`venv` or `uv`)

### 1. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database (Automated on Start)
```bash
python3 data/seed.py
```

### 4. Run the FastAPI Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
* Alternative Documentation (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Access the Web Frontend
Simply open your browser to:
👉 **[http://localhost:8000](http://localhost:8000)**

*(FastAPI serves `index.html`, `style.css`, and `script.js` directly from the project root).*

---

## 5. API Reference Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend status, version, and verification engine check |
| `POST` | `/api/emergencies` | Create emergency incident and trigger auto-coordination |
| `GET` | `/api/emergencies` | List all recorded emergencies |
| `GET` | `/api/emergencies/{id}` | Retrieve incident facts by ID |
| `GET` | `/api/emergencies/{id}/tracking` | Dynamic responder tracking telemetry (distance, ETA, speed, progress) |
| `WS` | `/ws/emergencies/{id}/tracking` | Real-time WebSocket streaming of live responder position |
| `GET` | `/api/units` | Discover units filtered by type and caller proximity |
| `POST` | `/api/units/{id}/dispatch` | Authoritative unit assignment (with HTTP 409 conflict guardrail) |
| `GET` | `/api/hospitals` | Discover regional hospitals with ICU and bed availability |
| `GET` | `/api/nearby-help` | Unified discovery of nearby hospitals, fire stations, and depots |
| `POST` | `/api/verify` | Python deterministic verification of incident parameters |
| `POST` | `/api/verify/what-if` | Model mutual-aid resource changes & predict shortfall elimination |
| `POST` | `/api/verify/resource-gaps` | Deterministic mathematical calculation of fleet deficits |
| `POST` | `/api/coordinate` | Full loop: MCP discovery → Python verification → Dispatch |
| `POST` | `/api/chat` | AI assistant grounded with dynamic MCP tool retrieval |
| `GET` | `/api/mcp/tools` | Enumerate all 29 registered MCP tools across 9 domains |
| `GET` | `/api/mcp/trace` | Execution trace log with durations and provenance |
| `DELETE`| `/api/mcp/trace` | Clear recorded trace buffer |
| `POST` | `/api/mcp/execute` | Directly invoke any MCP tool by name |
| `GET` | `/api/mcp/location/test` | Diagnostic endpoint for location MCP tools |
| `GET` | `/api/mcp/resource/test` | Diagnostic endpoint for resource discovery MCP tools |
| `GET` | `/api/mcp/hospital/test` | Diagnostic endpoint for hospital capacity MCP tools |
| `GET` | `/api/mcp/verification/test` | Diagnostic endpoint for deterministic verification MCP tools |

---

## 6. Official MCP Tools Catalog (29 Tools across 9 Domains)

All tools are registered on the official `MCPServer("mcp-resq-emergency-server")`:

### 1. Emergency Domain
* `get_emergency_details`: Full incident report, priority, casualties, and status.
* `get_emergency_location`: GPS coordinates, accuracy, and location label.
* `get_emergency_status`: Incident lifecycle state (`detected`, `triaged`, `dispatched`, `resolved`).
* `get_active_emergencies`: Query all unresolved incidents in the operations center.

### 2. Resources Domain
* `get_available_units`: Query available units with spatial proximity and ETA.
* `get_unit_status`: Single unit operational readiness, workload, and assignment.
* `get_unit_location`: GPS coordinates and depot origin.
* `get_resource_capabilities`: Fleet-wide capability discovery (`als`, `hazmat`, `extraction`).
* `find_best_resources`: Deterministic ranking minimizing distance and workload penalties.
* `get_resource_gaps`: Mathematical deficit between required and available units.

### 3. Hospitals Domain
* `get_nearby_hospitals`: Discover facilities sorted by proximity with bed counts.
* `get_hospital_capacity`: Detailed ICU, emergency bed, and surgical readiness.
* `get_hospital_emergency_status`: Check emergency intake readiness (`READY` vs `DIVERT`).
* `get_hospital_capabilities`: Inspect specialized trauma units (burn, cardiac, pediatric).
* `find_best_hospital`: Match critical casualties to highest capable facility.

### 4. Routing Domain
* `calculate_route`: Transit route calculation via Google Routes or Haversine fallback.
* `calculate_eta`: Kinematic travel duration based on speed and traffic density.
* `get_traffic_condition`: Query municipal corridor congestion indices.
* `compare_routes`: Contrast primary arterial route with perimeter highway bypass.

### 5. Safety Domain
* `find_safe_zone`: Nearest verified assembly point with amenities.
* `get_evacuation_points`: Mass civilian evacuation staging areas.
* `get_hazard_zones`: Exclusion zone radius based on chemical plume dispersion.
* `get_nearest_exit`: Perimeter egress vector and escape direction.

### 6. Verification Domain
* `verify_emergency`: Comprehensive deterministic check of incident facts.
* `verify_resource`: Inspect unit availability and GPS coordinate validity.
* `verify_hospital`: Confirm hospital bed readiness and trauma level.
* `verify_dispatch`: Verify dispatch constraints before assignment.
* `validate_response_plan`: Deterministically validate multi-unit deployment plans.

### 7. Dispatch Domain
* `dispatch_unit`: Authoritatively assign unit with 409 conflict prevention.
* `cancel_dispatch`: Recall dispatched responder to available pool.
* `reassign_unit`: Shift incident assignment from one unit to another.
* `get_dispatch_status`: Check current assignment and transit status.
* `get_response_status`: Comprehensive response metrics.

### 8. Tracking Domain
* `get_tracking_status`: Live spatial progress, speed, and ETA telemetry.

### 9. Alerts & Analytics Domain
* `create_alert`: Queue emergency alert in notification core.
* `broadcast_alert`: Transmit alert through distribution channels.
* `get_nearby_recipients`: Estimate devices within geofence radius.
* `send_local_alert`: Send localized mobile advisory within radius.
* `prepare_hospital_alert`: Generate pre-arrival trauma bay intake alert.
* `get_resource_utilization`: Fleet utilization percentage across 10 vehicle types.
* `get_incident_statistics`: Total active and critical incidents summary.
* `get_response_time_statistics`: Fleet transit metrics and 90th percentile ETA.

---

## 7. AI Orchestration & Guardrails

* **File**: `backend/ai.py`
* **Model**: Google Gemini 2.5 Flash (`gemini-2.5-flash`) via the official `google-genai` SDK.
* **Grounding**: Before calling Gemini, the backend retrieves verified context from MCP tools (`get_response_status`, `get_available_units`, `get_nearby_hospitals`, `get_resource_gaps`).
* **Deterministic Fallback**: If `GEMINI_API_KEY` is omitted or an external API error occurs, an intelligent deterministic reasoner synthesizes the exact response grounded in live telemetry.
* **Strict Guardrails**:
  - AI may **reason** over verified facts.
  - AI may **select** tools.
  - AI may **explain** resource choices.
  - AI is **strictly prohibited** from fabricating numerical resource gaps, ETAs, distances, or hospital capacity.

---

## 8. Python Verification Layer

* **File**: `backend/verification.py`
* **Core Rule**:
  > **AI Proposes. Python Verifies. Backend Executes.**
* **Mathematical Verifications**:
  1. **Haversine Distance**: Computes great-circle distance between GPS coordinates:
     $$d = 2r \arcsin\left(\sqrt{\sin^2(\Delta\phi/2) + \cos\phi_1\cos\phi_2\sin^2(\Delta\lambda/2)}\right)$$
  2. **ETA Calculation**: Deterministic calculation based on urban speeds and traffic factors.
  3. **Resource Gap Analysis**: Absolute arithmetic subtraction:
     $$\text{Gap}(T) = \max(0, \text{Required}(T) - \text{Available}(T))$$
  4. **Conflict Prevention**: Rejects dispatch of any unit not currently in `available` state with HTTP 409 Conflict.
  5. **What-If Simulation**: Deterministically recalculates fleet deficits when mutual-aid resources are added or subtracted.

---

## 9. Live Tracking Telemetry

* **REST Polling**: `GET /api/emergencies/{id}/tracking` returns distance, ETA, speed, and percentage progress.
* **WebSocket Streaming**: `/ws/emergencies/{id}/tracking` pushes telemetry frames every 3 seconds.
* **Kinematic Simulation**: Updates progress vector ($15\% \to 30\% \to 48\% \to 65\% \to 80\% \to 92\% \to 100\%$) and marks unit `on_scene` upon arrival.
* **Provenance**: Every payload is labeled `SIMULATED LIVE TRACKING`.

---

## 10. Automated Test Suite

All 27 automated tests are consolidated into `backend/tests.py`:

```bash
PYTHONPATH=. pytest backend/tests.py -v
```

### Coverage Summary:
* ✅ `test_health_endpoint`: Operational status and verification engine check.
* ✅ `test_create_emergency_success`: Incident creation and auto-coordination.
* ✅ `test_create_emergency_validation_failure`: Short description validation.
* ✅ `test_list_and_get_emergencies`: Incident retrieval and serialization.
* ✅ `test_get_emergency_not_found`: 404 error contract.
* ✅ `test_get_units_listing_and_filtering`: Fleet discovery and proximity calculation.
* ✅ `test_dispatch_unit_success`: Authoritative dispatch assignment.
* ✅ `test_dispatch_conflict_prevention`: HTTP 409 on already-dispatched unit.
* ✅ `test_get_hospitals_and_capacity`: Hospital ICU and bed status.
* ✅ `test_get_nearby_help`: Ranked emergency infrastructure discovery.
* ✅ `test_tracking_rest_endpoint`: Live tracking telemetry.
* ✅ `test_tracking_not_found`: 404 for undispatched emergency.
* ✅ `test_tracking_websocket`: WebSocket telemetry streaming.
* ✅ `test_coordinate_verification`: Coordinate bounds verification.
* ✅ `test_haversine_and_eta_math`: Deterministic mathematical calculations.
* ✅ `test_verify_incident_endpoint`: Incident verification endpoint.
* ✅ `test_resource_gaps_calculation`: Mathematical gap analysis.
* ✅ `test_what_if_simulation_endpoint`: What-if capacity modeling.
* ✅ `test_coordination_cycle`: End-to-end incident coordination.
* ✅ `test_ai_chat_deterministic_fallback`: Grounded AI responses.
* ✅ `test_ai_chat_why_selected`: Explainable resource selection.
* ✅ `test_ai_chat_empty_message`: 400 validation error on empty message.
* ✅ `test_mcp_tools_listing`: Registered MCP tools check.
* ✅ `test_mcp_traces_endpoint`: Observability trace buffer logging.
* ✅ `test_mcp_test_endpoints`: Diagnostic endpoints for all domains.
* ✅ `test_mcp_direct_execute_endpoint`: Direct tool execution via POST.
* ✅ `test_alert_service`: Alert creation, broadcast, and listing.

---

## 11. Security & Disclaimers

1. **Life-Safety Disclaimer**: MCP-ResQ is an engineering decision-support prototype. It does **NOT** autonomously dispatch real-world emergency responders or replace municipal 911 / 112 emergency services.
2. **Synthetic Data**: All responder units, telemetry, and hospital capacities are synthetic demo records clearly marked with provenance tags.
3. **Secret Protection**: API keys (Gemini, Google Maps) are strictly kept server-side and accessed via environment variables.
4. **SQL Injection Protection**: All database queries are executed via SQLAlchemy ORM parameterized queries.
5. **CORS & Input Validation**: Strict CORS origins and robust Pydantic v2 schemas reject malformed or malicious payloads.
