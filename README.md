
# MCP-RESQ

    AI-powered emergency resource coordination using Model Context Protocol (MCP), enabling an agent to connect incident, resource, safety, and location capabilities for verified and explainable emergency decision support.
=======
# MCP-ResQ

MCP-ResQ is a web-based emergency response platform integrating emergency reporting, unit tracking, nearby assistance lookup, resource management, and system monitoring through the Model Context Protocol (MCP). It enables coordinated emergency resource management with verified and explainable decision support.

## Overview

When the backend is unavailable, the app runs in fully functional demo mode with mock data — no server required to get started.

## Live Pages

| Page | Description |
|------|-------------|
| Home |Emergency assistance overview with quick emergency types |
| Emergency |Report an emergency, system analysis & emergency ID creation |
| Tracking | Live response map with unit locations, ETA, and progress |
| Nearby |Nearby hospitals, fire stations, police, and rescue services |
| Assistant | AI chat for emergency questions and status inquiries |
| Control  Operator view: stats, active emergency, activity log |
| Resources | Monitor and dispatch ambulance, fire, and rescue units |
| MCP | Test MCP service connectivity (location, resource, hospital, verification) |
| Verification | Validate emergency data, resources, and AI decisions |
| System | Technical status of frontend, backend, MCP, and database |

## UI Features

- Responsive sidebar collapses to icon-only mode at 800px; full navigation hides details
- Dark sidebar theme (#0b1426) with accent highlights; light cards (#ffffff) with subtle shadows
- Inter font with 9 weights (400-800) for hierarchy and emphasis
- Hero section with gradient background and large icon on home page
- Emergency type cards with 6 selector buttons (medical, fire, accident, rescue, disaster, other)
- Live response map with road pattern, user/response/hospital markers, zoom/controls
- Nearby services grid filters by type and renders cards with distance/ETA, Select/Track actions
- AI chat with persistent suggestions, bot avatars, and message history
- Control center displays 4 stat cards (available ambulances/fire units/rescue/hospitals), active emergency details, activity list
- Resource table shows unit name, type, status badge, location, with Dispatch action
- MCP service cards present 4 service test buttons (location, resource, hospital, verification) with status pills
- Verification cards check location, emergency type, resources, and AI decisions
- System monitoring displays 5 status cards (frontend, FastAPI backend, MCP, database)
- Toast notifications provide user feedback
- Breakpoints at 1100px (2-column to 1-column grid) and 800px (sidebar collapse)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, vanilla JavaScript, CSS3 (no build step, no framework) |
| Styling | CSS custom properties (colors, spacing, shadows), @media queries for responsiveness |
| Font | Inter from Google Fonts |
| API | Fetch with AbortController + 10s timeout |
| Deployment | Serve index.html from any static web server, or open directly in a browser |

## API Endpoints (FastAPI Backend)

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/health | GET | Backend health check (checkBackend()) |
| /api/units | GET | List emergency units (getUnits()) |
| /api/nearby-help | GET | Nearby emergency services (getNearbyHelp()) |
| /api/emergencies | POST | Create new emergency (createEmergency()) |
| /api/emergencies/{id} | GET | Retrieve emergency by ID (getEmergency()) |
| /api/emergencies/{id}/tracking | GET | Get tracking data (getTracking()) |
| /api/units/{id}/dispatch | POST | Dispatch a unit to emergency (dispatchUnit()) |
| /api/verify | POST | Verify emergency data (verifyEmergency()) |
| /api/coordinate | POST | Coordinate response (coordinateResponse()) |
| /api/chat | POST | Send chat message (sendChatMessage()) |
| /api/mcp/{service}/test | GET|POST | Test MCP service (testMCPService()) services: location, resource, hospital, verification |

All endpoints expect/return JSON with {error} fallback on failure. The frontend gracefully falls back to demo data when any request fails (network error, timeout, non-2xx status).

## Demo Mode

When the FastAPI backend (http://127.0.0.1:8000) is unreachable, the app auto-enters demo mode:

- Uses demoUnits and demoNearby arrays defined in script.js
- Emergency creation generates a DEMO-{timestamp} ID
- Tracking shows the best-match demo unit (ambulance for medical, fire for fire, rescue for rescue)
- Resource stats, nearby list, and MCP tests all serve demo data
- All interactive features work without a backend

## Getting Started

1. **Open the app** - drag index.html into any browser, or serve from a local web server:

   ```bash
   npx serve           # or: python -m http.server 8000
   ```

2. **Ensure backend is running** (optional) - FastAPI server at http://127.0.0.1:8000 with the required endpoints
3. **Start exploring** - the app loads the Home page; navigate via the sidebar or hero button

## Design Notes

- **Color palette** - sidebar #0b1426, cards #ffffff, primary #e53935 (red accent), blues/greens/oranges/purples for status badges, muted #718096 for secondary text
- **Shadow** - 0 10px 30px rgba(15, 23, 42, 0.07) applied to cards and the main app shell
- **Responsive** - at 800px sidebar collapses, grid columns stack, navigation details hide; at 1100px grids switch to 1 column
- **Accessibility** - :focus outlines on inputs/buttons, color contrast meets WCAG AA for text vs. background, box-sizing: border-box
- **Micro-interactions** - button hover transforms, progress bar width animation, toast enter animation, hover states on emergency-type cards
- **Visual hierarchy** - Inter weights: 800 for nav section labels, 700 for headings, 600 for body text, 500 for subtle text

## Project Structure

```
MCP-RESQ/
├── index.html        # Full UI markup (10 pages, sidebar, header, content sections)
├── style.css         # All styling - colors, layout, responsive, animations
├── script.js         # All logic - API calls, state management, UI updates, event handlers
└── README.md         # This file
```

## Scripts & Controls

### Keyboard shortcuts (within the app)

- **Enter** in chat input - send message
- **Refresh** (Refresh buttons) - reload data for tracking/nearby/resources
- **+ / - / Mouse wheel** - map zoom controls
- **Select / Track** - on nearby service cards

### Global event listeners (script.js)

- .nav-item clicks - show page
- .emergency-type clicks - populate description + show emergency page
- [data-suggestion] clicks - populate emergency description textarea
- [data-page-target] - show target page from hero CTA
- .filter-button - filter nearby services by type
- [data-service] - test MCP service connectivity
- .chat-suggestions - quick preset questions
- Form submit - send chat message
- Esc / arrow keys - not bound (keyboard nav not implemented)

### Demo data locations (script.js)

- demoUnits - 5 units: 2 ambulances, 2 fire units, 1 rescue team
- demoNearby - 6 services: 2 hospitals, 1 fire station, 1 police, 1 rescue base
- pageData - page titles/subtitles for the header
- state - app state: backendConnected, emergency, userLocation, tracking, units, nearby, currentFilter, mapScale

## Extending the App

Add new emergency types - update:

1. classifyEmergency() in script.js (line 286)
2. getEmergencyIcon() / getEmergencyName() mappings
3. Emergency-type selector buttons in index.html
4. New card in hero grid or elsewhere

Add new MCP service - update:

1. testMCPService() call site in script.js
2. Add service card in index.html MCP grid
3. Status badge color if needed ('.service-status' in style.css)

Add new page - create a section class="page" id="new-page" in index.html, add nav button, wire up in showPage().

## License

MIT - feel free to use, modify, and distribute. Attribution to original creators appreciated.

---

Generated from the MCP-RESQ codebase on 2026-10-08. Live demo: open index.html in a browser.
>>>>>>> Stashed changes
