# site_conditions_tab.py

import streamlit as st


def build_site_conditions_inputs():
    st.subheader("4. Site Conditions & Safety")

    col1, col2 = st.columns(2)

    with col1:
        other_agvs = st.text_input(
            "Other AGVs / AMRs / Automated Equipment on Site",
            placeholder="Example: existing AGVs, conveyors, AS/RS",
            key="other_agvs"
        )

        other_traffic = st.text_input(
            "Other Traffic on Site",
            placeholder="Example: forklifts, trucks, pedestrians",
            key="other_traffic"
        )

        ramp_gradient_deg = st.number_input(
            "Ramp Gradient [°]",
            min_value=0.0,
            max_value=15.0,
            value=0.0,
            step=0.5,
            key="ramp_gradient_deg"
        )

    with col2:
        parking_area = st.text_area(
            "Vehicle Parking / Rest Area",
            height=90,
            placeholder="Describe where vehicles can wait or park.",
            key="parking_area"
        )

        charging_status = st.text_area(
            "Charging Area Details",
            height=90,
            placeholder="Describe charger location, power availability, and space.",
            key="charging_status"
        )

    battery_heating = st.checkbox(
        "Battery Heating Required",
        value=False,
        key="battery_heating"
    )

    network_coverage = st.text_area(
        "Wireless / RF Details",
        height=110,
        placeholder="Example: Wi-Fi coverage, access points, dead zones, interference areas",
        key="network_coverage"
    )

    return {
        "other_agvs": other_agvs,
        "other_traffic": other_traffic,
        "ramp_gradient_deg": ramp_gradient_deg,
        "parking_area": parking_area,
        "charging_status": charging_status,
        "battery_heating": battery_heating,
        "network_coverage": network_coverage,
        "charging_stations": charging_status,
    }