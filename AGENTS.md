# AGENTS.md — MCP-ResQ Operational Directives

## 1. Project Identity & Team
- **Project**: MCP-ResQ
- **Team**: AGENTIX
- **Problem Statement**: MCP (Model Context Protocol)
- **Status**: 24-hour hackathon project

---

## 2. Core Operational Principle
```
AI reasons.
MCP connects.
Python verifies.
```
- **Gemini AI**: Interprets incoming emergency scenarios, decides on tool retrieval paths, reasons over verified data, and crafts transparent, explainable response briefings.
- **MCP Servers**: Expose structured tools to fetch authoritative operational data (`incident`, `resources`, `safety`, `maps`).
- **Deterministic Python**: Executes all mathematical and constraint computations (resource gap calculation, what-if capacity changes). The AI is NEVER permitted to invent numerical gaps, route distances, or resource counts.

---

## 3. Strict Boundary Rules

### 🚫 DO NOT MODIFY `app/ui/`
A teammate is actively building the frontend in `app/ui/`.
- Do NOT touch `app/ui/`.
- Do NOT modify Streamlit styling, layouts, or UI components.
- Do NOT create UI mockups inside backend files.
- Expose all capabilities via clean, typed Python service interfaces (`process_incident()`, `simulate_resource_change()`) returning Pydantic models / structured dicts.

### 🚫 Git Rules
- **DO NOT commit or push to Git.** The user will manually stage, commit, and push.

### 🚫 Hallucination & Life-Safety Guardrails
- **MCP-ResQ is a decision-support prototype**, not an autonomous emergency dispatch system.
- Never claim the prototype replaces emergency services.
- Never fabricate emergency data, medical facts, or operational capacity.
- In fallback or demo mode, explicitly label data as synthetic/fallback.

---

## 4. Architecture Requirements
- Keep the backend completely decoupled from the UI.
- All MCP tools must have typed inputs and outputs using Pydantic.
- Maps MCP must keep Google Maps logic isolated; if credentials are missing or the API fails, fall back gracefully to synthetic campus demo coordinates.
- Maintain minimal dependencies: Python 3.12, official `mcp` SDK, `google-genai`, `pydantic`, `sqlite3`, `googlemaps`, `pytest`. No heavy or unnecessary cloud infrastructure.
