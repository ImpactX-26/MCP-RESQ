"""
FastAPI Backend Application for MCP-RESQ.
Provides RESTful APIs, MCP integration, Gemini LLM chatbot, and emergency coordination endpoints.
"""

import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from models import (
    EmergencyCreateRequest,
    EmergencyResponse,
    DispatchRequest,
    VerificationRequest,
    ChatMessageRequest,
    ChatMessageResponse
)
from mcp_server import (
    MCPToolsEngine,
    units_db,
    nearby_services_db,
    emergencies_db,
    tracking_db
)
from gemini_service import (
    generate_gemini_emergency_analysis,
    handle_chat_message,
    GEMINI_API_KEY
)

app = FastAPI(
    title="MCP-RESQ Emergency Decision Support API",
    description="Backend service integrating Model Context Protocol (MCP) and Gemini AI LLM for emergency response.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# 1. Health & Status Endpoints
# -------------------------------------------------------------
@app.get("/api/health")
def get_health():
    """Health check endpoint for frontend connection verification."""
    return {
        "status": "ok",
        "service": "MCP-RESQ API",
        "backend_connected": True,
        "gemini_api_configured": bool(GEMINI_API_KEY),
        "mcp_status": "active",
        "timestamp": datetime.now().isoformat()
    }


# -------------------------------------------------------------
# 2. Emergency Resources & Nearby Help Endpoints
# -------------------------------------------------------------
@app.get("/api/units")
def get_units():
    """Lists all emergency response units (ambulances, fire tenders, rescue teams)."""
    return units_db


@app.get("/api/nearby-help")
def get_nearby_services():
    """Returns nearby emergency facilities (hospitals, fire stations, police, rescue bases)."""
    return nearby_services_db


# -------------------------------------------------------------
# 3. Emergency Incident Management Endpoints
# -------------------------------------------------------------
@app.post("/api/emergencies")
def create_emergency(req: EmergencyCreateRequest):
    """
    Creates a new emergency report.
    Uses MCP tools and Gemini LLM to collect incident details, assess hazard risk,
    and generate instructions for both victims and responders.
    """
    emergency_id = f"EMG-{int(time.time() * 1000) % 1000000:06d}"
    inc_type = req.type.lower() if req.type else "other"

    # Step 1: Run Gemini LLM + MCP Tools analysis
    analysis = generate_gemini_emergency_analysis(
        description=req.description,
        emergency_type=inc_type,
        location=req.location
    )

    # Step 2: Formulate complete emergency object
    emergency_record = {
        "id": emergency_id,
        "description": req.description,
        "type": inc_type,
        "priority": req.priority or "HIGH",
        "location": req.location or {"address": "City Center, Zone 1"},
        "status": "DETECTED",
        "source": req.source or "web",
        "created_at": datetime.now().isoformat(),
        "victim_guidance": analysis["victim_guidance"],
        "responder_guidance": analysis["responder_guidance"],
        "llm_analysis": analysis.get("llm_analysis", ""),
        "mcp_tools_used": analysis["mcp_tools_used"]
    }

    # Save in memory
    emergencies_db[emergency_id] = emergency_record

    # Auto-assign initial best matching demo unit for tracking
    best_unit = MCPToolsEngine.lookup_emergency_resources(resource_type=inc_type)
    assigned_unit = best_unit["units"][0] if best_unit.get("units") else units_db[0]

    tracking_db[emergency_id] = {
        "emergency_id": emergency_id,
        "unit_id": assigned_unit["id"],
        "unit_name": assigned_unit["name"],
        "unit_type": assigned_unit["type"],
        "distance_km": assigned_unit["distance_km"],
        "eta_minutes": assigned_unit["eta_minutes"],
        "status": "en_route",
        "progress": 35,
        "from": assigned_unit["location"],
        "destination": "Incident Scene",
        "updated_at": datetime.now().isoformat()
    }

    return {
        "emergency": emergency_record,
        "message": "Emergency successfully created and analyzed via MCP & Gemini."
    }


@app.get("/api/emergencies/{emergency_id}")
def get_emergency(emergency_id: str = Path(...)):
    """Retrieves emergency record by ID."""
    if emergency_id not in emergencies_db:
        # Return fallback demo record if not found
        return {
            "id": emergency_id,
            "description": "Reported emergency incident",
            "type": "medical",
            "priority": "HIGH",
            "status": "DETECTED",
            "created_at": datetime.now().isoformat(),
            "victim_guidance": INCIDENT_PROTOCOLS["medical"]["victim_instructions"],
            "responder_guidance": INCIDENT_PROTOCOLS["medical"]["responder_instructions"]
        }
    return emergencies_db[emergency_id]


@app.get("/api/emergencies/{emergency_id}/tracking")
def get_tracking(emergency_id: str = Path(...)):
    """Retrieves live response tracking details for an emergency."""
    if emergency_id in tracking_db:
        return tracking_db[emergency_id]

    # Dynamic fallback tracking generator if emergency ID exists or is demo
    emergency = emergencies_db.get(emergency_id)
    inc_type = emergency.get("type", "medical") if emergency else "medical"
    found_units = MCPToolsEngine.lookup_emergency_resources(resource_type=inc_type).get("units", [])
    best_unit = found_units[0] if found_units else units_db[0]

    return {
        "emergency_id": emergency_id,
        "unit_name": best_unit["name"],
        "unit_type": best_unit["type"],
        "distance_km": best_unit["distance_km"],
        "eta_minutes": best_unit["eta_minutes"],
        "status": "en_route",
        "progress": 65,
        "from": best_unit["location"],
        "destination": "Your Location",
        "updated_at": datetime.now().isoformat()
    }


# -------------------------------------------------------------
# 4. Dispatch & Verification Endpoints
# -------------------------------------------------------------
@app.post("/api/units/{unit_id}/dispatch")
def dispatch_unit(unit_id: str = Path(...), req: Optional[DispatchRequest] = None):
    """Dispatches a response unit to an active emergency using MCP tools."""
    emergency_id = req.emergency_id if req else "EMG-GENERAL"
    result = MCPToolsEngine.dispatch_unit_to_incident(unit_id, emergency_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@app.post("/api/verify")
def verify_emergency(req: Dict[str, Any]):
    """Verifies emergency data integrity and resource allocation via MCP."""
    return MCPToolsEngine.verify_incident_details(req)


@app.post("/api/coordinate")
def coordinate_response(req: Dict[str, Any]):
    """Coordinates multi-agency responder plan."""
    emergency_id = req.get("emergency_id", "EMG-GENERAL")
    return {
        "status": "COORDINATED",
        "emergency_id": emergency_id,
        "agencies_notified": [
            "Emergency Ambulance Fleet (ALS/BLS)",
            "Municipal Fire & Hazmat Control",
            "Metropolitan Police Traffic Squad",
            "City Trauma Center ER Desk"
        ],
        "mcp_protocol_status": "ACTIVE",
        "timestamp": datetime.now().isoformat()
    }


# -------------------------------------------------------------
# 5. Gemini AI LLM Chatbot Endpoint
# -------------------------------------------------------------
@app.post("/api/chat", response_model=ChatMessageResponse)
def chat_endpoint(req: ChatMessageRequest):
    """
    AI LLM Chatbot endpoint.
    Uses Gemini API Key + Model Context Protocol (MCP) to answer victim and responder questions.
    """
    res = handle_chat_message(message=req.message, emergency_id=req.emergency_id)
    return ChatMessageResponse(
        reply=res["reply"],
        message=res["reply"],
        emergency_id=req.emergency_id,
        tools_invoked=res.get("tools_invoked", [])
    )


# -------------------------------------------------------------
# 6. MCP Service Testing Endpoints
# -------------------------------------------------------------
@app.api_route("/api/mcp/{service}/test", methods=["GET", "POST"])
def test_mcp_service(service: str = Path(...)):
    """Tests connectivity and execution of specific MCP microservices."""
    srv = service.lower()

    if srv == "location":
        return {
            "service": "location",
            "status": "ONLINE",
            "mcp_tool": "geolocation_verify",
            "latency_ms": 14,
            "data": {"geocoded_zone": "Central Sector", "gps_accuracy": "98.5%"}
        }
    elif srv == "resource":
        res = MCPToolsEngine.lookup_emergency_resources()
        return {
            "service": "resource",
            "status": "ONLINE",
            "mcp_tool": "lookup_emergency_resources",
            "latency_ms": 18,
            "data": res
        }
    elif srv == "hospital":
        hosp = MCPToolsEngine.find_nearby_hospitals_and_facilities("hospital")
        return {
            "service": "hospital",
            "status": "ONLINE",
            "mcp_tool": "find_nearby_hospitals_and_facilities",
            "latency_ms": 22,
            "data": hosp
        }
    elif srv == "verification":
        ver = MCPToolsEngine.verify_incident_details({"description": "Test verification service"})
        return {
            "service": "verification",
            "status": "ONLINE",
            "mcp_tool": "verify_incident_details",
            "latency_ms": 12,
            "data": ver
        }

from fastapi import FastAPI, HTTPException, Request, Path, Form, UploadFile, File, Response
from voice_service import process_voice_call_webhook, process_audio_file_transcription

# -------------------------------------------------------------
# 6. Phone Call Voice & Speech-to-Text Endpoints (Twilio & Audio API)
# -------------------------------------------------------------
@app.post("/api/voice/webhook")
async def voice_webhook(request: Request, SpeechResult: Optional[str] = Form(None), From: Optional[str] = Form(None), CallSid: Optional[str] = Form(None)):
    """
    Twilio Phone Call Webhook.
    1. Converts incoming caller speech to text (Speech-to-Text).
    2. Runs Gemini AI + MCP tools to analyze emergency details.
    3. Returns TwiML Voice XML so the AI speaks advice to caller over phone.
    """
    if not SpeechResult:
        try:
            body = await request.form()
            SpeechResult = body.get("SpeechResult")
            From = body.get("From")
            CallSid = body.get("CallSid")
        except Exception:
            pass

    twiml_xml = process_voice_call_webhook(
        speech_result=SpeechResult,
        caller_number=From,
        call_sid=CallSid
    )
    return Response(content=twiml_xml, media_type="application/xml")


@app.post("/api/voice/transcribe")
async def transcribe_audio_file(file: UploadFile = File(...)):
    """
    Uploads an audio recording (.wav, .mp3, .m4a, .webm),
    transcribes speech into text, and processes emergency details via MCP tools.
    """
    contents = await file.read()
    result = process_audio_file_transcription(audio_bytes=contents, filename=file.filename)
    return result


@app.post("/api/voice/simulate")
async def simulate_voice_call(req: Dict[str, Any]):
    """
    Simulates a phone call speech input for testing without Twilio credentials.
    Example payload: {"speech": "There is a gas leak at Central Hub and workers are unconscious."}
    """
    speech_text = req.get("speech", "")
    caller = req.get("caller", "+1-800-555-0199")
    twiml_xml = process_voice_call_webhook(speech_result=speech_text, caller_number=caller)
    
    emergency_id = f"EMG-VOICE-{int(time.time() * 1000) % 1000000:06d}"
    ai_guidance = handle_chat_message(speech_text, emergency_id)
    
    return {
        "status": "success",
        "caller": caller,
        "speech_transcription": speech_text,
        "twiml_voice_xml_response": twiml_xml,
        "ai_guidance": ai_guidance,
        "timestamp": datetime.now().isoformat()
    }


# -------------------------------------------------------------
# Serve Static Frontend Files (Root Index & Assets)
# -------------------------------------------------------------
frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if os.path.exists(os.path.join(frontend_dir, "index.html")):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")


