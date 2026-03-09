# site_conditions_tab.py – Site Conditions & Safety
# Complete version with all fields mapped to template.docx
# Includes best practices prompts, conditional notes, and all return keys

import streamlit as st

def build_site_conditions_inputs():
    st.subheader("4. Site Conditions & Safety")

    st.markdown("**Provide details to assess site suitability for AMRs / AGVs.**")

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

    battery_heating = st.checkbox(
        "Battery Heating Required (for cold storage < -15°C)",
        value=False,
        key="battery_heating"
    )

    network_coverage = st.text_area(
        "Wireless / RF Survey Details (coverage, access points, interference)",
        height=100,
        placeholder="e.g. Wi-Fi coverage map, 5G/4G availability, metal racks causing interference, planned survey",
        key="network_coverage"
    )

    # Return all fields for template
    return {
        "other_agvs": other_agvs.strip(),
        "other_traffic": other_traffic.strip(),
        "ramp_gradient_deg": ramp_gradient_deg,
        "parking_area": parking_area.strip(),
        "charging_status": charging_status.strip(),
        "battery_heating": battery_heating,
        "network_coverage": network_coverage.strip(),
        "charging_stations": charging_status.strip()  # reused for template compatibility
    }