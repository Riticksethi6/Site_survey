# site_conditions_tab.py – Site Conditions & Safety
# Complete version with all fields mapped to template.docx
# Includes best practices prompts, conditional notes, and all return keys

import streamlit as st

def build_site_conditions_inputs():
    st.subheader("4. Site Conditions & Safety")

    st.markdown("**Please provide details to help assess site suitability for autonomous mobile robots.**")

    col1, col2 = st.columns(2)

    with col1:
        other_agvs = st.text_input(
            "Presence of Other AGVs / AMRs / Automated Equipment",
            placeholder="e.g. existing AGVs, conveyors, AS/RS, etc.",
            key="other_agvs"
        )

        other_traffic = st.text_input(
            "Presence of Trucks / Forklifts / Pedestrians",
            placeholder="Describe traffic density, peak times, shared areas",
            key="other_traffic"
        )

        ground_gaps_mm = st.number_input(
            "Ground Gaps / Depressions / Expansion Joints [mm width/depth]",
            min_value=0.0,
            value=0.0,
            step=1.0,
            help="Important for wheel/tracking stability. Max recommended gap < 20 mm.",
            key="ground_gaps_mm"
        )

        ramp_gradient_deg = st.number_input(
            "Ramp Gradient [°]",
            min_value=0.0,
            max_value=15.0,
            value=0.0,
            step=0.5,
            help="XPL/XQE typically max 5–10% (≈3–6°). Steeper ramps may require special config.",
            key="ramp_gradient_deg"
        )

    with col2:
        parking_area = st.text_area(
            "Vehicle Parking & Rest Area Description",
            height=80,
            placeholder="e.g. dedicated charging/parking zones, size, number of spots, location",
            key="parking_area"
        )

        charging_status = st.text_area(
            "Charging Area Status / Requirements",
            height=80,
            placeholder="e.g. existing stations, power availability, space for new chargers, fire safety",
            key="charging_status"
        )

        whiteboard_workers = st.number_input(
            "Number of Whiteboard / Manual Forklift Workers (Day)",
            min_value=0,
            value=0,
            step=1,
            key="whiteboard_workers"
        )

        night_workers = st.number_input(
            "Number of Night-Shift Forklift Workers",
            min_value=0,
            value=0,
            step=1,
            key="night_workers"
        )

    battery_heating = st.checkbox(
        "Battery Heating Required (for cold storage < -15°C)",
        value=False,
        key="battery_heating"
    )

    # Additional fields for template completeness
    warehouse_area = st.text_input(
        "Warehouse / Workshop Area (sq m)",
        placeholder="Approximate total floor area",
        key="warehouse_area"
    )

    storage_locations = st.number_input(
        "Number of Storage Locations / Pallet Positions",
        min_value=0,
        value=0,
        step=100,
        key="storage_locations"
    )

    environment = st.selectbox(
        "Environment Type",
        ["Normal (ambient)", "Cold Storage (0 to -25°C)", "Freezer (<-25°C)", "Explosion-Proof", "High Temperature", "Wash-down / Hygienic", "Other"],
        key="environment"
    )

    safety_assessment = st.text_area(
        "Safety Assessment (pedestrian traffic, standards, hazards)",
        height=100,
        placeholder="e.g. high pedestrian density, required safety standards (ISO 3691-4, CE), emergency stop zones, speed limits",
        key="safety_assessment"
    )

    network_coverage = st.text_area(
        "Wireless / RF Survey Details (coverage, access points, interference)",
        height=100,
        placeholder="e.g. Wi-Fi coverage map, 5G/4G availability, metal racks causing interference, planned survey",
        key="network_coverage"
    )

    positioning_req = st.text_area(
        "Positioning Accuracy / Docking Requirements",
        height=80,
        placeholder="e.g. ±10 mm docking accuracy needed, laser reflector-free preferred, QR code or natural feature navigation",
        key="positioning_req"
    )

    docking_equipment = st.text_area(
        "Related Equipment to Dock (elevators, arms, conveyors, doors, etc.)",
        height=80,
        placeholder="List equipment AMR needs to interact with (e.g. roller conveyor, pallet dispenser, wrapping machine)",
        key="docking_equipment"
    )

    special_demand = st.text_area(
        "Special Demands (explosion-proof, temp adaptability, monitoring, etc.)",
        height=80,
        placeholder="e.g. ATEX Zone 1/2, -30°C to +40°C operation, remote monitoring, fleet size scalability",
        key="special_demand"
    )

    # Return all fields – charging_stations reused from charging_status for template compatibility
    return {
        "other_agvs": other_agvs,
        "other_traffic": other_traffic,
        "ground_gaps_mm": ground_gaps_mm,
        "ramp_gradient_deg": ramp_gradient_deg,
        "parking_area": parking_area,
        "charging_status": charging_status,
        "whiteboard_workers": whiteboard_workers,
        "night_workers": night_workers,
        "battery_heating": battery_heating,
        "warehouse_area": warehouse_area,
        "storage_locations": storage_locations,
        "environment": environment,
        "safety_assessment": safety_assessment,
        "network_coverage": network_coverage,
        "positioning_req": positioning_req,
        "docking_equipment": docking_equipment,
        "special_demand": special_demand,
        "charging_stations": charging_status  # reused for template
    }