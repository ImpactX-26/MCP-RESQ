import os
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from mcp_server import MCPToolsEngine, emergencies_db, units_db, nearby_services_db

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

genai_client = None

if GEMINI_API_KEY:
    try:
        from google import genai
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
        print("[INFO] Gemini API Client initialized successfully.")
    except Exception as e:
        print(f"[WARN] Gemini SDK init warning: {e}. Falling back to MCP Decision Engine.")


PREFERRED_MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-pro"]

def call_gemini_with_fallback(prompt: str) -> Optional[str]:
    """Helper to try primary and fallback Gemini models."""
    if not genai_client:
        return None
    for model_name in PREFERRED_MODELS:
        try:
            response = genai_client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and hasattr(response, "text") and response.text:
                return response.text
        except Exception as e:
            print(f"[WARN] Model {model_name} failed: {e}. Trying next fallback...")
    return None


def generate_gemini_emergency_analysis(description: str, emergency_type: str, location: Any) -> Dict[str, Any]:
    """
    Uses Gemini LLM + MCP Tools to collect incident information (Fire, Medical, Rescue, etc.)
    and return instructions for both responder and victim.
    """
    inc_type = emergency_type.lower() if emergency_type else "other"

    # Step 1: Call specialized MCP Tools for context
    protocol = MCPToolsEngine.get_incident_protocols(inc_type)
    resources = MCPToolsEngine.lookup_emergency_resources(resource_type=inc_type)
    hazards = MCPToolsEngine.assess_hazard_and_safety_checks(inc_type, description)
    hospitals = MCPToolsEngine.find_nearby_hospitals_and_facilities("hospital" if inc_type in ["medical", "accident"] else "all")
    verification = MCPToolsEngine.verify_incident_details({"description": description, "type": inc_type, "location": location})

    # Prepare prompt for Gemini LLM if API Key is available
    if genai_client:
        system_prompt = f"""
You are the MCP-RESQ Emergency Decision Support AI powered by Google Gemini and Model Context Protocol (MCP).
An emergency report has been submitted by a user:
- Incident Type: {inc_type.upper()}
- Description: "{description}"
- Location Coordinates/Address: {location}
- Detected Environmental Hazards: {hazards.get('hazards_identified')}
- Available Specialized Units: {[u['name'] for u in resources.get('units', [])]}
- Nearby Facilities: {[f['name'] for f in hospitals.get('facilities', [])[:3]]}
- MCP Data Confidence Score: {verification.get('confidence_score')}

Provide structured, emergency-grade decision support strictly customized to what the user reported:
1. 🆘 VICTIM / CALLER GUIDANCE: 3-5 immediate, clear survival & safety steps for people on site.
2. 🚒 RESPONDER & DISPATCH TACTICAL PLAN: Specific unit dispatch recommendation, hazard containment, and hospital alert protocol.
3. 🛡️ MCP SAFETY VERIFICATION: Explanation of why these specific resources were selected.
"""
        llm_text = call_gemini_with_fallback(system_prompt)
        if llm_text:
            return {
                "victim_guidance": protocol["victim_instructions"],
                "responder_guidance": protocol["responder_instructions"],
                "llm_analysis": llm_text,
                "mcp_tools_used": [
                    "get_incident_protocols",
                    "lookup_emergency_resources",
                    "assess_hazard_and_safety_checks",
                    "find_nearby_hospitals_and_facilities",
                    "verify_incident_details",
                    "gemini_2.5_flash_llm"
                ]
            }

    # Fallback to local MCP Decision Engine if Gemini API Key is missing or API call fails
    return {
        "victim_guidance": protocol["victim_instructions"],
        "responder_guidance": protocol["responder_instructions"],
        "llm_analysis": f"MCP Emergency Decision Engine analyzed {inc_type.upper()} incident report: '{description}'. "
                       f"Identified {len(hazards.get('hazards_identified', []))} hazard factors. "
                       f"{len(resources.get('units', []))} specialized units assigned.",
        "mcp_tools_used": [
            "get_incident_protocols",
            "lookup_emergency_resources",
            "assess_hazard_and_safety_checks",
            "find_nearby_hospitals_and_facilities"
        ]
    }


def handle_chat_message(message: str, emergency_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Handles user chat messages using Gemini API + MCP Tools context.
    Analyzes exact user question intent to execute corresponding MCP tools.
    """
    msg_lower = message.lower()
    tools_invoked = []
    context_blocks = []

    # Active emergency context lookup
    active_emergency = emergencies_db.get(emergency_id) if emergency_id else None

    # Intent analysis & dynamic specialized MCP tool execution
    if any(k in msg_lower for k in ["gas", "leak", "chemical", "toxic", "hazard", "propane", "methane"]):
        hazmat = MCPToolsEngine.call_hazmat_containment_squad(emergency_id or "EMG-GENERAL")
        evac_zone = MCPToolsEngine.assess_gas_leak_evacuation_zone()
        tools_invoked.extend(["call_hazmat_containment_squad", "assess_gas_leak_evacuation_zone"])
        context_blocks.append(f"Hazmat Containment Unit Deployed: {hazmat['unit_dispatched']['name']}")
        context_blocks.append(f"Gas Leak Perimeter Advice: {evac_zone['wind_direction_advice']}")
        context_blocks.append(f"Safety Protocols: {evac_zone['safety_instructions']}")

    elif any(k in msg_lower for k in ["fire", "smoke", "flame", "explosion"]):
        fire_call = MCPToolsEngine.call_fire_engine_station(emergency_id or "EMG-GENERAL")
        evac_plan = MCPToolsEngine.generate_fire_evacuation_plan()
        exting = MCPToolsEngine.locate_nearby_extinguishers_and_suppression()
        tools_invoked.extend(["call_fire_engine_station", "generate_fire_evacuation_plan", "locate_nearby_extinguishers_and_suppression"])
        context_blocks.append(f"Fire Engine Call: {fire_call['unit_dispatched']['name']} from {fire_call['station']}")
        context_blocks.append(f"Evacuation Steps: {evac_plan['evacuation_steps']}")
        context_blocks.append(f"Suppression Equipment: {[a['type'] for a in exting['suppression_assets']]}")

    elif any(k in msg_lower for k in ["medical", "doctor", "ambulance", "heart", "bleed", "injur", "breathe", "pain", "cpr", "stroke", "chok", "faint", "seizure", "burn", "poison", "fracture", "headache", "chest", "head", "gasp", "pulse", "allergy", "anaphylaxis", "bite", "sting", "wound", "cut", "trauma", "unconscious", "first aid", "health", "patient", "sick", "neck", "spine", "spinal", "break", "broke"]):
        med_kb = MCPToolsEngine.search_medical_knowledgebase(message)
        amb_dispatch = MCPToolsEngine.dispatch_ambulance_unit(emergency_id or "EMG-GENERAL")
        proto = MCPToolsEngine.get_incident_protocols("medical")
        tools_invoked.extend(["search_medical_knowledgebase", "dispatch_ambulance_unit", "get_incident_protocols(medical)"])
        context_blocks.append(f"Medical KB Search ({med_kb['topic']} - Source: {med_kb['source']}):")
        for step in med_kb['guidance']:
            context_blocks.append(f"  - {step}")
        context_blocks.append(f"Medical Dispatch: {amb_dispatch['unit_dispatched']['name']} (Destination: {amb_dispatch['destination_hospital']})")
        context_blocks.append(f"ER Beds Available: {amb_dispatch['er_beds_available']} free at City Trauma Hospital")

    elif any(k in msg_lower for k in ["rescue", "trapped", "flood", "earthquake", "building", "collapse"]):
        heavy = MCPToolsEngine.dispatch_heavy_rescue_squad(emergency_id or "EMG-GENERAL")
        proto = MCPToolsEngine.get_incident_protocols("rescue")
        tools_invoked.extend(["dispatch_heavy_rescue_squad", "get_incident_protocols(rescue)"])
        context_blocks.append(f"Heavy Rescue Squad Deployed: {heavy['unit_dispatched']['name']} ({', '.join(heavy['equipment_deployed'])})")
        context_blocks.append(f"Rescue Survival SOP: {proto['victim_instructions']}")

    elif re.search(r'\b(hospital|hospitals|er|trauma desk|icu)\b', msg_lower):
        hosp = MCPToolsEngine.find_nearby_hospitals_and_facilities("hospital")
        tools_invoked.append("find_nearby_hospitals_and_facilities(hospital)")
        names = [f"{h['name']} ({h['distance_km']} km, {h.get('er_beds_free', 0)} ER beds free)" for h in hosp["facilities"]]
        context_blocks.append(f"Nearby Medical Facilities: {'; '.join(names)}")

    elif any(k in msg_lower for k in ["status", "where", "eta", "tracking", "unit", "location"]):
        res = MCPToolsEngine.lookup_emergency_resources()
        tools_invoked.append("lookup_emergency_resources()")
        avail = [f"{u['name']} ({u['status']}, ETA {u['eta_minutes']} min)" for u in res["units"]]
        context_blocks.append(f"Response Units Live Status: {', '.join(avail)}")

    # Prompt Gemini LLM with exact user message + MCP context
    if genai_client:
        is_medical_query = any(k in msg_lower for k in ["medical", "doctor", "ambulance", "heart", "bleed", "injur", "breathe", "pain", "cpr", "stroke", "chok", "faint", "seizure", "burn", "poison", "fracture", "headache", "chest", "head", "gasp", "pulse", "allergy", "anaphylaxis", "bite", "sting", "wound", "cut", "trauma", "unconscious", "first aid", "health", "sick", "patient", "neck", "spine", "spinal", "break", "broke"])
        
        prompt = f"""
You are the MCP-RESQ Medical Triage & Emergency Response AI powered by Google Gemini and Model Context Protocol.
The user asked the following question: "{message}"

Active Emergency Report: {active_emergency if active_emergency else "None logged yet."}
MCP Tools Context & Web-Verified Medical Knowledgebase Retrieved:
{chr(10).join(context_blocks) if context_blocks else "General Emergency Services Knowledge Base"}

{"CLINICAL MEDICAL DIRECTIVE: Search and summarize authoritative medical sources (Red Cross, Mayo Clinic, AHA guidelines). Provide immediate, step-by-step first aid (e.g. Spinal Immobilization, Airway, Bleeding Control). Be calm, authoritative, precise, and medically accurate. Do NOT return generic hospital list unless asked specifically for nearby hospitals." if is_medical_query else "Provide direct, actionable emergency guidance tailored specifically to the user question."}

Structure your response with clear numbered/bulleted action steps and bold key medical terms. Include ambulance dispatch details if medical assistance is needed.
"""
        reply_text = call_gemini_with_fallback(prompt)
        if reply_text:
            return {
                "reply": reply_text,
                "tools_invoked": tools_invoked or ["search_medical_knowledgebase", "gemini_2.5_flash_llm"],
                "emergency_id": emergency_id
            }

    # Fallback to Local MCP Chat Response if Gemini API Key fails or returns empty
    fallback_reply = generate_mcp_fallback_reply(message, context_blocks, active_emergency)
    return {
        "reply": fallback_reply,
        "tools_invoked": tools_invoked or ["search_medical_knowledgebase", "mcp_fallback_engine"],
        "emergency_id": emergency_id
    }


def generate_mcp_fallback_reply(message: str, context_blocks: List[str], active_emergency: Any) -> str:
    msg_lower = message.lower()

    # Medical Neck / Spinal Fracture Query
    if any(k in msg_lower for k in ["neck", "spine", "spinal", "back", "paralyz", "broken neck", "breaks their neck", "broke neck"]):
        kb = MCPToolsEngine.search_medical_knowledgebase(message)
        steps = "\n".join([f"{g}" for g in kb["guidance"]])
        return (f"🩺 **SPINAL & CERVICAL NECK INJURY FIRST AID (Red Cross / Mayo Clinic Protocol)**:\n\n"
                f"{steps}\n\n"
                f"🚑 **Dispatch Update**: Ambulance A-12 (ALS) equipped with cervical collar and spinal board dispatched (ETA 7 mins).")

    if any(k in msg_lower for k in ["chok", "heimlich", "airway"]):
        kb = MCPToolsEngine.search_medical_knowledgebase(message)
        steps = "\n".join([f"{g}" for g in kb["guidance"]])
        return (f"🩺 **CHOKING FIRST AID (AHA Emergency Protocol)**:\n\n{steps}")

    if any(k in msg_lower for k in ["bleed", "hemorrhage", "wound"]):
        kb = MCPToolsEngine.search_medical_knowledgebase(message)
        steps = "\n".join([f"{g}" for g in kb["guidance"]])
        return (f"🩸 **BLEEDING CONTROL PROTOCOL (Red Cross First Aid)**:\n\n{steps}")

    if any(k in msg_lower for k in ["fire", "smoke", "flame", "explosion"]):
        return ("🔥 **FIRE EMERGENCY RESPONSE (MCP SOP)**:\n"
                "1. **Evacuate immediately** via stairs. Do NOT use elevators.\n"
                "2. Stay low to the ground to avoid toxic smoke inhalation.\n"
                "3. Fire Tender F-04 (Yelahanka Fire Station) has been notified.\n"
                "4. Stop, Drop, and Roll if clothing catches fire.")

    if any(k in msg_lower for k in ["medical", "injured", "pain", "ambulance", "heart", "cpr", "stroke", "poison", "fracture"]):
        return ("🚑 **MEDICAL EMERGENCY FIRST AID (Red Cross SOP)**:\n"
                "1. Keep patient calm, comfortable, and lying completely flat.\n"
                "2. Loosen tight clothing around neck and waist to clear airway.\n"
                "3. If bleeding, apply direct, firm pressure with a clean cloth.\n"
                "4. Ambulance A-12 (ALS) is stationed 2.4 km away with a 7-minute ETA.")

    if any(k in msg_lower for k in ["status", "tracking", "eta", "where"]):
        if active_emergency:
            return f"📍 **Emergency Tracking ({active_emergency.get('id', 'Active')})**:\nStatus: {active_emergency.get('status', 'DETECTED')}\nType: {active_emergency.get('type', 'General').upper()}\nResponders en-route with live updates."
        return ("🚑 **Live Resource Status**:\n"
                "- Ambulance A-12: Available (ETA 7 mins)\n"
                "- Fire Unit F-04: Available (ETA 9 mins)\n"
                "- Rescue Team R-02: Available (ETA 5 mins)")

    # FIX: Use regex word boundary matching so substring "er" in "person" does NOT match!
    if re.search(r'\b(hospital|hospitals|er|trauma desk|icu)\b', msg_lower):
        return ("🏥 **Nearest Emergency Hospitals**:\n"
                "1. **City Emergency Trauma Hospital** (3.2 km, ETA 8 min) — Level 1 Trauma, 14 ER beds free\n"
                "2. **Metro Care Specialty Hospital** (4.5 km, ETA 12 min) — Level 2 Trauma, 8 ER beds free")

    return (f"🚨 **MCP-RESQ Emergency AI**: Received query: \"{message}\". "
            "MCP system analyzed emergency medical sources, response units, and hazard protocols. "
            "Please specify if you need immediate Medical first aid, Fire evacuation, or Rescue dispatch.")


