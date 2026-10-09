"""FastAPI application entrypoint for MCP-ResQ Emergency Decision Support Platform.

Consolidated backend service hosting REST APIs, WebSocket live tracking,
MCP diagnostics, AI orchestration, and deterministic verification.
"""

import asyncio
from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load environment configuration from root .env
load_dotenv()

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.ai import handle_ai_chat
from backend.database import SessionLocal, get_db
from backend.mcp import (
    MCP_TOOL_REGISTRY,
    call_mcp_tool,
    global_mcp_tracer,
    mcp_emergency_server,
)
from backend.models import (
    AuditLogEntry,
    ChatRequest,
    ChatResponse,
    ConfigResponse,
    CoordinationRequest,
    CoordinationResponse,
    DispatchRequest,
    DispatchResponse,
    Emergency,
    EmergencyCreateRequest,
    EmergencyResponse,
    EmergencyUnit,
    HospitalResponse,
    LocationSchema,
    NearbyHelpItem,
    ResourceGapRequest,
    SimulationControlRequest,
    SimulationControlResponse,
    ToolExecuteRequest,
    TrackingResponse,
    UnitResponse,
    VerificationRequest,
    VerificationResponse,
    WhatIfRequest,
)
from backend.services import (
    CoordinationService,
    EmergencyService,
    HospitalService,
    NearbyService,
    ResourceService,
    RoutingService,
    TrackingService,
    global_audit_logger,
    global_simulation_engine,
)
from backend.verification import (
    calculate_resource_gaps,
    run_verification,
    run_what_if_simulation,
)
from data.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    # Seed database with synthetic 10-role fleet, facilities, and scenarios
    seed_database()
    yield


app = FastAPI(
    title="MCP-ResQ",
    description="AI-Powered Emergency Resource Coordination using Model Context Protocol (MCP)",
    version="1.0.0",
    lifespan=lifespan,
)

# ----------------------------------------------------------------------------
# CORS Configuration
# ----------------------------------------------------------------------------
allowed_origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
if not allowed_origins:
    allowed_origins = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if os.getenv("APP_ENV") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
# Global Error Handler
# ----------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path,
        },
    )


# ----------------------------------------------------------------------------
# Health Endpoint
# ----------------------------------------------------------------------------
@app.get("/api/health", tags=["Health"])
def health_check():
    """Return backend operational status."""
    return {
        "status": "ok",
        "service": "MCP-ResQ",
        "backend": "FastAPI",
        "version": "1.0.0",
        "mcp_enabled": True,
        "verification_engine": "Python Deterministic",
    }


# ----------------------------------------------------------------------------
# Emergency Incidents Endpoints
# ----------------------------------------------------------------------------
@app.post("/api/emergencies", response_model=EmergencyResponse, status_code=status.HTTP_201_CREATED, tags=["Emergencies"])
def create_emergency_endpoint(request: EmergencyCreateRequest, db: Session = Depends(get_db)):
    """Create a new emergency incident and trigger initial coordination."""
    if not request.description or len(request.description.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emergency description must be at least 3 characters long.",
        )

    emergency = EmergencyService.create_emergency(db, request)

    # Automatically trigger coordination to attempt immediate resource assignment
    try:
        CoordinationService.coordinate_emergency(db, emergency.id)
        db.refresh(emergency)
    except Exception:
        pass

    return EmergencyResponse(
        id=emergency.id,
        type=emergency.type,
        priority=emergency.priority,
        severity=emergency.severity or "HIGH",
        status=emergency.status,
        description=emergency.description,
        latitude=emergency.latitude,
        longitude=emergency.longitude,
        location=LocationSchema(
            latitude=emergency.latitude,
            longitude=emergency.longitude,
            accuracy=emergency.accuracy or 10.0,
        ),
        assigned_unit_id=emergency.assigned_unit_id,
        assigned_hospital_id=emergency.assigned_hospital_id,
        created_at=emergency.created_at.isoformat() if hasattr(emergency.created_at, "isoformat") else str(emergency.created_at or ""),
    )


@app.get("/api/emergencies", response_model=List[EmergencyResponse], tags=["Emergencies"])
def get_all_emergencies(db: Session = Depends(get_db)):
    """List all recorded emergency incidents."""
    emergencies = EmergencyService.list_emergencies(db)
    return [
        EmergencyResponse(
            id=e.id,
            type=e.type,
            priority=e.priority,
            severity=e.severity or "HIGH",
            status=e.status,
            description=e.description,
            latitude=e.latitude,
            longitude=e.longitude,
            location=LocationSchema(
                latitude=e.latitude,
                longitude=e.longitude,
                accuracy=e.accuracy or 10.0,
            ),
            assigned_unit_id=e.assigned_unit_id,
            assigned_hospital_id=e.assigned_hospital_id,
            created_at=e.created_at.isoformat() if hasattr(e.created_at, "isoformat") else str(e.created_at or ""),
        )
        for e in emergencies
    ]


@app.get("/api/emergencies/{id}", response_model=EmergencyResponse, tags=["Emergencies"])
def get_emergency_by_id(id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific emergency incident."""
    emergency = EmergencyService.get_emergency(db, id)
    if not emergency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency '{id}' not found.",
        )

    return EmergencyResponse(
        id=emergency.id,
        type=emergency.type,
        priority=emergency.priority,
        severity=emergency.severity or "HIGH",
        status=emergency.status,
        description=emergency.description,
        latitude=emergency.latitude,
        longitude=emergency.longitude,
        location=LocationSchema(
            latitude=emergency.latitude,
            longitude=emergency.longitude,
            accuracy=emergency.accuracy or 10.0,
        ),
        assigned_unit_id=emergency.assigned_unit_id,
        assigned_hospital_id=emergency.assigned_hospital_id,
        created_at=emergency.created_at.isoformat() if hasattr(emergency.created_at, "isoformat") else str(emergency.created_at or ""),
    )


# ----------------------------------------------------------------------------
# System Configuration & Secret Status Endpoints
# ----------------------------------------------------------------------------
@app.get("/api/config", response_model=ConfigResponse, tags=["Configuration"])
def get_system_config():
    """Client configuration endpoint exposing browser maps key and dev connection statuses."""
    single_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    browser_key = (os.getenv("GOOGLE_MAPS_BROWSER_KEY") or single_key or os.getenv("GOOGLE_MAPS_SERVER_KEY") or "").strip()
    server_key = (os.getenv("GOOGLE_MAPS_SERVER_KEY") or single_key or browser_key).strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    twilio_tok = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    app_env = os.getenv("APP_ENV", "development")

    return ConfigResponse(
        google_maps_browser_key=browser_key,
        google_maps_map_id=os.getenv("GOOGLE_MAPS_MAP_ID", ""),
        app_env=app_env,
        dev_mode=(app_env != "production"),
        status={
            "google_maps_browser_key": "CONNECTED" if bool(browser_key) else "MISSING",
            "google_maps_server_key": "CONNECTED" if bool(server_key) else "MISSING",
            "gemini_api_key": "CONNECTED" if bool(gemini_key) else "MISSING",
            "twilio_configured": "CONNECTED" if bool(twilio_sid and twilio_tok) else "MISSING",
        },
    )


# ----------------------------------------------------------------------------
# Maps & Routes Endpoints
# ----------------------------------------------------------------------------
class RouteCalculationRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    origin_name: str = "Depot"
    dest_name: str = "Scene"


@app.post("/api/routes/calculate", tags=["Maps & Routing"])
def calculate_route_endpoint(req: RouteCalculationRequest):
    """Calculate traffic-aware road route using Google Routes API or deterministic road geometry fallback."""
    return RoutingService.calculate_route(
        origin_lat=req.origin_lat,
        origin_lng=req.origin_lng,
        dest_lat=req.dest_lat,
        dest_lng=req.dest_lng,
        origin_name=req.origin_name,
        dest_name=req.dest_name,
    )


# ----------------------------------------------------------------------------
# Tracking Endpoints (REST & WebSocket)
# ----------------------------------------------------------------------------
@app.get("/api/emergencies/{id}/tracking", response_model=TrackingResponse, tags=["Tracking"])
def get_emergency_tracking(id: str, db: Session = Depends(get_db)):
    """Retrieve dynamic tracking coordinates, distance, ETA, and progress for an active emergency."""
    tracking_data = TrackingService.get_tracking(db, emergency_id=id)
    if not tracking_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No tracking data available for emergency '{id}'. Unit may not yet be dispatched.",
        )
    return TrackingResponse(**tracking_data)


@app.post("/api/emergencies/{id}/simulation/control", response_model=SimulationControlResponse, tags=["Simulation"])
def control_simulation_endpoint(id: str, request: SimulationControlRequest, db: Session = Depends(get_db)):
    """Operator simulation control: pause, resume, restart, set_speed, set_multiplier."""
    action = request.action.lower()
    state = global_simulation_engine.get_state(id)
    if not state:
        TrackingService.get_tracking(db, emergency_id=id)
        state = global_simulation_engine.get_state(id)

    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No active simulation found for emergency '{id}'.")

    if action == "pause":
        global_simulation_engine.pause(id)
    elif action == "resume":
        global_simulation_engine.resume(id)
    elif action == "restart":
        global_simulation_engine.restart(id)
    elif action == "set_speed":
        if request.speed_kmh is None:
            raise HTTPException(status_code=400, detail="Missing 'speed_kmh' in request.")
        global_simulation_engine.set_speed(id, request.speed_kmh)
    elif action == "set_multiplier":
        if request.multiplier is None:
            raise HTTPException(status_code=400, detail="Missing 'multiplier' in request.")
        global_simulation_engine.set_multiplier(id, request.multiplier)
    elif action == "step":
        global_simulation_engine.advance(db, id, dt_seconds=1.5)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown simulation action '{action}'.")

    curr = global_simulation_engine.get_state(id) or state
    raw_sim = global_simulation_engine._states.get(id)
    reported_speed = raw_sim.speed_kmh if raw_sim else curr.get("speed_kmh", 50.0)
    return SimulationControlResponse(
        success=True,
        emergency_id=id,
        action=action,
        is_paused=curr.get("is_paused", False),
        speed_kmh=float(reported_speed),
        multiplier=curr.get("speed_multiplier", 1.0),
        status=curr.get("status", "en_route"),
        progress=float(curr.get("progress", 15.0)),
        message=f"Simulation action '{action}' applied successfully.",
    )


@app.get("/api/emergencies/{id}/audit", tags=["Audit"])
def get_emergency_audit_trail(id: str):
    """Retrieve chronological event audit trail for an emergency."""
    entries = global_audit_logger.get_entries(emergency_id=id, limit=50)
    return {"emergency_id": id, "total": len(entries), "audit_trail": entries}


@app.get("/api/audit/recent", tags=["Audit"])
def get_recent_audit_trail(limit: int = Query(50, ge=1, le=200)):
    """Retrieve system-wide chronological event audit trail for operator control centre."""
    entries = global_audit_logger.get_entries(limit=limit)
    return {"total": len(entries), "audit_trail": entries}


@app.websocket("/ws/emergencies/{emergency_id}/tracking")
async def tracking_websocket(websocket: WebSocket, emergency_id: str):
    """Real-time WebSocket streaming of live responder telemetry updates."""
    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            try:
                tracking_data = TrackingService.get_tracking(db, emergency_id=emergency_id)
                if tracking_data:
                    payload = TrackingResponse(**tracking_data).model_dump(by_alias=True)
                    payload["event"] = "tracking_update"
                    await websocket.send_json(payload)
                else:
                    await websocket.send_json({
                        "event": "waiting_dispatch",
                        "emergency_id": emergency_id,
                        "message": "Awaiting resource dispatch...",
                        "data_status": "SIMULATED LIVE TRACKING",
                        "data_source": "DEMO SIMULATION",
                    })
            finally:
                db.close()

            # Responsive 1.5s live streaming tick
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


# ----------------------------------------------------------------------------
# Operator Authorization & Control Centre Serving
# ----------------------------------------------------------------------------
def is_authorized_operator(request: Request) -> bool:
    """Validate operator/dev authentication via token query, header, or cookie."""
    expected_token = os.getenv("DEV_OPERATOR_TOKEN", "resq-operator-secure-2026")
    if request.headers.get("X-Operator-Token") == expected_token:
        return True
    if request.query_params.get("token") == expected_token:
        return True
    if request.cookies.get("resq_operator_token") == expected_token:
        return True
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and auth_header[7:].strip() == expected_token:
        return True
    return False


@app.get("/control-centre", response_class=HTMLResponse, tags=["Operator Control Centre"])
@app.get("/control-centre/", response_class=HTMLResponse, tags=["Operator Control Centre"])
@app.get("/control-centre.html", response_class=HTMLResponse, tags=["Operator Control Centre"])
@app.get("/control-center", response_class=HTMLResponse, tags=["Operator Control Centre"])
@app.get("/control-center/", response_class=HTMLResponse, tags=["Operator Control Centre"])
@app.get("/control-center.html", response_class=HTMLResponse, tags=["Operator Control Centre"])
def get_control_centre(request: Request):
    """Dev-only Operator Control Centre protected by backend token authorization."""
    token_param = request.query_params.get("token")
    expected_token = os.getenv("DEV_OPERATOR_TOKEN", "resq-operator-secure-2026")

    if token_param == expected_token or is_authorized_operator(request):
        control_centre_file = project_root / "control-centre.html"
        if not control_centre_file.exists():
            return HTMLResponse("<h1>Control Centre initializing...</h1>", status_code=200)
        content = control_centre_file.read_text(encoding="utf-8")
        response = HTMLResponse(content, status_code=200)
        response.set_cookie(
            key="resq_operator_token",
            value=expected_token,
            httponly=False,
            samesite="lax",
            max_age=86400,
        )
        return response

    gate_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MCP-ResQ — Operator Control Centre Authentication</title>
  <link rel="stylesheet" href="/style.css">
  <style>
    body {{
      background: #090d16;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
    }}
    .auth-card {{
      background: #111827;
      border: 1px solid #374151;
      border-radius: 12px;
      padding: 2.5rem;
      width: 100%;
      max-width: 440px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
      text-align: center;
    }}
    .badge {{
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      background: rgba(239, 68, 68, 0.2);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.4);
      margin-bottom: 1rem;
    }}
    h1 {{ font-size: 1.5rem; margin: 0 0 0.5rem 0; color: #f8fafc; }}
    p {{ color: #94a3b8; font-size: 0.875rem; margin-bottom: 1.5rem; line-height: 1.5; }}
    .form-group {{ margin-bottom: 1.25rem; text-align: left; }}
    label {{ display: block; font-size: 0.75rem; text-transform: uppercase; color: #94a3b8; margin-bottom: 0.5rem; }}
    input {{
      width: 100%;
      box-sizing: border-box;
      padding: 0.75rem 1rem;
      background: #1f2937;
      border: 1px solid #4b5563;
      border-radius: 8px;
      color: #f8fafc;
      font-family: monospace;
      font-size: 0.95rem;
    }}
    input:focus {{ outline: none; border-color: #3b82f6; }}
    button {{
      width: 100%;
      padding: 0.75rem;
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }}
    button:hover {{ background: #1d4ed8; }}
    .hint {{ margin-top: 1rem; font-size: 0.75rem; color: #64748b; }}
  </style>
</head>
<body>
  <div class="auth-card">
    <div class="badge">Restricted Access</div>
    <h1>Operator Control Centre</h1>
    <p>This terminal is reserved for emergency coordinators and authorized DEV operators. Enter your access token to continue.</p>
    <form onsubmit="handleAuth(event)">
      <div class="form-group">
        <label for="tokenInput">Operator Secret Key</label>
        <input type="password" id="tokenInput" placeholder="Enter DEV_OPERATOR_TOKEN" required autofocus>
      </div>
      <button type="submit">Unlock Control Centre</button>
    </form>
    <div class="hint">Development default: <code>resq-operator-secure-2026</code></div>
  </div>
  <script>
    function handleAuth(e) {{
      e.preventDefault();
      const token = document.getElementById('tokenInput').value.trim();
      if (!token) return;
      document.cookie = 'resq_operator_token=' + token + '; path=/; max-age=86400; SameSite=Lax';
      window.location.href = '/control-centre?token=' + encodeURIComponent(token);
    }}
  </script>
</body>
</html>"""
    return HTMLResponse(gate_html, status_code=401)


# ----------------------------------------------------------------------------
# Responder Units & Dispatch Endpoints
# ----------------------------------------------------------------------------
@app.get("/api/units", response_model=List[UnitResponse], tags=["Units"])
def get_units_endpoint(
    type: Optional[str] = Query(None, description="Filter by unit type (ambulance, fire, rescue, police)"),
    latitude: Optional[float] = Query(None, description="Caller latitude for proximity calculation"),
    longitude: Optional[float] = Query(None, description="Caller longitude for proximity calculation"),
    db: Session = Depends(get_db),
):
    """Retrieve emergency resource units with live operational status."""
    return ResourceService.list_units(db, unit_type=type, latitude=latitude, longitude=longitude)


@app.post("/api/units/{id}/dispatch", response_model=DispatchResponse, tags=["Units"])
def dispatch_unit_endpoint(
    id: str,
    request: DispatchRequest,
    db: Session = Depends(get_db),
):
    """Dispatch an emergency unit to a specified emergency."""
    result = ResourceService.dispatch_unit(db, unit_id=id, emergency_id=request.emergency_id)
    if not result.get("success"):
        code = result.get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=code, detail=result.get("error", "Dispatch failed."))

    return DispatchResponse(
        success=True,
        unit_id=result["unit_id"],
        emergency_id=result["emergency_id"],
        status=result["status"],
        eta_minutes=result["eta_minutes"],
        message=result.get("message"),
    )


# ----------------------------------------------------------------------------
# Hospitals & Nearby Services Endpoints
# ----------------------------------------------------------------------------
@app.get("/api/hospitals", response_model=List[HospitalResponse], tags=["Hospitals"])
def get_hospitals_endpoint(
    latitude: Optional[float] = Query(None, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, description="Longitude coordinate"),
    db: Session = Depends(get_db),
):
    """Retrieve list of medical facilities with distance, bed, and ICU status."""
    return HospitalService.list_hospitals(db, latitude=latitude, longitude=longitude)


@app.get("/api/nearby-help", response_model=List[NearbyHelpItem], tags=["Nearby Help"])
def get_nearby_help_endpoint(
    latitude: Optional[float] = Query(None, description="Current user latitude"),
    longitude: Optional[float] = Query(None, description="Current user longitude"),
    db: Session = Depends(get_db),
):
    """Retrieve nearby hospitals, fire stations, and emergency bases."""
    return NearbyService.list_nearby_help(db, latitude=latitude, longitude=longitude)


# ----------------------------------------------------------------------------
# Verification & What-If Simulation Endpoints
# ----------------------------------------------------------------------------
@app.post("/api/verify", response_model=VerificationResponse, tags=["Verification"])
def verify_incident_endpoint(
    request: VerificationRequest,
    db: Session = Depends(get_db),
):
    """Execute Python deterministic verification on incident parameters."""
    result = run_verification(
        db=db,
        emergency_id=request.emergency_id,
        emergency_type=request.emergency_type,
        location=request.location,
    )
    return VerificationResponse(**result)


@app.post("/api/verify/what-if", tags=["Verification"])
def simulate_what_if_endpoint(
    request: WhatIfRequest,
    db: Session = Depends(get_db),
):
    """Execute deterministic What-If scenario simulation."""
    return run_what_if_simulation(
        db=db,
        scenario=request.scenario,
        params=request.parameters or {},
    )


@app.post("/api/verify/resource-gaps", tags=["Verification"])
def resource_gaps_endpoint(
    request: ResourceGapRequest,
    db: Session = Depends(get_db),
):
    """Compute mathematical resource gaps."""
    avail = request.available
    if avail is None:
        units = db.query(EmergencyUnit).filter(EmergencyUnit.status == "available").all()
        avail = {}
        for u in units:
            avail[u.type] = avail.get(u.type, 0) + 1

    return {
        "verified_by_python": True,
        "gaps": calculate_resource_gaps(request.required, avail),
    }


@app.post("/api/simulate-change", tags=["Verification"])
def simulate_change_alias(
    request: WhatIfRequest,
    db: Session = Depends(get_db),
):
    """Alias for backwards compatibility with earlier What-If interfaces."""
    return run_what_if_simulation(
        db=db,
        scenario=request.scenario,
        params=request.parameters or {},
    )


# ----------------------------------------------------------------------------
# Coordination Endpoint
# ----------------------------------------------------------------------------
@app.post("/api/coordinate", response_model=CoordinationResponse, tags=["Coordination"])
def coordinate_incident_endpoint(
    request: CoordinationRequest,
    db: Session = Depends(get_db),
):
    """Run full coordination cycle: MCP discovery -> Python verification -> Dispatch."""
    result = CoordinationService.coordinate_emergency(db, emergency_id=request.emergency_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Coordination failed."),
        )

    return CoordinationResponse(
        success=True,
        emergency_id=result["emergency_id"],
        resources=result["resources"],
        hospital=result.get("hospital"),
        verification=result["verification"],
        summary=result["summary"],
    )


# ----------------------------------------------------------------------------
# AI Assistant Chat Endpoint
# ----------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse, tags=["AI Assistant"])
def ai_chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Process natural language emergency queries using MCP tools and Gemini reasoning."""
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat message cannot be empty.",
        )

    result = handle_ai_chat(
        db=db,
        message=request.message.strip(),
        emergency_id=request.emergency_id,
        history=request.history,
    )
    return ChatResponse(**result)


# ----------------------------------------------------------------------------
# MCP Diagnostics & Tool Endpoints
# ----------------------------------------------------------------------------
@app.get("/api/mcp/trace", tags=["MCP Tools Diagnostics"])
def get_mcp_traces(limit: int = Query(50, ge=1, le=200)):
    """Retrieve recent MCP execution trace log for judges & operators."""
    traces = global_mcp_tracer.get_recent_traces(limit=limit)
    return {
        "status": "success",
        "total_recorded": len(traces),
        "traces": traces,
    }


@app.delete("/api/mcp/trace", tags=["MCP Tools Diagnostics"])
def clear_mcp_traces():
    """Clear recorded MCP execution traces."""
    global_mcp_tracer.clear()
    return {"status": "success", "message": "Execution trace buffer cleared"}


@app.get("/api/mcp/tools", tags=["MCP Tools Diagnostics"])
def list_mcp_tools():
    """List all registered MCP tools across 9 domains."""
    tools_list = []
    for name in MCP_TOOL_REGISTRY.keys():
        tools_list.append({
            "name": name,
            "server": mcp_emergency_server.name,
        })
    return {
        "total_tools": len(tools_list),
        "server": mcp_emergency_server.name,
        "tools": tools_list,
    }


@app.post("/api/mcp/execute", tags=["MCP Tools Diagnostics"])
def execute_tool_endpoint(req: ToolExecuteRequest):
    """Directly execute any registered MCP tool by name."""
    try:
        res = call_mcp_tool(req.tool, **req.arguments)
        return {
            "tool": req.tool,
            "status": "success",
            "result": res,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/mcp/location/test", tags=["MCP Tools Diagnostics"])
def test_location_mcp():
    """Test MCP location tool with synthetic coordinates."""
    res = call_mcp_tool("get_unit_location", unit_id="AMB-101")
    return {
        "tool": "get_unit_location",
        "status": "success",
        "result": res,
    }


@app.get("/api/mcp/resource/test", tags=["MCP Tools Diagnostics"])
def test_resource_mcp():
    """Test MCP resource tool discovering available emergency units."""
    res = call_mcp_tool("get_available_units", unit_type="ambulance", latitude=12.9716, longitude=77.5946)
    return {
        "tool": "get_available_units",
        "status": "success",
        "result": res,
    }


@app.get("/api/mcp/hospital/test", tags=["MCP Tools Diagnostics"])
def test_hospital_mcp():
    """Test MCP hospital tool evaluating capacity."""
    res = call_mcp_tool("get_hospital_capacity", hospital_id="H-101")
    return {
        "tool": "get_hospital_capacity",
        "status": "success",
        "result": res,
    }


@app.get("/api/mcp/verification/test", tags=["MCP Tools Diagnostics"])
def test_verification_mcp():
    """Test MCP verification tool on mock coordinates."""
    res = call_mcp_tool("verify_emergency", emergency_id="EMG-1001")
    return {
        "tool": "verify_emergency",
        "status": "success",
        "result": res,
    }


# ----------------------------------------------------------------------------
# SPA Routes Fallback for Direct Browser Navigation & Refresh
# ----------------------------------------------------------------------------
@app.get("/tracking", response_class=HTMLResponse, include_in_schema=False)
@app.get("/emergency", response_class=HTMLResponse, include_in_schema=False)
@app.get("/chat", response_class=HTMLResponse, include_in_schema=False)
@app.get("/nearby", response_class=HTMLResponse, include_in_schema=False)
@app.get("/control", response_class=HTMLResponse, include_in_schema=False)
@app.get("/mcp", response_class=HTMLResponse, include_in_schema=False)
@app.get("/verification", response_class=HTMLResponse, include_in_schema=False)
def get_spa_page(request: Request):
    """Serve index.html for direct client-side routes on refresh or direct URL entry."""
    index_file = project_root / "index.html"
    if index_file.exists():
        return HTMLResponse(index_file.read_text(encoding="utf-8"), status_code=200)
    raise HTTPException(status_code=404, detail="Frontend index.html not found.")


# ----------------------------------------------------------------------------
# Frontend Static Files Serving
# ----------------------------------------------------------------------------
# Serve static files from root if index.html is present in root, or from frontend/
project_root = Path(__file__).resolve().parent.parent
frontend_dir = project_root / "frontend"

if (project_root / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(project_root), html=True), name="root_frontend")
elif frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
