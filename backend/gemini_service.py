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


PREFERRED_MODELS = ["gemini-3.5-flash", "gemini-3.1-pro-preview", "gemini-3.5-flash-lite", "gemini-3.8-flash"]

def call_gemini_with_fallback(prompt: str, system_instruction: str = "", max_tokens: int = 800) -> Optional[str]:
    """Helper to try primary and fallback Gemini models with high-quality token & length control."""
    if not genai_client:
        return None

    try:
        from google.genai import types
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=0.2,
            system_instruction=system_instruction if system_instruction else "You are MCP-RESQ Emergency Response AI. Provide complete, well-structured, clear answers with bold headings and action points."
        )
    except Exception as e:
        config = None

    for model_name in PREFERRED_MODELS:
        try:
            if config:
                response = genai_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
            else:
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
        llm_text = call_gemini_with_fallback(system_prompt, max_tokens=1000)
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
                    "gemini_3.5_flash_llm"
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
    Analyzes exact user question intent to execute corresponding MCP tools with complete answers.
    """
    msg_lower = message.lower()
    tools_invoked = []
    context_blocks = []

    # Active emergency context lookup
    active_emergency = emergencies_db.get(emergency_id) if emergency_id else None

    # Detect query intent categories
    is_eta_query = any(k in msg_lower for k in ["how long", "eta", "when", "arrive", "status", "where is", "help take", "how far", "who is coming", "tracking", "time"])
    is_first_aid_query = any(k in msg_lower for k in ["what to do", "how to", "first aid", "neck", "spine", "spinal", "bleed", "cpr", "chok", "burn", "fracture", "treat", "help for", "save", "broke", "break"])
    is_hospital_query = bool(re.search(r'\b(hospital|hospitals|er|trauma desk|icu)\b', msg_lower))

    # Intent analysis & dynamic specialized MCP tool execution
    if is_eta_query and not is_first_aid_query:
        res = MCPToolsEngine.lookup_emergency_resources()
        tools_invoked.append("lookup_emergency_resources()")
        avail = [f"{u['name']} ({u['status']}, ETA {u['eta_minutes']} min, {u['distance_km']} km)" for u in res["units"]]
        context_blocks.append(f"Response Units Live Status: {'; '.join(avail)}")

    elif any(k in msg_lower for k in ["gas", "leak", "chemical", "toxic", "hazard", "propane", "methane"]):
        hazmat = MCPToolsEngine.call_hazmat_containment_squad(emergency_id or "EMG-GENERAL")
        evac_zone = MCPToolsEngine.assess_gas_leak_evacuation_zone()
        tools_invoked.extend(["call_hazmat_containment_squad", "assess_gas_leak_evacuation_zone"])
        context_blocks.append(f"Hazmat Squad: {hazmat['unit_dispatched']['name']}")
        context_blocks.append(f"Evacuation Advice: {evac_zone['wind_direction_advice']}")

    elif any(k in msg_lower for k in ["fire", "smoke", "flame", "explosion"]):
        fire_call = MCPToolsEngine.call_fire_engine_station(emergency_id or "EMG-GENERAL")
        evac_plan = MCPToolsEngine.generate_fire_evacuation_plan()
        tools_invoked.extend(["call_fire_engine_station", "generate_fire_evacuation_plan"])
        context_blocks.append(f"Fire Engine: {fire_call['unit_dispatched']['name']} ({fire_call['station']})")
        context_blocks.append(f"Evacuation SOP: Evacuate via stairs, stay low under smoke.")

    elif is_first_aid_query or any(k in msg_lower for k in ["medical", "doctor", "ambulance", "heart", "bleed", "injur", "breathe", "pain", "cpr", "stroke", "chok", "faint", "seizure", "burn", "poison", "fracture", "chest", "gasp", "pulse", "trauma", "unconscious", "first aid", "health"]):
        med_kb = MCPToolsEngine.search_medical_knowledgebase(message)
        amb_dispatch = MCPToolsEngine.dispatch_ambulance_unit(emergency_id or "EMG-GENERAL")
        tools_invoked.extend(["search_medical_knowledgebase", "dispatch_ambulance_unit"])
        context_blocks.append(f"Medical Guidance ({med_kb['topic']}):")
        for step in med_kb['guidance']:
            context_blocks.append(f"  - {step}")
        context_blocks.append(f"Dispatched: {amb_dispatch['unit_dispatched']['name']} (ETA {amb_dispatch['unit_dispatched']['eta_minutes']} min)")

    elif is_hospital_query:
        hosp = MCPToolsEngine.find_nearby_hospitals_and_facilities("hospital")
        tools_invoked.append("find_nearby_hospitals_and_facilities(hospital)")
        names = [f"{h['name']} ({h['distance_km']} km, ETA {h['eta_minutes']} min, {h.get('er_beds_free', 0)} ER beds free)" for h in hosp["facilities"]]
        context_blocks.append(f"Nearby Medical Facilities: {'; '.join(names)}")

    # Prompt Gemini LLM with exact user message + tailored directives
    if genai_client:
        if is_eta_query and not is_first_aid_query:
            directive = ("Provide a complete, clear answer giving the exact ETA in minutes (7-9 min), assigned ambulance details, and 3 key actions for the caller while waiting (e.g. keep phone line clear, unlock front door, turn on porch lights).")
            max_tokens = 600
        elif is_first_aid_query:
            directive = ("Provide a complete, medically accurate, step-by-step first aid guide based on Red Cross & Mayo Clinic protocols. Use clear numbered steps with bold headers. Include emergency dispatch details at the end.")
            max_tokens = 1000
        elif is_hospital_query:
            directive = ("List the nearest emergency hospitals with distance, ETA, and free ER beds clearly.")
            max_tokens = 600
        else:
            directive = ("Provide a complete, helpful, direct answer tailored to the user's emergency query.")
            max_tokens = 600

        system_inst = "You are MCP-RESQ Emergency Response AI. Start directly with the answer without preamble or self-introductions. Use bold text for key terms."

        prompt = (f"User Question: \"{message}\"\n\n"
                  f"Active Emergency Info & MCP Tools Context:\n"
                  f"{chr(10).join(context_blocks) if context_blocks else 'Response Units Status: Ambulance A-12 (ETA 7 mins, 2.4 km away), Fire Unit F-04 (ETA 9 mins), Rescue Team R-02 (ETA 5 mins)'}\n\n"
                  f"Directive: {directive}")

        reply_text = call_gemini_with_fallback(prompt, system_instruction=system_inst, max_tokens=max_tokens)
        if reply_text:
            return {
                "reply": reply_text.strip(),
                "tools_invoked": tools_invoked or ["lookup_emergency_resources", "gemini_3.5_flash_llm"],
                "emergency_id": emergency_id
            }

    # Fallback to Local MCP Chat Response if Gemini API Key fails or returns empty
    fallback_reply = generate_mcp_fallback_reply(message, context_blocks, active_emergency, is_eta_query, is_first_aid_query, is_hospital_query)
    return {
        "reply": fallback_reply,
        "tools_invoked": tools_invoked or ["mcp_fallback_engine"],
        "emergency_id": emergency_id
    }


def generate_mcp_fallback_reply(message: str, context_blocks: List[str], active_emergency: Any, is_eta_query: bool = False, is_first_aid_query: bool = False, is_hospital_query: bool = False) -> str:
    msg_lower = message.lower()

    # ETA / Timing Query
    if is_eta_query and not is_first_aid_query:
        if active_emergency:
            return (f"⏱️ **ESTIMATED ARRIVAL TIME**: **7 - 9 minutes**\n\n"
                    f"• **Assigned Unit**: {active_emergency.get('unit_name', 'Ambulance A-12')} (ALS)\n"
                    f"• **Current Distance**: 2.4 km away from your location\n"
                    f"• **Destination Hospital**: City Emergency Trauma Hospital (14 ER beds active)\n\n"
                    f"**While waiting for emergency responders**:\n"
                    f"1. **Keep your phone line clear** in case emergency dispatch calls back.\n"
                    f"2. **Unlock the front door** so paramedics can enter immediately.\n"
                    f"3. **Turn on exterior lights** (if nighttime) and post someone outside to flag down the ambulance.")

        return ("⏱️ **ESTIMATED ARRIVAL TIME**: **7 - 9 minutes**\n\n"
                "• **Assigned Unit**: Ambulance A-12 (Advanced Life Support)\n"
                "• **Current Distance**: 2.4 km away\n"
                "• **Status**: En-route with live traffic prioritization\n\n"
                "**Actions while help is en-route**:\n"
                "1. Keep the patient calm and lying flat.\n"
                "2. Unlock the main entrance for paramedics.\n"
                "3. Turn on outdoor porch lights so responders locate your address quickly.")

    # Medical Neck / Spinal Fracture Query
    if any(k in msg_lower for k in ["neck", "spine", "spinal", "back", "paralyz", "broken neck", "breaks their neck", "broke neck"]):
        kb = MCPToolsEngine.search_medical_knowledgebase(message)
        steps = "\n".join([f"{g}" for g in kb["guidance"]])
        return (f"🩺 **SPINAL & CERVICAL NECK INJURY FIRST AID** *(Red Cross / Mayo Clinic Protocol)*:\n\n"
                f"{steps}\n\n"
                f"🚑 **Emergency Dispatch**: Ambulance A-12 (ALS) equipped with cervical collar and spinal board is en-route (ETA 7 mins).")

    if any(k in msg_lower for k in ["chok", "heimlich", "airway"]):
        kb = MCPToolsEngine.search_medical_knowledgebase(message)
        steps = "\n".join([f"{g}" for g in kb["guidance"]])
        return f"🩺 **CHOKING FIRST AID (AHA Protocol)**:\n\n{steps}"

    if any(k in msg_lower for k in ["bleed", "hemorrhage", "wound"]):
        kb = MCPToolsEngine.search_medical_knowledgebase(message)
        steps = "\n".join([f"{g}" for g in kb["guidance"]])
        return f"🩸 **BLEEDING CONTROL PROTOCOL (Red Cross First Aid)**:\n\n{steps}"

    if any(k in msg_lower for k in ["fire", "smoke", "flame", "explosion"]):
        return ("🔥 **FIRE EMERGENCY RESPONSE (MCP SOP)**:\n\n"
                "1. **Evacuate immediately** via fire stairwells. Do NOT use elevators.\n"
                "2. Stay below 3-foot mark to avoid carbon monoxide smoke inhalation.\n"
                "3. Touch doors with back of hand before opening.\n"
                "4. Fire Tender F-04 (Yelahanka Station) dispatched (ETA 9 mins).")

    if is_hospital_query:
        return ("🏥 **Nearest Emergency Hospitals**:\n\n"
                "1. **City Emergency Trauma Hospital** (3.2 km, ETA 8 min) — Level 1 Trauma, 14 ER beds free\n"
                "2. **Metro Care Specialty Hospital** (4.5 km, ETA 12 min) — Level 2 Trauma, 8 ER beds free")

    return (f"🚨 **MCP-RESQ Emergency Response AI**: Ambulance A-12 (ETA 7 mins) and Heavy Rescue Team R-02 (ETA 5 mins) are active. "
            "Please specify if you need immediate Medical first aid, Fire evacuation, or Hospital locations.")


