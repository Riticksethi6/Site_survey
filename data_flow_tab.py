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

    connections = st.text_input(
        "Connections / Interfaces to Other Equipment",
        placeholder="Example: WMS, ERP, conveyor PLC, dock door system",
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
        placeholder="Describe how orders, tasks, confirmations, and status updates should flow between systems.",
        key="data_flow_text"
    )

    return {
        "integration_req": integration_req,
        "wms_owner": wms_owner,
        "api_required": api_required,
        "connections": connections,
        "connections_details": connections_details,
        "data_flow_text": data_flow_text,
    }