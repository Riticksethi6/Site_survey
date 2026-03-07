# data_flow_tab.py – Data Flow & Connections
# Complete version – aligned with your template and form flow

import streamlit as st

def build_data_flow_inputs():
    """
    Collects data flow, system integration requirements, and connections/interfaces.
    All fields are mapped to template placeholders.
    """
    st.subheader("3. Data Flow & Connections")

    # Main integration requirements
    integration_req = st.text_area(
        "System Integration / Data Flow Requirements",
        height=160,
        placeholder="Describe any required integration with WMS, ERP, MES, conveyor controls, "
                    "fire alarm systems, automatic doors, elevators, etc. Include API needs, "
                    "data formats, protocols (e.g. REST, MQTT, OPC UA), real-time vs batch, etc.",
        key="integration_req"
    )

    # Detailed data flow description
    data_flow_text = st.text_area(
        "Data Flow & System Integration (WMS, API, ERP, etc.)",
        height=160,
        placeholder="Detail the expected data flow:\n"
                    "- What triggers AMR movement?\n"
                    "- Where does the AMR get task information?\n"
                    "- What status does the AMR send back?\n"
                    "- Any required handshakes with conveyors, palletizers, etc.?\n"
                    "- Fleet management / traffic control integration?",
        key="data_flow_text"
    )

    # Connections / Interfaces multiselect
    connections = st.multiselect(
        "Connections / Interfaces to Other Equipment",
        options=[
            "Fire Alarm System",
            "Automatic Doors / Gates",
            "Conveyors / Roller Tables",
            "Palletizers / Depalletizers",
            "Elevators / Vertical Conveyors",
            "Production Machines / Lines",
            "WMS / ERP / MES",
            "Traffic Lights / Signals",
            "Barcode / RFID Readers",
            "Other"
        ],
        default=[],
        key="connections"
    )

    # Details field – enabled only if connections are selected
    connections_details = st.text_area(
        "Details on Connections / Interfaces",
        height=120,
        placeholder="Provide details for each selected connection:\n"
                    "- Interface type (digital I/O, Ethernet/IP, Profinet, REST API, etc.)\n"
                    "- Required signals / data exchange\n"
                    "- Handshake protocol\n"
                    "- Safety-related interlocks (e.g. emergency stop propagation)",
        disabled=not connections,
        key="connections_details"
    )

    # Optional: Any additional notes
    additional_notes = st.text_area(
        "Additional Notes / Special Requirements (optional)",
        height=80,
        placeholder="E.g. real-time requirements, latency limits, fallback behavior, "
                    "cybersecurity constraints, preferred communication standards, etc.",
        key="data_flow_additional_notes"
    )

    return {
        "integration_req": integration_req.strip(),
        "data_flow_text": data_flow_text.strip(),
        "connections": connections,
        "connections_details": connections_details.strip(),
        "data_flow_additional_notes": additional_notes.strip()  # optional extra field
    }