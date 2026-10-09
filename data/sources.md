# Data Provenance & Open Dataset Attribution

**Project**: MCP-ResQ — Emergency Resource Coordination Platform  
**Team**: AGENTIX  
**Architecture Principle**: AI Reasons. MCP Connects. Python Verifies.  
**Last Updated**: October 8, 2026  

---

## 1. Data Governance Policy
In strict compliance with hackathon safety, ethical guidelines, and legal requirements:
* **No Confidential or Protected Health Information (PHI)**: No real patient records, personal identities, or classified dispatch communications are collected, stored, or distributed.
* **No Unauthorized Scraping**: Datasets referenced are publicly licensed for research and prototype demonstration under permissive open licenses (ODbL, CC-BY 4.0, MIT, or Open Government Data License).
* **Clear Provenance Tagging**: Every API payload indicates `source`, `data_status` (`LIVE`, `SIMULATED`, or `HISTORICAL`), `confidence`, and `timestamp`.
* **Zero False "Live" Claims**: Demo coordinates and synthetic fleet trajectories are explicitly labeled `SIMULATED LIVE TRACKING`.

---

## 2. Dataset Reference Catalog

### 2.1 Geographic & Landmark Coordinates (Bengaluru Sector)
* **Dataset / Source**: OpenStreetMap (OSM) / Public Geographic Gazetteer for Bengaluru Urban
* **URL**: [https://www.openstreetmap.org](https://www.openstreetmap.org)
* **License**: Open Database License (ODbL) 1.0
* **Retrieval Date**: October 2026
* **Purpose**: Provides realistic coordinates, station depots, and road arterial names (MG Road, Indiranagar, Brigade Road, Cubbon Park, Central Fire Station) for authentic spatial calculations.
* **Transformations**: Extracted landmark center points to establish deterministic coordinates for synthetic routing tests.

### 2.2 Emergency Triage & Incident Classification Reference
* **Dataset / Source**: Synthetic Emergency Triage Benchmark (adapted from Kaggle Open Triagegeist / Emergency Severity Index (ESI) Public Domain Guidelines)
* **URL**: [https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)
* **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
* **Retrieval Date**: October 2026
* **Purpose**: Provides clinical baseline distributions for incident severities (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), required resource ratios, and triage rules.
* **Transformations**: Translated into deterministic Python verification dictionaries mapping 16 incident classifications (`cardiac`, `chemical_spill`, `building_collapse`, etc.) to specific capability requirements.

### 2.3 Hospital Capacity & Trauma Readiness Model
* **Dataset / Source**: Public Hospital Facility & Bed Inventory Guidelines (adapted from Open Government Data India (OGD) / National Health Mission Hospital Metrics)
* **URL**: [https://data.gov.in](https://data.gov.in)
* **License**: National Data Sharing and Accessibility Policy (NDSAP) / Government Open Data License - India
* **Retrieval Date**: October 2026
* **Purpose**: Benchmark parameters for hospital facility modeling: ICU availability, emergency bed capacities, surgical readiness, and trauma level tiers (Level 1, 2, 3).
* **Transformations**: Synthesized into a balanced municipal hospital inventory for Central and East Bengaluru response sectors.

---

## 3. Data Dictionary

| Entity | Field | Type | Description | Provenance |
|---|---|---|---|---|
| `Emergency` | `id` | String | Unique incident identifier (e.g., `EMG-1001`) | Generated |
| `Emergency` | `type` | Enum (16) | Standardized classification category | Verified by Python |
| `Emergency` | `severity` | Enum (4) | ESI-aligned triage severity tier | Inferred by AI, verified by Python |
| `EmergencyUnit` | `type` | Enum (10) | Standardized emergency fleet role | Pre-seeded / Simulated |
| `EmergencyUnit` | `capabilities` | Array[String]| Specific operational skills (e.g., `hazmat`, `icu`, `extraction`) | Pre-seeded |
| `EmergencyUnit` | `status` | Enum (8) | Operational lifecycle state | Live / Simulated |
| `Hospital` | `icu_available` | Boolean | Real-time ICU bed readiness flag | Simulated Facility Telemetry |
| `Tracking` | `distance_km` | Float | Haversine or traffic-aware distance | Verified by Python / Maps MCP |
| `Provenance` | `data_status` | String | Data validity state (`LIVE`, `SIMULATED`, `VERIFIED`) | System Tagged |
