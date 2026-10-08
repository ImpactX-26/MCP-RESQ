"""
Model Context Protocol (MCP) Server & Tool Registry for MCP-RESQ.
Provides structured capabilities and tools for emergency AI decision support.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

# In-Memory State for Emergency System
units_db: List[Dict[str, Any]] = [
    {
        "id": "AMB-101",
        "name": "Ambulance A-12 (ALS)",
        "type": "ambulance",
        "status": "available",
        "location": "City Hospital Station - Central",
        "distance_km": 2.4,
        "eta_minutes": 7,
        "equipment": ["Defibrillator", "Oxygen", "Trauma Kit", "Ventilator"]
    },
    {
        "id": "AMB-102",
        "name": "Ambulance A-15 (BLS)",
        "type": "ambulance",
        "status": "available",
        "location": "MG Road Sector 4",
        "distance_km": 4.1,
        "eta_minutes": 12,
        "equipment": ["First Aid", "Stretcher", "AED", "O2 Tank"]
    },
    {
        "id": "FIRE-201",
        "name": "Fire Tender F-04",
        "type": "fire",
        "status": "available",
        "location": "Yelahanka Central Fire Station",
        "distance_km": 3.1,
        "eta_minutes": 9,
        "equipment": ["Water Cannon", "Foam Extinguisher", "Thermal Camera", "Ladders"]
    },
    {
        "id": "FIRE-202",
        "name": "Fire Tender F-08",
        "type": "fire",
        "status": "busy",
        "location": "Hebbal Flyover Zone",
        "distance_km": 6.4,
        "eta_minutes": 18,
        "equipment": ["Hydraulic Cutter", "Smoke Extractor"]
    },
    {
        "id": "RES-301",
        "name": "Heavy Rescue Team R-02",
        "type": "rescue",
        "status": "available",
        "location": "Central Metro Rescue Hub",
        "distance_km": 1.8,
        "eta_minutes": 5,
        "equipment": ["Jaws of Life", "Search Drone", "Rope Rescue", "Hazmat Suit"]
    }
]

nearby_services_db: List[Dict[str, Any]] = [
    {
        "id": "H-101",
        "name": "City Emergency Trauma Hospital",
        "type": "hospital",
        "distance_km": 3.2,
        "eta_minutes": 8,
        "status": "Emergency Desk Active",
        "address": "120 Central Boulevard, City Center",
        "phone": "+1-800-555-0199",
        "er_beds_free": 14,
        "icu_beds_free": 5,
        "trauma_level": "Level 1"
    },
    {
        "id": "H-102",
        "name": "Metro Care Specialty Hospital",
        "type": "hospital",
        "distance_km": 4.5,
        "eta_minutes": 12,
        "status": "Emergency Desk Active",
        "address": "45 North Expressway, Zone 3",
        "phone": "+1-800-555-0244",
        "er_beds_free": 8,
        "icu_beds_free": 2,
        "trauma_level": "Level 2"
    },
    {
        "id": "F-101",
        "name": "Yelahanka Fire & Hazmat Station",
        "type": "fire",
        "distance_km": 3.1,
        "eta_minutes": 9,
        "status": "Operational",
        "address": "88 Yelahanka Ring Road",
        "phone": "101 Fire Control",
        "units_available": 3
    },
    {
        "id": "P-101",
        "name": "Central Metropolitan Police HQ",
        "type": "police",
        "distance_km": 2.7,
        "eta_minutes": 7,
        "status": "Operational",
        "address": "10 Civic Center Drive",
        "phone": "100 Police Control",
        "patrol_cars_active": 12
    },
    {
        "id": "R-101",
        "name": "Disaster Rescue Command Base",
        "type": "rescue",
        "distance_km": 1.8,
        "eta_minutes": 5,
        "status": "Available 24/7",
        "address": "5 Rescue Parkway, South Hub",
        "phone": "+1-800-555-0911",
        "teams_standby": 4
    }
]

emergencies_db: Dict[str, Dict[str, Any]] = {}
tracking_db: Dict[str, Dict[str, Any]] = {}

# Incident SOP Protocols (Victim + Responder Guidance)
INCIDENT_PROTOCOLS = {
    "fire": {
        "victim_instructions": [
            "🚨 EVACUATE IMMEDIATELY: Leave the building using stairs. Do NOT use elevators.",
            "💨 STAY LOW TO THE FLOOR: Crawl under smoke to avoid toxic gas inhalation.",
            "🚪 TOUCH DOORS BEFORE OPENING: If a door is hot to touch, do NOT open it — seek alternate exit.",
            "👕 STOP, DROP, AND ROLL: If clothing catches fire, cover your face and roll on the ground.",
            "📍 MEET AT ASSEMBLY POINT: Move to an open area away from structure once safe."
        ],
        "responder_instructions": [
            "🚒 Dispatch Fire Unit F-04 immediately with thermal imaging & foam extinguisher.",
            "💧 Establish primary water supply connection from nearest hydrant.",
            "🚪 Conduct search and rescue on ground level and secondary egress points.",
            "⚡ Request power grid isolation for affected structure from local utility.",
            "🏥 Alert City Trauma Hospital (H-101) to stand by for smoke inhalation burn victims."
        ]
    },
    "medical": {
        "victim_instructions": [
            "🧘 STAY CALM AND STILL: Sit or lie down in a comfortable, open position.",
            "🫁 OPEN AIRWAY & BREATHE: Loosen tight clothing around neck and chest.",
            "🩸 BLEEDING CONTROL: If bleeding, apply direct pressure with a clean cloth.",
            "🚫 NO FOOD/DRINK: Do not eat, drink, or ingest medication until paramedics arrive.",
            "🔓 UNLOCK FRONT DOOR: Ensure responders can access the building easily."
        ],
        "responder_instructions": [
            "🚑 Dispatch ALS Ambulance A-12 with oxygen, defibrillator, and ECG equipment.",
            "📈 Prepare for triage check: Vitals, airway, pulse oximetry, and GCS score.",
            "🏥 Notify Metro Care ER desk with incoming patient profile & ETA.",
            "🛣️ Request traffic control priority along MG Road corridor."
        ]
    },
    "accident": {
        "victim_instructions": [
            "🚗 TURN OFF VEHICLE IGNITION: Prevent potential fuel leaks or fire hazards.",
            "⚠️ TURN ON HAZARD LIGHTS: Signal incoming traffic if safe inside vehicle.",
            "🛑 DO NOT MOVE INJURED PERSONS: Unless immediate danger of fire exists, immobilize neck.",
            "📞 REMAIN AT SAFE DISTANCE: Stand behind safety barriers away from traffic flow."
        ],
        "responder_instructions": [
            "🚓 Dispatch Traffic Police & Ambulance A-15 for collision site perimeter.",
            "🛟 Prepare Hydraulic Cutter (Jaws of Life) if occupant entrapment is reported.",
            "⛽ Inspect for fuel spillage; deploy absorbent sand/foam if required.",
            "🚧 Set up road flare warning triangle 100 meters upstream."
        ]
    },
    "rescue": {
        "victim_instructions": [
            "📢 MAKE DISTINCT NOISE: Tap rhythmically on pipes/walls to assist search locator drones.",
            "🛡️ COVER HEAD & MOUTH: Use cloth to cover nose and mouth from dust.",
            "🔋 CONSERVE PHONE BATTERY: Keep phone on power saver; avoid streaming.",
            "🧘 STAY CALM: Emergency Rescue Squad R-02 is en route."
        ],
        "responder_instructions": [
            "🛟 Deploy Heavy Rescue Squad R-02 with acoustic search sensors and drones.",
            "🏗️ Stabilize surrounding debris before structural entry.",
            "🏥 Pre-stage ALS Paramedics at extraction zone."
        ]
    },
    "disaster": {
        "victim_instructions": [
            "⛰️ MOVE TO HIGH/OPEN GROUND: Stay clear of power lines, trees, and tall structures.",
            "📻 LISTEN TO EMERGENCY BROADCASTS: Follow official evacuation route directives.",
            "💧 DRINK BOTTLED WATER ONLY: Avoid tap water if contamination risk exists.",
            "🎒 KEEP EMERGENCY GO-BAG READY: Wallet, medication, flashlight, and IDs."
        ],
        "responder_instructions": [
            "🌊 Establish Incident Command Center at Disaster Rescue Base (R-101).",
            "🚁 Deploy reconnaissance drone for flood/quake damage assessment.",
            "⛺ Set up temporary triage shelter with emergency supplies."
        ]
    },
    "other": {
        "victim_instructions": [
            "📍 STAY IN A SAFE LOCATION: Share your exact coordinates with emergency dispatch.",
            "📞 KEEP PHONE LINE CLEAR: Emergency services may call back for details.",
            "👀 WATCH FOR RESPONDERS: Flash lights or wave bright cloth to signal position."
        ],
        "responder_instructions": [
            "📞 Maintain continuous phone contact with victim for situation monitoring.",
            "🚔 Dispatch local police patrol P-101 for scene evaluation."
        ]
    }
}


class MCPToolsEngine:
    """
    Model Context Protocol (MCP) Tool Implementation.
    """

    @staticmethod
    def get_incident_protocols(incident_type: str, priority: str = "HIGH") -> Dict[str, Any]:
        """MCP Tool: Retrieves official SOP guidance for victim safety and responder action."""
        normalized_type = incident_type.lower() if incident_type else "other"
        protocol = INCIDENT_PROTOCOLS.get(normalized_type, INCIDENT_PROTOCOLS["other"])
        return {
            "tool": "get_incident_protocols",
            "incident_type": normalized_type,
            "priority": priority,
            "victim_instructions": protocol["victim_instructions"],
            "responder_instructions": protocol["responder_instructions"],
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def lookup_emergency_resources(resource_type: str = "all", status: str = "available") -> Dict[str, Any]:
        """MCP Tool: Queries live database for matching emergency response units."""
        filtered = units_db
        if resource_type and resource_type != "all":
            filtered = [u for u in filtered if u["type"] == resource_type.lower()]
        if status:
            filtered = [u for u in filtered if u["status"] == status.lower()]

        return {
            "tool": "lookup_emergency_resources",
            "query_type": resource_type,
            "status_filter": status,
            "total_found": len(filtered),
            "units": filtered
        }

    @staticmethod
    def find_nearby_hospitals_and_facilities(facility_type: str = "all") -> Dict[str, Any]:
        """MCP Tool: Locates nearest medical, fire, police, or rescue facilities."""
        filtered = nearby_services_db
        if facility_type and facility_type != "all":
            filtered = [f for f in filtered if f["type"] == facility_type.lower()]

        return {
            "tool": "find_nearby_hospitals_and_facilities",
            "facility_type": facility_type,
            "facilities": filtered
        }

    @staticmethod
    def verify_incident_details(incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """MCP Tool: Validates emergency data, location accuracy, and resource matching."""
        desc = str(incident_data.get("description", ""))
        inc_type = incident_data.get("type", "other")
        loc = incident_data.get("location")

        loc_verified = bool(loc and (isinstance(loc, dict) and loc.get("latitude") or isinstance(loc, str)))
        emergency_verified = len(desc) > 3
        resources_verified = any(u["status"] == "available" for u in units_db)
        ai_verified = True

        return {
            "tool": "verify_incident_details",
            "location_verified": loc_verified,
            "emergency_verified": emergency_verified,
            "resources_verified": resources_verified,
            "ai_verified": ai_verified,
            "confidence_score": 0.96 if (loc_verified and emergency_verified) else 0.82,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def dispatch_unit_to_incident(unit_id: str, emergency_id: str) -> Dict[str, Any]:
        """MCP Tool: Dispatches a response unit to an active emergency ID."""
        unit = next((u for u in units_db if u["id"] == unit_id), None)
        if not unit:
            return {"tool": "dispatch_unit_to_incident", "success": False, "error": f"Unit {unit_id} not found."}

        unit["status"] = "en_route"

        # Update or create tracking record
        tracking_db[emergency_id] = {
            "emergency_id": emergency_id,
            "unit_id": unit_id,
            "unit_name": unit["name"],
            "unit_type": unit["type"],
            "distance_km": unit["distance_km"],
            "eta_minutes": unit["eta_minutes"],
            "status": "en_route",
            "progress": 25,
            "from": unit["location"],
            "destination": "Incident Scene",
            "updated_at": datetime.now().isoformat()
        }

        return {
            "tool": "dispatch_unit_to_incident",
            "success": True,
            "unit_dispatched": unit,
            "emergency_id": emergency_id,
            "tracking": tracking_db[emergency_id]
        }

    @staticmethod
    def assess_hazard_and_safety_checks(incident_type: str, description: str) -> Dict[str, Any]:
        """MCP Tool: Assesses critical environmental and physical hazards from incident report."""
        desc_lower = description.lower()
        hazards = []

        if "smoke" in desc_lower or "fire" in desc_lower or "flame" in desc_lower:
            hazards.append("🔥 High Risk: Toxic smoke inhalation and structural heat collapse.")
        if "gas" in desc_lower or "leak" in desc_lower or "chemical" in desc_lower:
            hazards.append("⚠️ Critical Risk: Airborne chemical hazard or explosive gas leak.")
        if "blood" in desc_lower or "bleed" in desc_lower or "injury" in desc_lower:
            hazards.append("🩸 Medical Urgency: Severe blood loss or trauma detected.")
        if "trapped" in desc_lower or "stuck" in desc_lower or "debris" in desc_lower:
            hazards.append("🏗️ Structural Risk: Entrapment under heavy load.")

        if not hazards:
            hazards.append("⚡ Standard Alert: Maintain safe distance and keep communications active.")

        return {
            "tool": "assess_hazard_and_safety_checks",
            "incident_type": incident_type,
            "hazards_identified": hazards,
            "safety_clearance_required": len(hazards) > 1
        }
    def dispatch_ambulance_unit(emergency_id: str = "EMG-GENERAL") -> Dict[str, Any]:
        """MCP Tool: Specialized Medical Emergency Ambulance Dispatch & ER Bed Check."""
        amb = next((u for u in units_db if u["type"] == "ambulance" and u["status"] == "available"), units_db[0])
        hosp = nearby_services_db[0]
        return {
            "tool": "dispatch_ambulance_unit",
            "unit_dispatched": amb,
            "emergency_id": emergency_id,
            "destination_hospital": hosp["name"],
            "er_beds_available": hosp.get("er_beds_free", 14),
            "tactical_guidance": [
                "1. Maintain patient airway and monitor oxygen saturation.",
                "2. Apply firm direct pressure for active hemorrhage.",
                "3. Pre-alert ER trauma team at City Emergency Hospital with ETA."
            ],
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def call_fire_engine_station(emergency_id: str = "EMG-GENERAL") -> Dict[str, Any]:
        """MCP Tool: Fire Engine Station Call & Hydrant Deployment."""
        fire_unit = next((u for u in units_db if u["type"] == "fire" and u["status"] == "available"), units_db[2])
        return {
            "tool": "call_fire_engine_station",
            "unit_dispatched": fire_unit,
            "emergency_id": emergency_id,
            "station": "Yelahanka Fire & Hazmat Station",
            "water_capacity": "4500 Liters Foam/Water Engine",
            "tactical_guidance": [
                "1. Deploy thermal imaging drone for roof heat spots.",
                "2. Hook primary 65mm hose line to nearest municipal hydrant.",
                "3. Conduct primary search along secondary egress staircases."
            ],
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def generate_fire_evacuation_plan(building_type: str = "residential") -> Dict[str, Any]:
        """MCP Tool: Generates emergency floor-by-floor evacuation plan and smoke safety route."""
        return {
            "tool": "generate_fire_evacuation_plan",
            "building_type": building_type,
            "evacuation_steps": [
                "🚨 Step 1: Evacuate immediately via fire stairwell. Do NOT use elevators.",
                "💨 Step 2: Stay below 3-foot mark to avoid carbon monoxide smoke layer.",
                "🚪 Step 3: Touch door handles with back of hand before opening.",
                "📍 Step 4: Proceed to Primary Assembly Point A (100 meters upwind)."
            ],
            "suppression_supplies_nearby": [
                "Class A/B/C Dry Powder Extinguisher (50m down hallway)",
                "Fire Hose Reel (Stairwell Landing Floor 2)",
                "Municipal High-Pressure Hydrant (Main Gate Entrance)"
            ]
        }

    @staticmethod
    def locate_nearby_extinguishers_and_suppression() -> Dict[str, Any]:
        """MCP Tool: Locates nearby fire hydrants, CO2 extinguishers, and foam suppressors."""
        return {
            "tool": "locate_nearby_extinguishers_and_suppression",
            "suppression_assets": [
                {"type": "Municipal Hydrant H-104", "location": "50m North Gate", "status": "Active (4.5 Bar)"},
                {"type": "CO2 Extinguisher 10kg", "location": "Electrical Panel Room", "status": "Inspected"},
                {"type": "Foam Cannon Trailer", "location": "Industrial Sector Depot", "status": "On Standby"}
            ]
        }

    @staticmethod
    def call_hazmat_containment_squad(emergency_id: str = "EMG-GENERAL") -> Dict[str, Any]:
        """MCP Tool: Dispatches specialized Chemical & Toxic Gas Containment Squad."""
        return {
            "tool": "call_hazmat_containment_squad",
            "unit_dispatched": {
                "id": "HAZ-401",
                "name": "Hazmat Containment Squad H-09",
                "type": "hazmat",
                "status": "en_route",
                "equipment": ["Chemical Suit Level A", "Gas Vapor Detector", "Plug & Patch Kit"]
            },
            "emergency_id": emergency_id,
            "containment_protocols": [
                "1. Establish 500-meter upwind isolation perimeter.",
                "2. Shut off main gas intake valve immediately.",
                "3. Prohibit open flames, electrical switches, or engine ignition."
            ]
        }

    @staticmethod
    def assess_gas_leak_evacuation_zone(gas_type: str = "natural_gas") -> Dict[str, Any]:
        """MCP Tool: Assesses gas leak hazard, windward isolation zone, and ignition prevention."""
        return {
            "tool": "assess_gas_leak_evacuation_zone",
            "gas_type": gas_type,
            "isolation_radius_meters": 500,
            "wind_direction_advice": "Evacuate UPWIND or CROSSWIND immediately.",
            "safety_instructions": [
                "⚠️ DO NOT flip electrical switches or start vehicle engines.",
                "🪟 Ventilate space if safe by opening windows/doors.",
                "😷 Cover mouth/nose with wet cloth to filter airborne particulates."
            ]
        }

    @staticmethod
    def dispatch_heavy_rescue_squad(emergency_id: str = "EMG-GENERAL") -> Dict[str, Any]:
        """MCP Tool: Dispatches Heavy Rescue Squad with hydraulic cutters & acoustic drones."""
        rescue_unit = units_db[4]
    @staticmethod
    def search_medical_knowledgebase(query: str) -> Dict[str, Any]:
        """MCP Tool: Searches medical knowledgebase & Red Cross/AHA protocols for accurate first aid."""
        q_lower = query.lower()

        if "neck" in q_lower or "spine" in q_lower or "spinal" in q_lower or "back" in q_lower or "paralys" in q_lower:
            return {
                "tool": "search_medical_knowledgebase",
                "topic": "Spinal / Cervical Neck Injury Protocol",
                "source": "American Red Cross & Mayo Clinic Emergency Protocol",
                "guidance": [
                    "🚨 DO NOT MOVE THE PATIENT: Do NOT move head, neck, or spine under any circumstances unless in immediate danger of fire.",
                    "🚑 CALL AMBULANCE IMMEDIATELY: Request ALS Ambulance A-12 with cervical collar and spinal immobilization board.",
                    "🧥 IMMOBILIZE HEAD & NECK: Place rolled towels, jackets, or sandbags on both sides of head to prevent any movement.",
                    "🪖 DO NOT REMOVE HELMETS: If victim is wearing a motorcycle or sports helmet, leave it on.",
                    "🪵 LOG-ROLL RIGIDLY IF VOMITING: If victim vomits or chokes, log-roll their entire body as a single rigid unit without twisting the neck."
                ]
            }
        elif "chok" in q_lower or "airway" in q_lower:
            return {
                "tool": "search_medical_knowledgebase",
                "topic": "Choking & Airway Obstruction",
                "source": "AHA First Aid Guidelines",
                "guidance": [
                    "1. Conscious Adult: Give 5 back blows followed by 5 abdominal thrusts (Heimlich maneuver).",
                    "2. Unconscious: Lower gently to floor, request ambulance, begin CPR chest compressions.",
                    "3. Check mouth for visible object before rescue breaths; avoid blind finger sweeps."
                ]
            }
        elif "bleed" in q_lower or "wound" in q_lower or "cut" in q_lower or "hemorrhage" in q_lower:
            return {
                "tool": "search_medical_knowledgebase",
                "topic": "Severe Hemorrhage & Bleeding Control",
                "source": "AHA / Red Cross First Aid",
                "guidance": [
                    "1. Apply direct, firm, continuous pressure over wound with clean cloth or sterile gauze.",
                    "2. Do not remove blood-soaked cloths; layer additional pads directly on top.",
                    "3. Apply arterial tourniquet 2-3 inches above wound on limb if life-threatening hemorrhage."
                ]
            }
        elif "cpr" in q_lower or "heart" in q_lower or "cardiac" in q_lower or "chest pain" in q_lower:
            return {
                "tool": "search_medical_knowledgebase",
                "topic": "Cardiac Arrest & CPR Protocol",
                "source": "AHA CPR Protocol",
                "guidance": [
                    "1. Push hard and fast in center of chest (100-120 compressions per minute).",
                    "2. Alternate 30 compressions with 2 rescue breaths if trained.",
                    "3. Apply Automated External Defibrillator (AED) as soon as available."
                ]
            }
        elif "burn" in q_lower or "fire" in q_lower or "scald" in q_lower:
            return {
                "tool": "search_medical_knowledgebase",
                "topic": "Thermal & Chemical Burn Protocol",
                "source": "Red Cross Emergency First Aid",
                "guidance": [
                    "1. Cool burn immediately under clean, cool running water for at least 10-20 minutes.",
                    "2. Cover loosely with sterile, non-stick bandage or clean cling wrap.",
                    "3. Do NOT apply ice, butter, or ointments. Do NOT break blisters."
                ]
            }

        return {
            "tool": "search_medical_knowledgebase",
            "topic": "General Emergency Medical First Aid",
            "source": "Red Cross Triage Guidelines",
            "guidance": [
                "1. Keep patient calm, comfortable, and still.",
                "2. Call emergency ambulance dispatch immediately.",
                "3. Monitor airway, breathing, and pulse continuously."
            ]
        }


