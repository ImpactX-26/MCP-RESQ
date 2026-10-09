"""MCP-ResQ — Consolidated Models & Schemas.

Contains both SQLAlchemy ORM models and Pydantic validation schemas.
Principle: AI Reasons. MCP Connects. Python Verifies.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from backend.database import Base


# ============================================================================
# 1. SQLALCHEMY ORM MODELS
# ============================================================================

class Emergency(Base):
    __tablename__ = "emergencies"

    id = Column(String(50), primary_key=True, index=True)
    description = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, index=True)  # medical, road_accident, chemical_spill, etc.
    priority = Column(String(20), nullable=False, default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    severity = Column(String(20), nullable=False, default="HIGH")
    status = Column(String(50), nullable=False, default="detected")  # detected, triaged, dispatched, active, resolved
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True, default=10.0)
    affected_count = Column(Integer, default=2)
    critical_count = Column(Integer, default=0)
    required_resources = Column(Text, nullable=True, default='{"ambulance": 1}')
    assigned_unit_id = Column(String(50), nullable=True)
    assigned_hospital_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class EmergencyUnit(Base):
    __tablename__ = "emergency_units"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False, index=True)  # 10 fleet roles
    status = Column(String(50), nullable=False, default="available")  # available, dispatched, en_route, on_scene, busy
    location = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capabilities = Column(Text, nullable=True, default="[]")
    capacity = Column(Integer, default=2)
    workload = Column(Integer, default=0)
    assigned_emergency_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), default="hospital")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(200), nullable=False)
    emergency_available = Column(Boolean, default=True)
    available_beds = Column(Integer, default=10)
    total_beds = Column(Integer, default=100)
    icu_available = Column(Boolean, default=True)
    icu_beds = Column(Integer, default=4)
    trauma_level = Column(Integer, default=1)
    trauma_support = Column(Boolean, default=True)
    capabilities = Column(Text, nullable=True, default="[]")
    contact = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Dispatch(Base):
    __tablename__ = "dispatches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emergency_id = Column(String(50), nullable=False, index=True)
    unit_id = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="dispatched")
    eta_minutes = Column(Integer, default=7)
    dispatched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Tracking(Base):
    __tablename__ = "tracking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emergency_id = Column(String(50), nullable=False, index=True)
    unit_id = Column(String(50), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_km = Column(Float, default=2.4)
    eta_minutes = Column(Integer, default=7)
    progress = Column(Integer, default=65)  # 0 to 100%
    speed_kmh = Column(Float, default=45.0)
    traffic_condition = Column(String(50), default="moderate")
    origin = Column(String(100), default="MG Road")
    destination = Column(String(100), default="Emergency Location")
    data_status = Column(String(50), default="SIMULATED LIVE TRACKING")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(50), primary_key=True, index=True)
    emergency_id = Column(String(50), nullable=True, index=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="HIGH")  # INFO, WARNING, CRITICAL
    alert_type = Column(String(50), default="hazard_warning")
    target_area = Column(String(100), default="Sector A")
    area = Column(String(100), default="Sector A")
    recipient_count = Column(Integer, default=150)
    status = Column(String(50), default="broadcasted")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = f"ALT-{int(datetime.now(timezone.utc).timestamp() * 1000) % 100000:05d}"
        if "area" in kwargs and "target_area" not in kwargs:
            kwargs["target_area"] = kwargs["area"]
        elif "target_area" in kwargs and "area" not in kwargs:
            kwargs["area"] = kwargs["target_area"]
        super().__init__(**kwargs)


# ============================================================================
# 2. PYDANTIC SCHEMAS (API & DATA CONTRACTS)
# ============================================================================

class EmergencyLocationSchema(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy: Optional[float] = 10.0

LocationSchema = EmergencyLocationSchema


class EmergencyCreateRequest(BaseModel):
    type: str = Field(..., min_length=2)
    description: str = Field(..., min_length=3)
    priority: Optional[str] = "HIGH"
    severity: Optional[str] = "HIGH"
    location: Optional[EmergencyLocationSchema] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = 10.0
    affected_count: Optional[int] = 2
    critical_count: Optional[int] = 0
    required_resources: Optional[Dict[str, int]] = None
    source: Optional[str] = "web"


class EmergencyResponse(BaseModel):
    id: str
    type: str
    description: str
    priority: str
    severity: str
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[EmergencyLocationSchema] = None
    affected_count: Optional[int] = 0
    critical_count: Optional[int] = 0
    assigned_unit_id: Optional[str] = None
    assigned_hospital_id: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class UnitResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    location: str
    latitude: float
    longitude: float
    capabilities: List[str] = []
    capacity: int = 2
    workload: int = 0
    distance_km: Optional[float] = None
    eta_minutes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class HospitalResponse(BaseModel):
    id: str
    name: str
    type: str
    latitude: float
    longitude: float
    address: str
    emergency_available: bool
    available_beds: int
    total_beds: int = 100
    icu_available: bool = True
    icu_beds: int = 4
    trauma_level: int = 1
    trauma_support: bool = True
    capabilities: List[str] = []
    contact: Optional[str] = None
    distance_km: Optional[float] = None
    eta_minutes: Optional[int] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class NearbyHelpItem(BaseModel):
    name: str
    type: str
    distance_km: float
    eta_minutes: int
    status: str
    address: str
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class TrackingResponse(BaseModel):
    emergency_id: Optional[str] = None
    unit_id: Optional[str] = "AMB-101"
    unit_name: Optional[str] = "Emergency Responder"
    status: str = "en_route"
    distance_km: Optional[float] = 0.0
    eta_minutes: Optional[int] = 0
    progress: Optional[int] = 0
    origin: Optional[str] = Field("Base Station", alias="from")
    destination: Optional[str] = "Incident Location"
    latitude: Optional[float] = 12.9716
    longitude: Optional[float] = 77.5946
    speed_kmh: Optional[float] = 45.0
    traffic_condition: Optional[str] = "moderate"
    data_status: Optional[str] = "SIMULATED LIVE TRACKING"
    data_source: Optional[str] = "DEMO SIMULATION"
    is_paused: Optional[bool] = False
    speed_multiplier: Optional[float] = 1.0
    route_geometry: Optional[List[List[float]]] = None
    polyline: Optional[str] = None
    updated_at: str

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
        extra="ignore",
    )


class SimulationControlRequest(BaseModel):
    action: str = Field(..., description="pause, resume, restart, set_speed, set_multiplier, step")
    speed_kmh: Optional[float] = None
    multiplier: Optional[float] = None


class SimulationControlResponse(BaseModel):
    success: bool
    emergency_id: str
    action: str
    is_paused: bool
    speed_kmh: float
    multiplier: float
    status: str
    progress: float
    message: str


class AuditLogEntry(BaseModel):
    id: str
    timestamp: str
    iso_time: str
    emergency_id: Optional[str] = None
    event_type: str
    description: str
    details: Optional[Dict[str, Any]] = None


class ConfigResponse(BaseModel):
    google_maps_browser_key: Optional[str] = None
    google_maps_map_id: Optional[str] = None
    app_env: str = "development"
    dev_mode: bool = True
    status: Dict[str, str]



class DispatchActionRequest(BaseModel):
    emergency_id: str

DispatchRequest = DispatchActionRequest


class DispatchResponse(BaseModel):
    success: bool
    unit_id: str
    emergency_id: str
    status: str
    eta_minutes: int
    message: Optional[str] = None
    model_config = ConfigDict(extra="ignore")


class VerificationRequest(BaseModel):
    emergency_id: Optional[str] = None
    emergency_type: str = "general"
    location: Optional[Dict[str, float]] = None


class VerificationResponse(BaseModel):
    verified: bool
    overall_verified: Optional[bool] = True
    is_valid: bool
    message: str
    checks: Optional[Dict[str, bool]] = None
    details: Dict[str, Any] = {}
    verified_by_python: bool = True
    timestamp: str
    model_config = ConfigDict(extra="ignore")


class WhatIfRequest(BaseModel):
    scenario: str
    emergency_id: Optional[str] = "EMG-1001"
    parameters: Optional[Dict[str, Any]] = None


class ResourceGapRequest(BaseModel):
    required: Dict[str, int]
    available: Optional[Dict[str, int]] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    emergency_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    response: str
    emergency_id: Optional[str] = None
    mcp_tools_used: List[str] = []
    context: Dict[str, Any] = {}


class CoordinationRequest(BaseModel):
    emergency_id: str


class CoordinationResponse(BaseModel):
    success: bool
    emergency_id: str
    resources: List[Dict[str, Any]] = []
    hospital: Optional[Dict[str, Any]] = None
    verification: Dict[str, Any] = {}
    summary: str
    model_config = ConfigDict(extra="ignore")


class ToolExecuteRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}


# ============================================================================
# 3. BACKWARD-COMPATIBILITY SCHEMAS FOR TESTS & DEMO BENCHMARKS
# ============================================================================

class Incident(BaseModel):
    id: str
    type: str
    location: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    affected: int = Field(..., ge=0)
    critical: int = Field(..., ge=0)
    severity: str
    description: str
    is_synthetic: bool = True


class IncidentAnalysis(BaseModel):
    incident_id: str
    triage_priority: str
    required_resources: Dict[str, int]
    hazard_notes: List[str] = []
    evacuation_needed: bool = False
    ai_reasoning: str


class Resource(BaseModel):
    id: str
    name: str
    type: str
    status: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    distance_km: Optional[float] = None
    eta_mins: Optional[int] = None
    is_synthetic: bool = True


class ResourceGap(BaseModel):
    resource_type: str
    required: int = Field(..., ge=0)
    available: int = Field(..., ge=0)
    gap: int = Field(..., ge=0)
    has_gap: bool


class WhatIfResult(BaseModel):
    scenario: str
    parameter_change: str
    initial_gap: int = Field(..., ge=0)
    new_gap: int = Field(..., ge=0)
    change_delta: int
    gap_eliminated: bool
    explanation: str


class Facility(BaseModel):
    id: str
    name: str
    type: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    total_capacity: int = Field(..., ge=0)
    available_capacity: int = Field(..., ge=0)
    has_icu: bool = False
    has_burn_unit: bool = False
    distance_km: Optional[float] = None
    eta_mins: Optional[int] = None
    is_synthetic: bool = True


class SafeLocation(BaseModel):
    id: str
    name: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    capacity: int = Field(..., ge=0)
    upwind_safe: bool = True
    type: str
    distance_km: Optional[float] = None
    is_synthetic: bool = True


class Route(BaseModel):
    origin: str
    destination: str
    distance_km: float = Field(..., ge=0.0)
    duration_mins: int = Field(..., ge=0)
    fallback: bool = True
    polyline: Optional[str] = None


class ResponsePlan(BaseModel):
    incident_id: str
    incident_type: str
    severity: str
    resources_allocated: List[Resource] = []
    facilities_allocated: List[Facility] = []
    safe_locations: List[SafeLocation] = []
    resource_gaps: List[ResourceGap] = []
    routes: List[Route] = []
    python_verified: bool = True
    explainable_briefing: str
    is_synthetic_demo: bool = True


class MCPToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any
    latency_ms: float
    error: Optional[str] = None


class MCPExecutionTrace(BaseModel):
    trace_id: str
    timestamp: str
    tools_called: List[MCPToolResult] = []
    total_latency_ms: float
    pipeline_status: str


class IncidentProcessOutput(BaseModel):
    incident_id: str
    analysis: IncidentAnalysis
    response_plan: ResponsePlan
    trace: MCPExecutionTrace
    status: str
