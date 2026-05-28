import html
import streamlit as st

EXTERNAL_SYSTEM_OPTIONS = [
    "Customer WMS",
    "Customer ERP",
    "Customer MES",
    "Conveyor / PLC",
    "AS/RS system",
    "Fire alarm / safety system",
    "Automatic doors / gates",
    "RFID / barcode system",
    "Other",
]

TRIGGER_OPTIONS = [
    "Customer WMS order",
    "Customer ERP order",
    "Customer MES signal",
    "Conveyor / PLC signal",
    "EP DAS (scheduled / rule-based)",
    "Barcode / RFID scan",
    "Manual / HMI",
    "Scheduled task",
    "Other",
]


def _flow_html(nodes):
    def _node(text, highlight=False):
        border = "#1a73e8" if highlight else "#444"
        bg = "#e8f0fe" if highlight else "white"
        return (
            f"<div style='min-width:120px;text-align:center;padding:14px 10px;"
            f"border:2px solid {border};border-radius:10px;background:{bg};"
            f"font-weight:600;font-size:13px;'>{html.escape(str(text))}</div>"
        )

    def _arrow():
        return "<div style='font-size:24px;font-weight:700;color:#444;'>→</div>"

    parts = []
    for i, node in enumerate(nodes):
        # highlight EP USP Fleet Manager
        is_usp = "USP" in str(node)
        parts.append(_node(node, highlight=is_usp))
        if i < len(nodes) - 1:
            parts.append(_arrow())

    return (
        "<div style='border:1px solid #d9d9e3;border-radius:14px;padding:18px;"
        "background:#fafafa;margin:12px 0;'>"
        "<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;'>"
        + "".join(parts)
        + "</div></div>"
    )


def build_data_flow_inputs(route_details=None, selected_apps=None):
    st.subheader("3. Data Flow & Integration")

    integration_required = st.radio(
        "Is integration to any external system required?",
        ["Yes", "No"],
        horizontal=True,
        key="integration_required",
    )

    if integration_required == "No":
        st.markdown("**Data flow:**")
        st.markdown(
            _flow_html(["EP DAS / WMS", "EP USP Fleet Manager", "AGV Fleet"]),
            unsafe_allow_html=True,
        )
        st.info("No external system integration. EP DAS coordinates tasks via EP USP Fleet Manager to the AGV fleet.")
        return {
            "integration_required": "No",
            "ep_wms_used": "Yes",
            "connected_external_systems": [],
            "task_trigger": "",
            "data_flow_additional_notes": "",
            "system_architecture_text": "No external integration required. EP DAS coordinates tasks via EP USP Fleet Manager to the AGV fleet.",
            "integration_route_text": "EP DAS / WMS → EP USP Fleet Manager → AGV Fleet",
            "task_flow_text": "EP DAS / WMS → EP USP Fleet Manager → AGV Fleet",
            "connected_systems_text": "EP DAS / WMS, EP USP Fleet Manager, AGV Fleet",
            "status_feedback_text": "",
            "key_data_exchange_text": "",
            "connections_details": "",
            "current_system_needed": "No",
            "current_system_name": "",
            "current_system_type": "",
            "other_wms_integration_needed": "No",
            "other_wms_name": "",
            "integration_connections": [],
            "api_protocols": [],
            "integration_req": "Integration required: No\nEP DAS layer: Yes",
            "data_flow_text": "EP DAS / WMS → EP USP Fleet Manager → AGV Fleet",
            "connections": [],
            "data_flow_diagram_text": "EP DAS / WMS → EP USP Fleet Manager → AGV Fleet",
            "route_flow_summaries": [],
        }

    # ── Step 1: Which external systems connect? ──────────────────────────────
    st.markdown("### Step 1 — Which systems connect to EP equipment?")

    selected_systems = st.multiselect(
        "Select all external systems that will be connected",
        EXTERNAL_SYSTEM_OPTIONS,
        key="connected_external_systems",
        placeholder="Pick one or more systems…",
    )

    other_system_name = ""
    if "Other" in selected_systems:
        other_system_name = st.text_input(
            "Describe the other system",
            placeholder="e.g. custom middleware, proprietary integration hub",
            key="other_system_name",
        )

    # Resolve display names (replace "Other" with custom label)
    display_systems = []
    for s in selected_systems:
        if s == "Other":
            display_systems.append(other_system_name.strip() if other_system_name.strip() else "Other system")
        else:
            display_systems.append(s)

    # ── Step 2: Does EP DAS sit in between? ─────────────────────────────────
    st.markdown("### Step 2 — EP DAS / WMS layer")

    ep_wms_used = st.radio(
        "Does EP DAS / WMS sit between the external system(s) and EP USP Fleet Manager?",
        ["Yes", "No"],
        horizontal=True,
        key="ep_wms_used",
        help=(
            "Yes → External system → EP DAS → USP Fleet Manager → AGV\n"
            "No  → External system → USP Fleet Manager directly → AGV"
        ),
    )

    # ── Step 3: Who triggers the task? ──────────────────────────────────────
    st.markdown("### Step 3 — Task trigger")

    # If EP DAS is used and no external system, EP DAS trigger makes most sense
    trigger_default_index = 0
    if ep_wms_used == "Yes" and not display_systems:
        trigger_default_index = TRIGGER_OPTIONS.index("EP DAS (scheduled / rule-based)")

    trigger = st.selectbox(
        "Who / what triggers the AGV task?",
        TRIGGER_OPTIONS,
        index=trigger_default_index,
        key="task_trigger",
    )

    # ── Build flow nodes ─────────────────────────────────────────────────────
    flow_nodes = []

    if display_systems:
        if len(display_systems) == 1:
            flow_nodes.append(display_systems[0])
        else:
            flow_nodes.append(" / ".join(display_systems))

    if ep_wms_used == "Yes":
        flow_nodes.append("EP DAS / WMS")

    flow_nodes.append("EP USP Fleet Manager")
    flow_nodes.append("AGV Fleet")

    # ── Live flow preview ────────────────────────────────────────────────────
    st.markdown("### Data flow")
    st.markdown(_flow_html(flow_nodes), unsafe_allow_html=True)

    # ── Optional notes ───────────────────────────────────────────────────────
    additional_notes = st.text_area(
        "Additional integration notes (optional)",
        height=90,
        placeholder="e.g. specific API protocol, special requirement, or exception.",
        key="data_flow_additional_notes",
    )

    # ── Build text outputs for Word report ───────────────────────────────────
    integration_route_text = " → ".join(flow_nodes)

    if display_systems and ep_wms_used == "Yes":
        arch_text = (
            f"External system(s) ({', '.join(display_systems)}) connect to EP DAS / WMS, "
            "which coordinates tasks via EP USP Fleet Manager to the AGV fleet."
        )
    elif display_systems:
        arch_text = (
            f"External system(s) ({', '.join(display_systems)}) connect directly to "
            "EP USP Fleet Manager for AGV task dispatch."
        )
    elif ep_wms_used == "Yes":
        arch_text = (
            "EP DAS / WMS coordinates tasks via EP USP Fleet Manager to the AGV fleet."
        )
    else:
        arch_text = "EP USP Fleet Manager dispatches tasks directly to the AGV fleet."

    task_flow_lines = [f"Task trigger: {trigger}", f"Data flow: {integration_route_text}"]
    if additional_notes.strip():
        task_flow_lines.append(f"Notes: {additional_notes.strip()}")

    connections_details_lines = []
    if additional_notes.strip():
        connections_details_lines.append(additional_notes.strip())

    return {
        "integration_required": integration_required,
        "ep_wms_used": ep_wms_used,
        "connected_external_systems": selected_systems,
        "task_trigger": trigger,
        "data_flow_additional_notes": additional_notes.strip(),
        "system_architecture_text": arch_text,
        "integration_route_text": integration_route_text,
        "task_flow_text": "\n".join(task_flow_lines),
        "connected_systems_text": ", ".join(flow_nodes),
        "status_feedback_text": "",
        "key_data_exchange_text": "",
        "connections_details": "\n".join(connections_details_lines),
        "current_system_needed": "Yes" if display_systems else "No",
        "current_system_name": display_systems[0] if display_systems else "",
        "current_system_type": selected_systems[0] if selected_systems else "",
        "other_wms_integration_needed": "No",
        "other_wms_name": other_system_name.strip(),
        "integration_connections": selected_systems,
        "api_protocols": [],
        "integration_req": (
            f"Integration required: Yes\n"
            f"Connected systems: {', '.join(display_systems) if display_systems else 'None'}\n"
            f"EP DAS layer: {ep_wms_used}\n"
            f"Task trigger: {trigger}"
        ),
        "data_flow_text": integration_route_text,
        "connections": display_systems,
        "data_flow_diagram_text": integration_route_text,
        "route_flow_summaries": [],
    }
