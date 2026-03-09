# data_flow_tab.py

import streamlit as st


def build_data_flow_inputs():
    st.subheader("3. Data Flow & Integration")

    system_integration = st.multiselect(
        "System Integration",
        [
            "Fire Door",
            "Fire Alarm",
            "Conveyor",
            "Automatic Doors",
            "Production Units",
            "Elevators",
            "Dock Doors",
            "Other",
        ],
        key="system_integration"
    )

    integration_to_your_system_required = st.radio(
        "Integration to your system required?",
        ["Yes", "No"],
        horizontal=True,
        key="integration_to_your_system_required"
    )

    systems_to_integrate = []
    if integration_to_your_system_required == "Yes":
        systems_to_integrate = st.multiselect(
            "What all systems need to be integrated?",
            [
                "ERP",
                "WMS",
                "Fleet Manager",
                "PLCs for Production",
                "PLCs for Conveyors",
            ],
            key="systems_to_integrate"
        )

    connections = st.text_input(
        "Other Connections / Interfaces",
        placeholder="Example: scanners, lifts, dock systems, barcode systems",
        key="connections"
    )

    connections_details = st.text_area(
        "Connection / Interface Details",
        height=120,
        placeholder="Describe what data needs to be exchanged and with which systems.",
        key="connections_details"
    )

    data_flow_text = st.text_area(
        "Data Flow Description",
        height=140,
        placeholder="Describe how orders, tasks, confirmations, alarms, and status updates should flow between systems.",
        key="data_flow_text"
    )

    system_integration_summary = ", ".join(system_integration) if system_integration else ""
    systems_to_integrate_summary = ", ".join(systems_to_integrate) if systems_to_integrate else ""

    return {
        "system_integration": system_integration,
        "system_integration_summary": system_integration_summary,
        "integration_to_your_system_required": integration_to_your_system_required,
        "systems_to_integrate": systems_to_integrate,
        "systems_to_integrate_summary": systems_to_integrate_summary,
        "connections": connections,
        "connections_details": connections_details,
        "data_flow_text": data_flow_text,
    }