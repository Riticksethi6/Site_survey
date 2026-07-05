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
    "WMS / DAS (scheduled / rule-based)",
    "Barcode / RFID scan",
    "Manual / HMI",
    "Scheduled task",
    "Other",
]


def _flow_html(nodes):
    parts = []
    for i, node in enumerate(nodes):
        is_fleet = "Fleet Manager" in str(node)
        is_das = "DAS" in str(node) or "WMS" in str(node)
        is_agv = "AGV" in str(node)
        if is_fleet:
            border, bg, color = "#10b981", "#ecfdf5", "#065f46"
        elif is_das:
            border, bg, color = "#0891b2", "#ecfeff", "#164e63"
        elif is_agv:
            border, bg, color = "#7c3aed", "#f5f3ff", "#4c1d95"
        else:
            border, bg, color = "#6b7280", "#f9fafb", "#1f2937"
        parts.append(
            f"<div style='min-width:120px;text-align:center;padding:14px 10px;"
            f"border:2px solid {border};border-radius:10px;background:{bg};"
            f"font-weight:600;font-size:13px;color:{color};'>{html.escape(str(node))}</div>"
        )
        if i < len(nodes) - 1:
            parts.append("<div style='font-size:22px;font-weight:700;color:#10b981;'>→</div>")

    return (
        "<div style='border:1px solid #d1fae5;border-radius:14px;padding:18px;"
        "background:#f8fafc;margin:10px 0;'>"
        "<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;'>"
        + "".join(parts)
        + "</div></div>"
    )


def _sort_systems(systems, order_values):
    if not systems:
        return []
    paired = sorted(zip(order_values, systems), key=lambda x: x[0])
    return [s for _, s in paired]


def _build_nodes(ordered_systems, das_enabled):
    nodes = list(ordered_systems)
    if das_enabled:
        nodes.append("WMS / DAS Layer")
    nodes.append("Fleet Manager")
    nodes.append("AGV Fleet")
    return nodes


def _sequence_widget(systems, key_prefix):
    """Show position number inputs for each system. Returns ordered list."""
    if len(systems) <= 1:
        return list(systems)

    st.caption("Set the position / sequence — Fleet Manager and AGV Fleet are always fixed at the end.")
    cols = st.columns(len(systems))
    order_values = []
    for i, sys_name in enumerate(systems):
        with cols[i]:
            val = st.number_input(
                sys_name,
                min_value=1,
                max_value=len(systems),
                value=i + 1,
                step=1,
                key=f"{key_prefix}_order_{i}",
                label_visibility="visible",
            )
            order_values.append(val)

    return _sort_systems(systems, order_values)


def build_data_flow_inputs(route_details=None, selected_apps=None):
    route_details = route_details or []
    ep_routes = [r for r in route_details if r.get("flow_type") != "No - not handled by EP automation"]

    st.subheader("3. Data Flow & Integration")

    integration_required = st.radio(
        "Is integration to any external system required?",
        ["Yes", "No"],
        horizontal=True,
        key="integration_required",
    )

    # ── No integration: WMS/DAS layer is always present ──────────────────────
    if integration_required == "No":
        st.markdown("**Data flow:**")
        st.markdown(
            _flow_html(["WMS / DAS Layer", "Fleet Manager", "AGV Fleet"]),
            unsafe_allow_html=True,
        )
        st.info("No external system integration. WMS / DAS Layer coordinates tasks via Fleet Manager to the AGV fleet.")
        return {
            "integration_required": "No",
            "ep_wms_used": "Yes",
            "connected_external_systems": [],
            "task_trigger": "",
            "data_flow_additional_notes": "",
            "system_architecture_text": "No external integration required. WMS / DAS Layer coordinates tasks via Fleet Manager to the AGV fleet.",
            "integration_route_text": "WMS / DAS Layer → Fleet Manager → AGV Fleet",
            "task_flow_text": "WMS / DAS Layer → Fleet Manager → AGV Fleet",
            "connected_systems_text": "WMS / DAS Layer, Fleet Manager, AGV Fleet",
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
            "integration_req": "Integration required: No\nWMS/DAS layer: Yes",
            "data_flow_text": "WMS / DAS Layer → Fleet Manager → AGV Fleet",
            "connections": [],
            "data_flow_diagram_text": "WMS / DAS Layer → Fleet Manager → AGV Fleet",
            "route_flow_summaries": [],
        }

    # ── Global system pool ───────────────────────────────────────────────────
    st.markdown("### Which external systems are involved?")

    selected_systems = st.multiselect(
        "Select all systems that connect to the AGV system",
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

    display_systems = []
    for s in selected_systems:
        if s == "Other":
            display_systems.append(other_system_name.strip() or "Other system")
        else:
            display_systems.append(s)

    route_flow_summaries = []
    all_flow_texts = []

    # ── Per-route data flow (one block per material flow step) ───────────────
    if ep_routes:
        st.markdown("### Data flow per process step")

        for idx, route in enumerate(ep_routes):
            route_name = f"{route.get('from', 'Start')} → {route.get('to', 'End')}"

            with st.expander(f"Process {idx + 1}: {route_name}", expanded=True):

                # Which systems apply to this route?
                route_systems = st.multiselect(
                    "Systems connected for this step",
                    display_systems,
                    default=display_systems,
                    key=f"route_systems_{idx}",
                    placeholder="Select systems for this step…",
                )

                # Sequence them
                ordered = _sequence_widget(route_systems, key_prefix=f"route_{idx}")

                col1, col2 = st.columns(2)
                with col1:
                    das = st.radio(
                        "WMS / DAS layer for this step?",
                        ["Yes", "No"],
                        horizontal=True,
                        key=f"das_route_{idx}",
                    )
                with col2:
                    trigger = st.selectbox(
                        "What triggers the task for this step?",
                        TRIGGER_OPTIONS,
                        key=f"trigger_route_{idx}",
                    )

                flow_nodes = _build_nodes(ordered, das == "Yes")
                st.markdown(_flow_html(flow_nodes), unsafe_allow_html=True)

                route_flow_summaries.append({
                    "route_name": route_name,
                    "systems": ordered,
                    "das": das,
                    "trigger": trigger,
                    "flow_nodes": flow_nodes,
                })
                all_flow_texts.append(f"{route_name}:\n  " + " → ".join(flow_nodes))

        ep_wms_used = "Yes" if any(r["das"] == "Yes" for r in route_flow_summaries) else "No"
        integration_route_text = "\n".join(all_flow_texts)

        # Architecture summary from first route as representative
        first = route_flow_summaries[0] if route_flow_summaries else {}
        rep_systems = first.get("systems", display_systems)
        rep_das = first.get("das", "No")

    else:
        # ── No material flow routes yet: global flow builder ─────────────────
        st.markdown("### Data flow")

        ordered = _sequence_widget(display_systems, key_prefix="global")

        col1, col2 = st.columns(2)
        with col1:
            ep_wms_used = st.radio(
                "Does WMS / DAS sit between external system(s) and the Fleet Manager?",
                ["Yes", "No"],
                horizontal=True,
                key="ep_wms_used",
            )
        with col2:
            trigger = st.selectbox(
                "What triggers the AGV task?",
                TRIGGER_OPTIONS,
                key="task_trigger",
            )

        flow_nodes = _build_nodes(ordered, ep_wms_used == "Yes")
        st.markdown(_flow_html(flow_nodes), unsafe_allow_html=True)

        route_flow_summaries = []
        integration_route_text = " → ".join(flow_nodes)
        rep_systems = ordered
        rep_das = ep_wms_used

    # ── Additional notes ─────────────────────────────────────────────────────
    additional_notes = st.text_area(
        "Additional integration notes (optional)",
        height=90,
        placeholder="e.g. specific API protocol, special requirement, or exception.",
        key="data_flow_additional_notes",
    )

    # ── Build Word report texts ───────────────────────────────────────────────
    if rep_systems and rep_das == "Yes":
        arch_text = (
            f"External system(s) ({', '.join(rep_systems)}) connect to the WMS / DAS Layer, "
            "which coordinates tasks via Fleet Manager to the AGV fleet."
        )
    elif rep_systems:
        arch_text = (
            f"External system(s) ({', '.join(rep_systems)}) connect directly to "
            "Fleet Manager for AGV task dispatch."
        )
    elif ep_wms_used == "Yes":
        arch_text = "WMS / DAS Layer coordinates tasks via Fleet Manager to the AGV fleet."
    else:
        arch_text = "Fleet Manager dispatches tasks directly to the AGV fleet."

    task_flow_lines = [f"Data flow:\n{integration_route_text}"]
    if additional_notes.strip():
        task_flow_lines.append(f"Notes: {additional_notes.strip()}")

    all_nodes = set()
    for r in route_flow_summaries:
        all_nodes.update(r.get("flow_nodes", []))
    if not all_nodes:
        all_nodes = {"WMS / DAS Layer", "Fleet Manager", "AGV Fleet"} if ep_wms_used == "Yes" else {"Fleet Manager", "AGV Fleet"}

    return {
        "integration_required": integration_required,
        "ep_wms_used": ep_wms_used,
        "connected_external_systems": selected_systems,
        "task_trigger": route_flow_summaries[0].get("trigger", "") if route_flow_summaries else "",
        "data_flow_additional_notes": additional_notes.strip(),
        "system_architecture_text": arch_text,
        "integration_route_text": integration_route_text,
        "task_flow_text": "\n".join(task_flow_lines),
        "connected_systems_text": ", ".join(sorted(all_nodes)),
        "status_feedback_text": "",
        "key_data_exchange_text": "",
        "connections_details": additional_notes.strip(),
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
            f"WMS/DAS layer: {ep_wms_used}"
        ),
        "data_flow_text": integration_route_text,
        "connections": display_systems,
        "data_flow_diagram_text": integration_route_text,
        "route_flow_summaries": route_flow_summaries,
    }
