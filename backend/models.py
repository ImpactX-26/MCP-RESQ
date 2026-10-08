from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class LocationModel(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = "Unknown Location"
    accuracy: Optional[float] = None

class EmergencyCreateRequest(BaseModel):
    description: str
    type: Optional[str] = "other"
    priority: Optional[str] = "HIGH"
    location: Optional[Any] = None
    source: Optional[str] = "web"

class EmergencyResponse(BaseModel):
    id: str
    type: str
    priority: str
    description: str
    location: Optional[Any] = None
    status: str = "DETECTED"
    created_at: str
    source: str = "web"
    victim_guidance: Optional[List[str]] = []
    responder_guidance: Optional[List[str]] = []
    mcp_tools_used: Optional[List[str]] = []

class DispatchRequest(BaseModel):
    emergency_id: str

class VerificationRequest(BaseModel):
    id: Optional[str] = None
    description: Optional[str] = ""
    type: Optional[str] = "other"
    location: Optional[Any] = None
    priority: Optional[str] = "HIGH"

class ChatMessageRequest(BaseModel):
    message: str
    emergency_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    reply: str
    message: Optional[str] = None
    emergency_id: Optional[str] = None
    tools_invoked: Optional[List[str]] = []
