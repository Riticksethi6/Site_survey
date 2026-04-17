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
        if value and value not in cleaned:
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


def _build_execution_nodes(execution_mode, primary_vehicle, primary_action, secondary_vehicle, secondary_action):
    if execution_mode == "Vehicle handover":
        first_node = f"{primary_vehicle} {primary_action}".strip()
        second_node = f"{secondary_vehicle} {secondary_action}".strip()
        return _dedupe_consecutive([first_node, second_node])
    return [primary_vehicle]


def _build_forward_nodes(trigger, info_source, leading_system, ep_wms_used, execution_nodes):
    nodes = []
    trigger_source = TRIGGER_DEFAULT_SOURCE.get(trigger, trigger)
    nodes.append(trigger_source)
    nodes.append(info_source)
    nodes.append(leading_system)

    if ep_wms_used == "Yes" and "EP WMS / DAS" not in nodes:
        nodes.append("EP WMS / DAS")

    nodes.append("EP USP Fleet Manager")
    nodes.extend(execution_nodes)
    return _dedupe_consecutive(nodes)


def _build_return_nodes(final_execution_node, return_targets, ep_wms_used):
    targets = _clean_multiselect(return_targets)
    if not targets:
        return []

    nodes = [final_execution_node, "EP USP Fleet Manager"]

    if ep_wms_used == "Yes" and "EP WMS / DAS" not in targets:
        nodes.append("EP WMS / DAS")

    nodes.extend(targets)
    return _dedupe_consecutive(nodes)


def build_data_flow_inputs(route_details=None, selected_apps=None):
    route_details = route_details or []
    selected_apps = selected_apps or []

    route_details = [
        route for route in route_details
        if route.get("flow_type") != "No - not handled by EP automation"
    ]

    st.subheader("3. Data Flow & Integration")
    st.info(
        "Define the overall integration scope first. Then, for each EP-automation process, choose a simple system flow. "
        "Only optional extra details are shown under advanced options."
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
            "current_system_type": "",
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

    overall_notes = st.text_area(
        "Overall integration / API notes",
        height=90,
        placeholder="Only add anything here if there is an important overall note.",
        key="data_flow_additional_notes",
    )

    st.markdown("### Process-based Data Flow")
    st.caption("Only the routes handled by EP automation are shown here.")

    if not route_details:
        st.info("No EP-automation routes available for Data Flow.")

    equipment_choices = _equipment_options(selected_apps)
    route_flow_summaries = []
    concise_flow_lines = []
    diagram_blocks = []
    all_connected_nodes = set()
    all_statuses = set()
    all_key_data = set()

    for idx, route in enumerate(route_details):
        route_name = f"{route.get('from', 'Start')} → {route.get('to', 'End')}"

        with st.expander(f"Process {idx + 1}: {route_name}", expanded=(idx == 0)):
            col1, col2 = st.columns(2)

            with col1:
                trigger = st.selectbox(
                    f"Task trigger for {route_name}",
                    TRIGGER_OPTIONS,
                    key=f"df_trigger_{idx}",
                )

                default_info_index = INFO_SOURCE_OPTIONS.index("Customer WMS") if (
                    current_system_needed == "Yes" and "Customer WMS" in INFO_SOURCE_OPTIONS
                ) else 0

                info_source = st.selectbox(
                    f"Info source for {route_name}",
                    INFO_SOURCE_OPTIONS,
                    index=default_info_index,
                    key=f"df_info_source_{idx}",
                )

                leading_options = list(COORDINATION_OPTIONS)
                if ep_wms_used == "No":
                    leading_options = [opt for opt in leading_options if opt != "EP WMS / DAS"]

                default_leading_index = leading_options.index("Customer WMS") if (
                    current_system_needed == "Yes" and "Customer WMS" in leading_options
                ) else 0

                leading_system = st.selectbox(
                    f"Leading / coordinating system for {route_name}",
                    leading_options,
                    index=default_leading_index,
                    key=f"df_leading_system_{idx}",
                )

                provided_info = st.text_input(
                    f"What does the source system provide? ({route_name})",
                    placeholder="e.g. material type and storage location",
                    key=f"df_provided_info_{idx}",
                )

            with col2:
                execution_mode = st.radio(
                    f"Execution mode for {route_name}",
                    ["Single EP vehicle", "Vehicle handover"],
                    horizontal=True,
                    key=f"df_execution_mode_{idx}",
                )

                primary_vehicle = st.selectbox(
                    f"Primary EP vehicle for {route_name}",
                    equipment_choices,
                    key=f"df_primary_vehicle_{idx}",
                )

                primary_action_default = "transport"
                if route.get("to") in ["Rack Storage", "Buffer Storage", "Floor Storage"]:
                    primary_action_default = "transport"

                primary_action = st.text_input(
                    f"Primary vehicle action ({route_name})",
                    value=primary_action_default,
                    key=f"df_primary_action_{idx}",
                )

                secondary_vehicle = ""
                secondary_action = ""
                if execution_mode == "Vehicle handover":
                    secondary_vehicle = st.selectbox(
                        f"Final EP vehicle for {route_name}",
                        equipment_choices,
                        index=min(1, len(equipment_choices) - 1) if len(equipment_choices) > 1 else 0,
                        key=f"df_secondary_vehicle_{idx}",
                    )
                    secondary_action_default = "stacking"
                    if route.get("to") == "Outbound":
                        secondary_action_default = "transport"
                    elif route.get("from") in ["Rack Storage", "Buffer Storage", "Floor Storage"] and route.get("to") == "Outbound":
                        secondary_action_default = "transport"

                    secondary_action = st.text_input(
                        f"Final vehicle action ({route_name})",
                        value=secondary_action_default,
                        key=f"df_secondary_action_{idx}",
                    )

            with st.expander("Advanced options", expanded=False):
                col3, col4 = st.columns(2)

                with col3:
                    route_statuses = st.multiselect(
                        f"Status returned for {route_name}",
                        STATUS_OPTIONS,
                        default=["Task completed"],
                        key=f"df_statuses_{idx}",
                    )

                    route_key_data = st.multiselect(
                        f"Data exchanged for {route_name}",
                        KEY_DATA_OPTIONS,
                        default=[
                            "Pallet ID / Barcode",
                            "Pickup location",
                            "Destination / Storage location",
                        ],
                        key=f"df_data_{idx}",
                    )

                with col4:
                    default_return_targets = (
                        ["Customer WMS"] if current_system_needed == "Yes"
                        else (["EP WMS / DAS"] if ep_wms_used == "Yes" else [])
                    )

                    return_targets = st.multiselect(
                        f"Systems receiving status / confirmation for {route_name}",
                        RETURN_TARGET_OPTIONS,
                        default=default_return_targets,
                        key=f"df_return_targets_{idx}",
                    )

                process_notes = st.text_area(
                    f"Additional process note ({route_name})",
                    height=90,
                    placeholder="Only fill this if there is something extra to mention.",
                    key=f"df_process_notes_{idx}",
                )

            execution_nodes = _build_execution_nodes(
                execution_mode=execution_mode,
                primary_vehicle=primary_vehicle,
                primary_action=primary_action,
                secondary_vehicle=secondary_vehicle,
                secondary_action=secondary_action,
            )

            forward_nodes = _build_forward_nodes(
                trigger=trigger,
                info_source=info_source,
                leading_system=leading_system,
                ep_wms_used=ep_wms_used,
                execution_nodes=execution_nodes,
            )

            final_execution_node = execution_nodes[-1] if execution_nodes else primary_vehicle
            return_nodes = _build_return_nodes(
                final_execution_node=final_execution_node,
                return_targets=return_targets,
                ep_wms_used=ep_wms_used,
            )

            st.markdown("**Flow preview**")
            st.markdown(_flow_html(forward_nodes, return_nodes), unsafe_allow_html=True)

            concise_lines = [f"{route_name}:", " → ".join(forward_nodes)]
            if provided_info.strip():
                concise_lines.append(f"{info_source} provides: {provided_info.strip()}")
            if process_notes.strip():
                concise_lines.append(process_notes.strip())

            concise_flow_lines.append("\n".join(concise_lines))

            diagram_line = " → ".join(forward_nodes)
            if return_nodes:
                diagram_line += "\nReturn: " + " → ".join(return_nodes)
            diagram_blocks.append(f"{route_name}:\n{diagram_line}")

            route_flow_summaries.append(
                {
                    "route_name": route_name,
                    "trigger": trigger,
                    "info_source": info_source,
                    "leading_system": leading_system,
                    "execution_mode": execution_mode,
                    "primary_vehicle": primary_vehicle,
                    "primary_action": primary_action,
                    "secondary_vehicle": secondary_vehicle,
                    "secondary_action": secondary_action,
                    "provided_info": provided_info.strip(),
                    "return_targets": return_targets,
                    "statuses": route_statuses,
                    "key_data": route_key_data,
                    "process_notes": process_notes.strip(),
                    "forward_nodes": forward_nodes,
                    "return_nodes": return_nodes,
                }
            )

            all_connected_nodes.update(forward_nodes)
            all_connected_nodes.update(return_nodes)
            all_statuses.update(route_statuses)
            all_key_data.update(route_key_data)

    connections = list(
        dict.fromkeys(
            integration_connections
            + ([current_system_type] if current_system_needed == "Yes" and current_system_type else [])
            + ([other_wms_name] if other_wms_name else [])
        )
    )

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
        system_architecture_lines.append(
            "Customer-side system integration is required. EP WMS / DAS is included as the mandatory coordination layer before EP USP Fleet Manager and EP vehicle execution."
        )
    elif ep_wms_used == "Yes":
        system_architecture_lines.append(
            "EP WMS / DAS is used as the main coordination layer before EP USP Fleet Manager and EP vehicle execution."
        )
    else:
        system_architecture_lines.append(
            "Customer / third-party systems coordinate the process and hand tasks to EP USP Fleet Manager for EP vehicle execution."
        )

    integration_route_parts = []
    if current_system_name:
        integration_route_parts.append(current_system_name)
    elif current_system_needed == "Yes" and current_system_type:
        integration_route_parts.append(current_system_type)
    if ep_wms_used == "Yes":
        integration_route_parts.append("EP WMS / DAS")
    integration_route_parts.append("EP USP Fleet Manager")
    integration_route_parts.append("EP equipment")

    integration_route_text = " → ".join(_dedupe_consecutive(integration_route_parts))
    data_flow_text = "\n\n".join(diagram_blocks)
    task_flow_text = "\n\n".join(concise_flow_lines)
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