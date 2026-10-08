# MCP-ResQ Backend Engine

The **MCP-ResQ Backend** is a high-performance Python FastAPI service integrated with **Google Gemini AI LLMs**, **Model Context Protocol (MCP) Tools Engine**, and **Twilio Voice AI Webhooks**. It powers real-time emergency decision support, speech-to-text voice dispatch, responder coordination, and clinical first aid retrieval.

---

## 🌟 Key Features

### 1. 🤖 Gemini AI LLM & Model Context Protocol (MCP) Engine
- **Multi-Model Fallback**: Automated fallback chain (`gemini-3.5-flash` → `gemini-3.1-pro-preview` → `gemini-3.5-flash-lite` → `gemini-3.8-flash`).
- **Intent Triage Classification**: Dynamically identifies query intent (Medical First Aid, Fire Evacuation, Hazmat Containment, Heavy Rescue, Hospital Lookup, ETA/Status).
- **Clinical First Aid Retrieval**: Invokes Red Cross, Mayo Clinic, and AHA guidelines for spinal neck trauma, choking (Heimlich), bleeding control, CPR, and burns.

### 2. 📞 Voice Call AI & Speech-to-Text Engine (`voice_service.py`) *(Latest Feature)*
- **Twilio Voice Webhook (`POST /api/voice/webhook`)**: Receives live phone calls, transcribes caller speech in real-time, and runs emergency analysis.
- **TwiML Text-to-Speech Output**: Generates TwiML `<Say voice="Polly.Amy-Neural">` XML responses so the AI speaks emergency instructions back to the phone caller.
- **Audio File Transcription (`POST /api/voice/transcribe`)**: Upload `.wav`, `.mp3`, `.m4a`, `.webm` recordings for AI transcription and MCP incident extraction.
- **Outbound Voice Call Dispatch (`POST /api/voice/call-responder`)**: Initiates automated outbound AI phone calls to responders or victims.
- **Twilio Security Authentication**: Signature verification via `TWILIO_AUTH_TOKEN` to prevent webhook spoofing.

### 3. 🚑 MCP Specialized Tools Registry (`mcp_server.py`)
- `search_medical_knowledgebase`: Clinical first aid guidance lookup.
- `dispatch_ambulance_unit`: ALS ambulance unit dispatch & ER bed availability check.
- `call_fire_engine_station`: Fire engine station alert & municipal hydrant locator.
- `generate_fire_evacuation_plan`: Floor-by-floor fire & smoke safety route generation.
- `locate_nearby_extinguishers_and_suppression`: CO2, foam, and hydrant asset locator.
- `call_hazmat_containment_squad`: Chemical & toxic gas leak squad dispatch.
- `assess_gas_leak_evacuation_zone`: Upwind/crosswind hazard isolation zone assessment.
- `dispatch_heavy_rescue_squad`: Structural collapse squad dispatch with acoustic search drones & hydraulic cutters.
- `verify_incident_details`: Location verification, hazard scoring, and confidence checking.

---

## 🛠️ Project Structure & Files

```
backend/
├── main.py             # FastAPI App, REST endpoints, CORS, static file server
├── gemini_service.py   # Gemini LLM integration, intent classification, prompt formatting
├── mcp_server.py       # Model Context Protocol (MCP) tools, incident DBs, SOP protocols
├── voice_service.py    # Twilio Voice webhooks, Speech-to-Text, TwiML XML voice generation
├── models.py           # Pydantic data schemas & request/response validation
├── .env.example        # Environment variable template
├── .env                # Local secrets configuration (Git ignored)
├── requirements.txt    # Python package dependencies
└── README.md           # Backend documentation (this file)
```

---

## ⚙️ Environment Variables Setup

Create a `.env` file inside the `backend/` folder (or copy from `.env.example`):

```env
# Gemini AI API Key (Get from https://ai.google.dev/)
GEMINI_API_KEY=your_gemini_api_key_here

# Twilio Voice & Phone Call Integration (Get from https://www.twilio.com/console)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

# Backend Server Port
HOST=127.0.0.1
PORT=8000
```

---

## 🚀 Installation & Running Locally

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the FastAPI server**:
   ```bash
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Verify server status**:
   Open `http://127.0.0.1:8000/api/health` or Swagger Docs at `http://127.0.0.1:8000/docs`.

---

## 📡 API Endpoints Reference

### 1. System & Health
| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | `GET` | Health check & Gemini/MCP status |

### 2. Emergency Management
| Endpoint | Method | Description |
|---|---|---|
| `/api/emergencies` | `POST` | Create emergency report with AI analysis |
| `/api/emergencies/{id}` | `GET` | Get emergency details by ID |
| `/api/emergencies/{id}/tracking` | `GET` | Get live response unit tracking & ETA |

### 3. Response Units & Facilities
| Endpoint | Method | Description |
|---|---|---|
| `/api/units` | `GET` | List all response units (Ambulance, Fire, Rescue) |
| `/api/units/{id}/dispatch` | `POST` | Dispatch specific unit to emergency |
| `/api/nearby-help` | `GET` | List nearby hospitals, fire stations, police HQ |

### 4. AI Assistant & Decision Support
| Endpoint | Method | Description |
|---|---|---|
| `/api/chat` | `POST` | AI assistant query handler |
| `/api/verify` | `POST` | Verify emergency details & hazard score |
| `/api/coordinate` | `POST` | Coordinate tactical emergency plan |

### 5. Phone Call Voice & Speech-to-Text AI *(New)*
| Endpoint | Method | Description |
|---|---|---|
| `/api/voice/status` | `GET` | Check Twilio Voice & Auth Token status |
| `/api/voice/webhook` | `POST` | Twilio Voice Webhook for real-time speech-to-text dispatch |
| `/api/voice/transcribe` | `POST` | Upload audio file (.wav, .mp3) for AI transcription |
| `/api/voice/simulate` | `POST` | Simulate voice call speech input for testing |
| `/api/voice/call-responder` | `POST` | Trigger automated outbound AI phone call to responder/victim |

### 6. MCP Services Testing
| Endpoint | Method | Description |
|---|---|---|
| `/api/mcp/{service}/test` | `GET` / `POST` | Test MCP tools (location, resource, hospital, verification) |

---

## 📞 How to Connect Live Twilio Phone Number

1. Log in to [Twilio Console](https://www.twilio.com/console).
2. Go to **Phone Numbers -> Manage -> Active Numbers**.
3. Select your phone number and set **A CALL COMES IN**:
   - **Webhook URL**: `https://<YOUR-DOMAIN>/api/voice/webhook` (or use `ngrok http 8000` for testing)
   - **Method**: `POST`
4. When a user or responder calls the number, Twilio sends caller speech to your backend, Gemini & MCP analyze the emergency, and the AI speaks real-time instructions back over the phone call!
