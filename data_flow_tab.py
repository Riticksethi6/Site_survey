import html
import streamlit as st

TRIGGER_OPTIONS = [
    "PDA / barcode scan",
    "Customer WMS order",
    "Customer ERP order",
    "Customer MES production signal",
    "Integrator system",
    "Conveyor sensor",
    "Conveyor PLC",
    "Photoeye / light sensor",
    "Sky camera / overhead camera",
    "Vision system",
    "RFID reader",
    "Machine / production line signal",
    "Dispatch request",
    "Scheduled task",
    "Manual release",
    "HMI / local panel",
    "Other",
]

INFO_SOURCE_OPTIONS = [
    "Customer WMS",
    "Customer ERP",
    "Customer MES",
    "Integrator system",
    "EP WMS / DAS",
    "PDA / Scanner",
    "Conveyor PLC",
    "RFID system",
    "Vision system",
    "Fixed rule / predefined location",
    "Manual operator",
    "Other",
]

COORDINATION_OPTIONS = [
    "Customer WMS",
    "Customer ERP",
    "Customer MES",
    "Integrator system",
    "Middleware / API hub",
    "EP WMS / DAS",
    "Other",
]

RETURN_TARGET_OPTIONS = [
    "Customer WMS",
    "Customer ERP",
    "Customer MES",
    "Integrator system",
    "EP WMS / DAS",
    "PDA / HMI",
    "API callback target",
    "Other",
]

STATUS_OPTIONS = [
    "Task received",
    "Task accepted",
    "Task queued",
    "Task assigned",
    "AGV en route",
    "Pickup confirmed",
    "Destination confirmed",
    "Put-away confirmed",
    "Task completed",
    "Failed / exception",
    "Blocked / waiting",
    "Manual intervention required",
]

KEY_DATA_OPTIONS = [
    "Pallet ID / Barcode",
    "Pickup location",
    "Destination / Storage location",
    "Storage location confirmation",
    "Task ID",
    "SKU / Material code",
    "Quantity",
    "Task completed",
    "Exception code",
]

API_PROTOCOL_OPTIONS = [
    "REST API",
    "Webhook",
    "MQTT",
    "OPC UA",
    "Profinet",
    "Ethernet/IP",
    "SQL / DB",
    "CSV / File exchange",
    "Digital I/O",
    "Custom API",
    "Other",
]

SYSTEM_INTEGRATION_OPTIONS = [
    "Customer WMS",
    "Customer ERP",
    "Customer MES",
    "Integrator system",
    "Other WMS",
    "Fire alarm system",
    "Elevators / vertical conveyors",
    "Conveyors / PLC",
    "Automatic doors / gates",
    "Traffic lights / signals",
    "Barcode / RFID system",
    "AS/RS / warehouse automation",
    "Production machines / lines",
    "Other",
]

APP_TO_EQUIPMENT = {
    "Transport / Cross Docking": "XPL",
    "Stacking/Conveyor": "XQE",
    "Narrow Aisle": "XNA",
}

TRIGGER_DEFAULT_SOURCE = {
    "PDA / barcode scan": "PDA / Scanner",
    "Customer WMS order": "Customer WMS",
    "Customer ERP order": "Customer ERP",
    "Customer MES production signal": "Customer MES",
    "Integrator system": "Integrator system",
    "Conveyor sensor": "Conveyor PLC",
    "Conveyor PLC": "Conveyor PLC",
    "Photoeye / light sensor": "Conveyor PLC",
    "Sky camera / overhead camera": "Vision system",
    "Vision system": "Vision system",
    "RFID reader": "RFID system",
    "Machine / production line signal": "Customer MES",
    "Dispatch request": "Customer WMS",
    "Scheduled task": "EP WMS / DAS",
    "Manual release": "Manual operator",
    "HMI / local panel": "Manual operator",
    "Other": "Other",
}


def _dedupe_keep_order(values):
    cleaned = []
    for value in values:
        if not value:
            continue
        if value not in cleaned:
            cleaned.append(value)
    return cleaned


def _dedupe_consecutive(values):
    cleaned = []
    for value in values:
        if not value:
            continue
        if not cleaned or cleaned[-1] != value:
            cleaned.append(value)
    return cleaned


def _equipment_options(selected_apps):
    equipment = [APP_TO_EQUIPMENT[a] for a in selected_apps or [] if a in APP_TO_EQUIPMENT]
    equipment = _dedupe_keep_order(equipment)
    return equipment or ["AGV"]


def _flow_html(forward_nodes, return_nodes=None):
    forward_nodes = forward_nodes or []
    return_nodes = return_nodes or []

    def _line(nodes, reverse=False):
        parts = []
        for i, node in enumerate(nodes):
            parts.append(f"<div class='df-node'>{html.escape(str(node))}</div>")
            if i < len(nodes) - 1:
                parts.append(f"<div class='df-arrow'>{'←' if reverse else '→'}</div>")
        return "".join(parts)

    return f"""
    <style>
    .df-wrap {{border: 1px solid #d9d9e3; border-radius: 14px; padding: 14px; background: #fafafa; margin: 8px 0 12px 0;}}
    .df-caption {{font-size: 13px; color: #666; margin-bottom: 8px;}}
    .df-line {{display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;}}
    .df-node {{min-width: 120px; text-align: center; padding: 16px 12px; border: 2px solid #444; border-radius: 12px; background: white; font-weight: 600;}}
    .df-arrow {{font-size: 24px; font-weight: 700; color: #444;}}
    </style>
    <div class='df-wrap'>
      <div class='df-caption'>Forward task flow</div>
      <div class='df-line'>{_line(forward_nodes, reverse=False)}</div>
      {("<div class='df-caption'>Status / confirmation return</div><div class='df-line'>" + _line(return_nodes, reverse=True) + "</div>") if return_nodes else ""}
    </div>
    """


def _clean_multiselect(values):
    return [v for v in (values or []) if v]


def _build_forward_nodes(trigger, info_source, leading_system, ep_wms_used, execution):
    nodes = []
    trigger_source = TRIGGER_DEFAULT_SOURCE.get(trigger, trigger)
    nodes.append(trigger_source)
    nodes.append(info_source)
    nodes.append(leading_system)
    if ep_wms_used == "Yes" and "EP WMS / DAS" not in nodes:
        nodes.append("EP WMS / DAS")
    nodes.append("EP USP Fleet Manager")
    nodes.append(execution)
    return _dedupe_consecutive(nodes)


def _build_return_nodes(execution, return_targets, ep_wms_used):
    targets = _clean_multiselect(return_targets)
    if not targets:
        return []
    nodes = [execution, "EP USP Fleet Manager"]
    if ep_wms_used == "Yes" and "EP WMS / DAS" not in targets:
        nodes.append("EP WMS / DAS")
    nodes.extend(targets)
    return _dedupe_consecutive(nodes)


def build_data_flow_inputs(route_details=None, selected_apps=None):
    route_details = route_details or []
    selected_apps = selected_apps or []

    st.subheader("3. Data Flow & Integration")
    st.info(
        "Define the overall integration scope first. Then, for each material-flow process, choose the system blocks in sequence and describe what information is needed in which system."
    )

    integration_required = st.radio(
        "Integration to any system required?",
        ["Yes", "No"],
        horizontal=True,
        key="integration_required",
    )

    if integration_required == "No":
        st.info("No external system integration selected. EP equipment will run without customer-system integration.")
        return {
            "integration_required": "No",
            "ep_wms_used": "No",
            "current_system_needed": "No",
            "current_system_name": "",
            "other_wms_integration_needed": "No",
            "other_wms_name": "",
            "integration_connections": [],
            "api_protocols": [],
            "integration_req": "Integration required: No",
            "data_flow_text": "No external integration required.",
            "connections": [],
            "connections_details": "",
            "data_flow_additional_notes": "",
            "system_architecture_text": "No external integration required. EP equipment will run without customer-system integration.",
            "integration_route_text": "EP equipment only",
            "data_flow_diagram_text": "EP equipment only",
            "task_flow_text": "No external task-flow integration required.",
            "connected_systems_text": "EP equipment",
            "status_feedback_text": "",
            "key_data_exchange_text": "",
            "route_flow_summaries": [],
        }

    st.markdown("### Overall integration scope")
    col_left, col_right = st.columns(2)

    with col_left:
        ep_wms_used = st.radio(
            "Do you want DAS / EP WMS?",
            ["Yes", "No"],
            horizontal=True,
            key="ep_wms_used",
        )

        current_system_needed = st.radio(
            "Integration to your current customer system needed?",
            ["Yes", "No"],
            horizontal=True,
            key="current_system_needed",
        )
        current_system_name = ""
        current_system_type = ""
        if current_system_needed == "Yes":
            current_system_type = st.selectbox(
                "Current customer system type",
                ["Customer WMS", "Customer ERP", "Customer MES", "Integrator system", "Other"],
                key="current_system_type",
            )
            current_system_name = st.text_input(
                "Name of the current customer system",
                placeholder="e.g. SAP EWM, Manhattan WMS, custom WMS, MES name",
                key="current_system_name",
            )

        other_wms_integration_needed = st.radio(
            "Integration to any other WMS or business system?",
            ["Yes", "No"],
            horizontal=True,
            key="other_wms_integration_needed",
        )
        other_wms_name = ""
        if other_wms_integration_needed == "Yes":
            other_wms_name = st.text_input(
                "Name of the other WMS / system",
                placeholder="e.g. another WMS, middleware, customer integration hub",
                key="other_wms_name",
            )

    with col_right:
        integration_connections = st.multiselect(
            "Integration to other systems / equipment",
            SYSTEM_INTEGRATION_OPTIONS,
            default=[],
            key="integration_connections",
        )

        api_protocols = st.multiselect(
            "All integrations to other systems will be done by APIs / interfaces",
            API_PROTOCOL_OPTIONS,
            default=["REST API"],
            key="api_protocols",
        )

        global_status_feedback = st.multiselect(
            "Default status feedback EP should return",
            STATUS_OPTIONS,
            default=["Task completed"],
            key="global_status_feedback",
        )

        global_key_data = st.multiselect(
            "Default key data exchanged",
            KEY_DATA_OPTIONS,
            default=["Pallet ID / Barcode", "Pickup location", "Destination / Storage location", "Task completed"],
            key="global_key_data",
        )

    overall_notes = st.text_area(
        "Overall integration / API notes",
        height=120,
        placeholder="Describe API ownership, handshake expectations, middleware, error handling, timing, or any general integration requirement.",
        key="data_flow_additional_notes",
    )

    st.markdown("### Process-based Data Flow")
    st.caption("Based on the material-flow routes you defined, configure the system flow for each process below.")

    if not route_details:
        st.warning("No material-flow routes found yet. Please define routes in the Material Flow tab first.")

    equipment_choices = _equipment_options(selected_apps)
    route_flow_summaries = []
    task_flow_blocks = []
    diagram_blocks = []
    all_connected_nodes = set()
    all_statuses = set(global_status_feedback)
    all_key_data = set(global_key_data)

    for idx, route in enumerate(route_details or []):
        route_name = f"{route.get('from', 'Start')} → {route.get('to', 'End')}"
        with st.expander(f"Process {idx + 1}: {route_name}", expanded=(idx == 0)):
            col1, col2 = st.columns(2)

            with col1:
                trigger = st.selectbox(
                    f"Select the task trigger for {route_name}",
                    TRIGGER_OPTIONS,
                    key=f"df_trigger_{idx}",
                )

                info_source = st.selectbox(
                    f"Which system provides pallet / pickup / destination information for {route_name}?",
                    INFO_SOURCE_OPTIONS,
                    index=INFO_SOURCE_OPTIONS.index("Customer WMS") if current_system_needed == "Yes" and "Customer WMS" in INFO_SOURCE_OPTIONS else 0,
                    key=f"df_info_source_{idx}",
                )

                leading_options = list(COORDINATION_OPTIONS)
                if ep_wms_used == "No":
                    leading_options = [opt for opt in leading_options if opt != "EP WMS / DAS"]
                leading_system = st.selectbox(
                    f"Select the system leading / coordinating {route_name}",
                    leading_options,
                    index=leading_options.index("Customer WMS") if current_system_needed == "Yes" and "Customer WMS" in leading_options else 0,
                    key=f"df_leading_system_{idx}",
                )

            with col2:
                execution_default = equipment_choices[0] if len(equipment_choices) == 1 else equipment_choices[min(idx, len(equipment_choices) - 1)]
                execution = st.selectbox(
                    f"Which EP equipment executes {route_name}?",
                    equipment_choices,
                    index=equipment_choices.index(execution_default),
                    key=f"df_execution_{idx}",
                )

                route_statuses = st.multiselect(
                    f"Status returned for {route_name}",
                    STATUS_OPTIONS,
                    default=global_status_feedback or ["Task completed"],
                    key=f"df_statuses_{idx}",
                )

                return_targets = st.multiselect(
                    f"Which systems receive the status / confirmation for {route_name}?",
                    RETURN_TARGET_OPTIONS,
                    default=["Customer WMS"] if current_system_needed == "Yes" else (["EP WMS / DAS"] if ep_wms_used == "Yes" else []),
                    key=f"df_return_targets_{idx}",
                )

                route_key_data = st.multiselect(
                    f"Data exchanged for {route_name}",
                    KEY_DATA_OPTIONS,
                    default=global_key_data or ["Pallet ID / Barcode", "Pickup location", "Destination / Storage location", "Task completed"],
                    key=f"df_data_{idx}",
                )

            process_notes = st.text_area(
                f"Please determine the data flow for this process. What information is needed in which system, or what information must be provided from which system? ({route_name})",
                height=120,
                placeholder="Example: PDA provides pallet barcode. Customer WMS provides pickup and drop-off location to EP WMS / DAS. EP WMS / DAS sends the task to EP USP Fleet Manager, which dispatches the AGV. Task status is returned to customer WMS.",
                key=f"df_process_notes_{idx}",
            )

            forward_nodes = _build_forward_nodes(trigger, info_source, leading_system, ep_wms_used, execution)
            return_nodes = _build_return_nodes(execution, return_targets, ep_wms_used)

            st.markdown("**Flow preview**")
            st.markdown(_flow_html(forward_nodes, return_nodes), unsafe_allow_html=True)

            diagram_line = " → ".join(forward_nodes)
            if return_nodes:
                diagram_line += "\nReturn: " + " → ".join(return_nodes)

            route_flow_summaries.append({
                "route_name": route_name,
                "trigger": trigger,
                "info_source": info_source,
                "leading_system": leading_system,
                "execution": execution,
                "return_targets": return_targets,
                "statuses": route_statuses,
                "key_data": route_key_data,
                "process_notes": process_notes.strip(),
                "forward_nodes": forward_nodes,
                "return_nodes": return_nodes,
            })

            task_block = [
                f"{route_name}:",
                f"Trigger: {trigger}",
                f"Information source: {info_source}",
                f"Leading / coordinating system: {leading_system}",
                "Fixed fleet layer: EP USP Fleet Manager",
                f"Execution: {execution}",
                f"Forward path: {' → '.join(forward_nodes)}",
            ]
            if return_nodes:
                task_block.append(f"Return path: {' → '.join(return_nodes)}")
            if route_statuses:
                task_block.append(f"Status returned: {', '.join(route_statuses)}")
            if route_key_data:
                task_block.append(f"Data exchanged: {', '.join(route_key_data)}")
            if process_notes.strip():
                task_block.append(f"Process notes: {process_notes.strip()}")

            task_flow_blocks.append("\n".join(task_block))
            diagram_blocks.append(f"{route_name}:\n{diagram_line}")
            all_connected_nodes.update(forward_nodes)
            all_connected_nodes.update(return_nodes)
            all_statuses.update(route_statuses)
            all_key_data.update(route_key_data)

    connections = list(dict.fromkeys(integration_connections + ([current_system_type] if current_system_needed == "Yes" and current_system_type else []) + ([other_wms_name] if other_wms_name else [])))

    integration_req_lines = [
        f"Integration required: {integration_required}",
        f"DAS / EP WMS required: {ep_wms_used}",
        f"Integration to current customer system needed: {current_system_needed}",
    ]
    if current_system_name:
        integration_req_lines.append(f"Current customer system: {current_system_name} ({current_system_type})")
    if other_wms_integration_needed == "Yes":
        integration_req_lines.append(f"Other WMS / system integration: {other_wms_name or 'Yes'}")
    if integration_connections:
        integration_req_lines.append("Other integrations: " + ", ".join(integration_connections))

    connections_details_lines = []
    if api_protocols:
        connections_details_lines.append("All integrations are API / interface based via: " + ", ".join(api_protocols))
    if current_system_name:
        connections_details_lines.append(f"Current customer system name: {current_system_name}")
    if other_wms_name:
        connections_details_lines.append(f"Other WMS / system name: {other_wms_name}")
    if overall_notes.strip():
        connections_details_lines.append(f"Overall integration notes: {overall_notes.strip()}")

    system_architecture_lines = []
    if current_system_needed == "Yes" and ep_wms_used == "Yes":
        system_architecture_lines.append("Customer-side system integration is required. EP WMS / DAS is included as the mandatory coordination layer before EP USP Fleet Manager and AGV execution.")
    elif ep_wms_used == "Yes":
        system_architecture_lines.append("EP WMS / DAS is used as the main coordination layer before EP USP Fleet Manager and AGV execution.")
    else:
        system_architecture_lines.append("Customer / third-party systems coordinate the process and hand tasks to EP USP Fleet Manager for AGV execution.")
    if current_system_name:
        system_architecture_lines.append(f"Named customer system: {current_system_name}.")
    if other_wms_name:
        system_architecture_lines.append(f"Additional integrated system: {other_wms_name}.")

    integration_route_parts = []
    if current_system_name:
        integration_route_parts.append(current_system_name)
    elif current_system_needed == "Yes" and current_system_type:
        integration_route_parts.append(current_system_type)
    if other_wms_name:
        integration_route_parts.append(other_wms_name)
    if ep_wms_used == "Yes":
        integration_route_parts.append("EP WMS / DAS")
    integration_route_parts.append("EP USP Fleet Manager")
    integration_route_parts.append("EP equipment")
    integration_route_text = " → ".join(_dedupe_consecutive(integration_route_parts))

    data_flow_text = "\n\n".join(diagram_blocks)
    task_flow_text = "\n\n".join(task_flow_blocks)

    connected_systems_text = "\n".join(sorted(node for node in all_connected_nodes if node))
    status_feedback_text = "\n".join(sorted(status for status in all_statuses if status))
    key_data_exchange_text = "\n".join(sorted(item for item in all_key_data if item))

    return {
        "integration_required": integration_required,
        "ep_wms_used": ep_wms_used,
        "current_system_needed": current_system_needed,
        "current_system_name": current_system_name,
        "current_system_type": current_system_type,
        "other_wms_integration_needed": other_wms_integration_needed,
        "other_wms_name": other_wms_name,
        "integration_connections": integration_connections,
        "api_protocols": api_protocols,
        "integration_req": "\n".join(integration_req_lines),
        "data_flow_text": data_flow_text,
        "connections": connections,
        "connections_details": "\n".join(connections_details_lines),
        "data_flow_additional_notes": overall_notes.strip(),
        "system_architecture_text": "\n".join(system_architecture_lines),
        "integration_route_text": integration_route_text,
        "data_flow_diagram_text": data_flow_text,
        "task_flow_text": task_flow_text,
        "connected_systems_text": connected_systems_text,
        "status_feedback_text": status_feedback_text,
        "key_data_exchange_text": key_data_exchange_text,
        "route_flow_summaries": route_flow_summaries,
    }
