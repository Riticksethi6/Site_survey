# data_flow_tab.py

import streamlit as st


def build_data_flow_inputs():
    st.subheader("3. Data Flow & Integration")

    integration_req = st.radio(
        "Is system integration required?",
        ["Yes", "No"],
        horizontal=True,
        key="integration_req"
    )

    wms_owner = st.selectbox(
        "Which WMS is the system of record?",
        ["Customer", "EP", "Other", "No WMS"],
        key="wms_owner"
    )

    api_required = st.radio(
        "Is an API required to connect to the customer system?",
        ["Yes", "No", "Not Sure"],
        horizontal=True,
        key="api_required"
    )

    st.markdown("### Equipment / System Connections")

    fire_door_connection = st.selectbox(
        "Fire Door Connection Required",
        ["No", "Yes", "Not Sure"],
        key="fire_door_connection"
    )

    fire_alarm_connection = st.selectbox(
        "Fire Alarm Connection Required",
        ["No", "Yes", "Not Sure"],
        key="fire_alarm_connection"
    )

    conveyor_connection = st.selectbox(
        "Conveyor Connection Required",
        ["No", "Yes", "Not Sure"],
        key="conveyor_connection"
    )

    automatic_door_connection = st.selectbox(
        "Automatic Door Connection Required",
        ["No", "Yes", "Not Sure"],
        key="automatic_door_connection"
    )

    production_unit_connection = st.selectbox(
        "Production Unit Connection Required",
        ["No", "Yes", "Not Sure"],
        key="production_unit_connection"
    )

    connections = st.text_input(
        "Other Connections / Interfaces",
        placeholder="Example: ERP, WMS, lifts, PLC, scanners, dock systems",
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

    connection_summary = (
        f"Fire Door: {fire_door_connection}, "
        f"Fire Alarm: {fire_alarm_connection}, "
        f"Conveyor: {conveyor_connection}, "
        f"Automatic Doors: {automatic_door_connection}, "
        f"Production Units: {production_unit_connection}"
    )

    return {
        "integration_req": integration_req,
        "wms_owner": wms_owner,
        "api_required": api_required,
        "fire_door_connection": fire_door_connection,
        "fire_alarm_connection": fire_alarm_connection,
        "conveyor_connection": conveyor_connection,
        "automatic_door_connection": automatic_door_connection,
        "production_unit_connection": production_unit_connection,
        "connections": connections,
        "connections_details": connections_details,
        "data_flow_text": data_flow_text,
        "connection_summary": connection_summary,
    }