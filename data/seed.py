"""Deterministic Seed Dataset for MCP-ResQ Emergency Response Platform.

Populates SQLite with a 10-role responder fleet, regional trauma hospitals,
active multi-incident scenarios, simulated tracking, and designated safe zones.

All synthetic data is clearly labelled as decision-support simulation data.
"""

import json
from typing import Optional
from backend.database import Base, SessionLocal, engine
from backend.models import Alert, Emergency, EmergencyUnit, Hospital, Tracking


def seed_database(force: bool = False) -> None:
    """Create database tables and seed comprehensive emergency fleet, facilities, and incidents."""
    if force:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already populated
        if not force and db.query(EmergencyUnit).count() >= 10:
            return

        # 1. 10-Role Responder Fleet
        units = [
            EmergencyUnit(
                id="AMB-101",
                name="Ambulance A-12",
                type="ambulance",
                status="dispatched",
                location="MG Road Station",
                latitude=12.9756,
                longitude=77.6066,
                capabilities=json.dumps(["basic_life_support", "advanced_life_support", "trauma"]),
                capacity=2,
                workload=1,
            ),
            EmergencyUnit(
                id="AMB-102",
                name="Ambulance B-04",
                type="ambulance",
                status="available",
                location="Indiranagar Depot",
                latitude=12.9784,
                longitude=77.6408,
                capabilities=json.dumps(["advanced_life_support", "cardiac_monitor", "pediatric"]),
                capacity=2,
                workload=0,
            ),
            EmergencyUnit(
                id="FIRE-201",
                name="Fire Engine F-01",
                type="fire",
                status="available",
                location="South Fire Station",
                latitude=12.9352,
                longitude=77.6245,
                capabilities=json.dumps(["structural_fire", "high_reach_ladder", "water_pump"]),
                capacity=6,
                workload=0,
            ),
            EmergencyUnit(
                id="FIRE-202",
                name="Hazmat Engine F-02",
                type="fire",
                status="available",
                location="Central Fire Station",
                latitude=12.9800,
                longitude=77.5900,
                capabilities=json.dumps(["hazmat", "chemical_containment", "foam_dispenser", "decontamination"]),
                capacity=5,
                workload=0,
            ),
            EmergencyUnit(
                id="RES-301",
                name="Rescue Squad Alpha",
                type="rescue",
                status="available",
                location="Disaster Management Base 1",
                latitude=12.9600,
                longitude=77.6100,
                capabilities=json.dumps(["heavy_extraction", "building_collapse", "confined_space", "cutting_gear"]),
                capacity=8,
                workload=0,
            ),
            EmergencyUnit(
                id="POL-401",
                name="Patrol Interceptor P-09",
                type="police",
                status="available",
                location="Cubbon Park Post",
                latitude=12.9750,
                longitude=77.5920,
                capabilities=json.dumps(["perimeter_control", "traffic_clearing", "armed_security", "crowd_control"]),
                capacity=4,
                workload=0,
            ),
            EmergencyUnit(
                id="MED-501",
                name="Field Medical Team M-01",
                type="medical_team",
                status="available",
                location="Victoria Hospital Compound",
                latitude=12.9620,
                longitude=77.5750,
                capabilities=json.dumps(["field_triage", "emergency_physician", "resuscitation", "mass_casualty"]),
                capacity=4,
                workload=0,
            ),
            EmergencyUnit(
                id="TRM-601",
                name="Mobile Trauma Unit T-01",
                type="trauma_team",
                status="available",
                location="Bowring Hospital Annex",
                latitude=12.9820,
                longitude=77.6050,
                capabilities=json.dumps(["trauma_surgery", "blood_transfusion", "ventilator", "icu_transport"]),
                capacity=2,
                workload=0,
            ),
            EmergencyUnit(
                id="HELI-701",
                name="Air Rescue Lifeflight H-01",
                type="helicopter",
                status="available",
                location="HAL Helipad Base",
                latitude=12.9500,
                longitude=77.6680,
                capabilities=json.dumps(["aeromedical_evac", "rapid_long_range", "winch_rescue", "high_speed"]),
                capacity=2,
                workload=0,
            ),
            EmergencyUnit(
                id="FA-801",
                name="Rapid First Aid Squad FA-01",
                type="first_aid",
                status="available",
                location="MG Road Metro Center",
                latitude=12.9755,
                longitude=77.6060,
                capabilities=json.dumps(["basic_life_support", "oxygen_administration", "wound_dressing", "aed"]),
                capacity=2,
                workload=0,
            ),
            EmergencyUnit(
                id="EVAC-901",
                name="Civil Evacuation Carrier E-01",
                type="evacuation_unit",
                status="available",
                location="Majestic Transport Terminal",
                latitude=12.9770,
                longitude=77.5710,
                capabilities=json.dumps(["mass_evac", "high_capacity", "disabled_access", "stretcher_bays"]),
                capacity=20,
                workload=0,
            ),
            EmergencyUnit(
                id="DRT-902",
                name="Disaster Response Taskforce D-01",
                type="disaster_response_team",
                status="available",
                location="SNDRF Regional Base",
                latitude=12.9200,
                longitude=77.6100,
                capabilities=json.dumps(["flood_rescue", "inflatable_boats", "seismic_search", "thermal_imaging"]),
                capacity=12,
                workload=0,
            ),
        ]

        # 2. Regional Medical Facilities
        hospitals = [
            Hospital(
                id="H-101",
                name="City Emergency Hospital",
                type="hospital",
                latitude=12.9730,
                longitude=77.5960,
                address="Central Bengaluru, Zone 1",
                emergency_available=True,
                available_beds=14,
                total_beds=120,
                icu_available=True,
                icu_beds=6,
                trauma_level=1,
                trauma_support=True,
                capabilities=json.dumps(["trauma_level_1", "icu", "cardiac_cath", "burn_unit", "neurosurgery"]),
                contact="+91-80-2222-0000",
            ),
            Hospital(
                id="H-102",
                name="Memorial Trauma & Surgical Center",
                type="hospital",
                latitude=12.9850,
                longitude=77.6100,
                address="East Bengaluru, Sector 3",
                emergency_available=True,
                available_beds=8,
                total_beds=90,
                icu_available=True,
                icu_beds=4,
                trauma_level=1,
                trauma_support=True,
                capabilities=json.dumps(["trauma_level_1", "orthopedic_surgery", "vascular", "blood_bank"]),
                contact="+91-80-2333-1111",
            ),
            Hospital(
                id="H-103",
                name="Metro General Hospital",
                type="hospital",
                latitude=12.9650,
                longitude=77.5850,
                address="West Zone, Medical Enclave",
                emergency_available=True,
                available_beds=18,
                total_beds=150,
                icu_available=False,
                icu_beds=0,
                trauma_level=2,
                trauma_support=False,
                capabilities=json.dumps(["general_emergency", "pediatric", "radiology", "pharmacy"]),
                contact="+91-80-2444-2222",
            ),
            Hospital(
                id="H-104",
                name="Cantonment Health Post",
                type="clinic",
                latitude=12.9900,
                longitude=77.6000,
                address="North Central Sector",
                emergency_available=True,
                available_beds=5,
                total_beds=25,
                icu_available=False,
                icu_beds=0,
                trauma_level=3,
                trauma_support=False,
                capabilities=json.dumps(["outpatient", "basic_triage", "stabilization"]),
                contact="+91-80-2555-3333",
            ),
        ]

        # 3. Seed Incidents
        emergencies = [
            Emergency(
                id="EMG-1001",
                description="Traffic collision at MG Road junction with 2 casualties.",
                type="road_accident",
                priority="HIGH",
                severity="HIGH",
                status="dispatched",
                latitude=12.9716,
                longitude=77.5946,
                accuracy=10.0,
                affected_count=2,
                critical_count=1,
                required_resources='{"ambulance": 1}',
                assigned_unit_id="AMB-101",
                assigned_hospital_id="H-101",
            ),
            Emergency(
                id="EMG-1002",
                description="Hazardous chemical breach in industrial laboratory sector.",
                type="chemical_spill",
                priority="CRITICAL",
                severity="CRITICAL",
                status="active",
                latitude=12.9800,
                longitude=77.6000,
                accuracy=12.0,
                affected_count=4,
                critical_count=2,
                required_resources='{"ambulance": 2, "rescue": 1}',
            ),
            Emergency(
                id="EMG-1003",
                description="Structural electrical fire on 3rd floor commercial building.",
                type="fire",
                priority="HIGH",
                severity="HIGH",
                status="active",
                latitude=12.9650,
                longitude=77.5850,
                accuracy=8.0,
                affected_count=1,
                critical_count=0,
                required_resources='{"fire": 2, "ambulance": 1}',
            ),
        ]

        # 4. Live Tracking Telemetry
        trackings = [
            Tracking(
                emergency_id="EMG-1001",
                unit_id="AMB-101",
                latitude=12.9736,
                longitude=77.6006,
                distance_km=1.8,
                eta_minutes=4,
                progress=35,
                speed_kmh=48.0,
                traffic_condition="moderate",
                origin="MG Road Station",
                destination="Incident EMG-1001 (12.9716, 77.5946)",
                data_status="SIMULATED LIVE TRACKING",
            ),
        ]

        # 5. Seed Alerts
        alerts = [
            Alert(
                title="Chemical Spill Exclusion Advisory",
                message="Avoid Industrial Sector 4 within 500m due to vapor cloud dispersal.",
                severity="CRITICAL",
                area="Industrial Sector 4",
                is_active=True,
                emergency_id="EMG-1002",
            )
        ]

        db.add_all(units)
        db.add_all(hospitals)
        db.add_all(emergencies)
        db.add_all(trackings)
        db.add_all(alerts)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(force=True)
    print("MCP-ResQ database seeded successfully with 10-role fleet and facility matrix.")
