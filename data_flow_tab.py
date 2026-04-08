import html
import streamlit as st

TRIGGER_OPTIONS = [
    "PDA / barcode scan",
    "Customer WMS order",
    "ERP / MES production signal",
    "PLC / conveyor signal",
    "Manual release",
    "Dispatch request",
    "Other",
]

STATUS_OPTIONS = [
    "Task received",
    "Task assigned",
    "Task started",
    "Destination / storage location confirmed",
    "Task completed",
    "Exception / blocked",
]

KEY_DATA_OPTIONS = [
    "Pallet ID / Barcode",
    "Pickup location",
    "Destination / Storage location",
    "Task ID",
    "Task completed",
    "Exception code",
    "SKU / Material code",
    "Quantity",
]

PROTOCOL_OPTIONS = [
    "REST API",
    "SQL / DB",
    "CSV / File exchange",
    "OPC UA",
    "MQTT",
    "Profinet",
    "Ethernet/IP",
    "Digital I/O",
    "Other",
]

EXTERNAL_SYSTEMS = [
    "PDA / Scanner",
    "Customer WMS",
    "Customer ERP",
    "Customer MES",
    "PLC / Conveyor",
    "Barcode / RFID Reader",
    "Automatic Doors / Gates",
    "Elevators / Vertical Conveyors",
    "Traffic lights / signals",
    "Other",
]

APP_TO_EQUIPMENT = {
    "Transport / Cross Docking": "XPL",
    "Stacking/Conveyor": "XQE",
    "Narrow Aisle": "XNA",
}

TRIGGER_TO_SYSTEM = {
    "PDA / barcode scan": "PDA / Scanner",
    "Customer WMS order": "Customer WMS",
    "ERP / MES production signal": "Customer ERP / MES",
    "PLC / conveyor signal": "PLC / Conveyor",
    "Manual release": "Manual / Operator",
    "Dispatch request": "Customer WMS",
    "Other": "External trigger",
}


def _dedupe_consecutive(values):
    cleaned = []
    for value in values:
        if not value:
            continue
        if not cleaned or cleaned[-1] != value:
            cleaned.append(value)
    return cleaned


def _system_label(value):
    if value == "Customer ERP / MES":
        return "Customer ERP / MES"
    return value


def _equipment_options(selected_apps):
    equipment = [APP_TO_EQUIPMENT[a] for a in selected_apps or [] if a in APP_TO_EQUIPMENT]
    equipment = list(dict.fromkeys(equipment))
    return equipment or ["AGV"]


def _route_sender_options(ep_wms_used, customer_system_involved):
    options = []
    if customer_system_involved == "Yes":
        options.extend(["Customer WMS", "Customer ERP / MES"])
    options.extend(["PDA / Scanner", "PLC / Conveyor", "Manual / Operator"])
    if ep_wms_used == "Yes":
        options.append("EP WMS / DAS")
    options.append("Other")
    return list(dict.fromkeys(options))


def _route_destination_options(ep_wms_used, customer_system_involved):
    options = []
    if customer_system_involved == "Yes":
        options.extend(["Customer WMS", "Customer ERP / MES", "Fixed rule / predefined location"])
    if ep_wms_used == "Yes":
        options.append("EP WMS / DAS")
    options.extend(["Operator", "Other"])
    return list(dict.fromkeys(options))


def _default_sender(trigger, ep_wms_used, customer_system_involved):
    if trigger == "PDA / barcode scan":
        return "Customer WMS" if customer_system_involved == "Yes" else ("EP WMS / DAS" if ep_wms_used == "Yes" else "PDA / Scanner")
    if trigger == "Customer WMS order":
        return "Customer WMS"
    if trigger == "ERP / MES production signal":
        return "Customer ERP / MES"
    if trigger == "PLC / conveyor signal":
        return "PLC / Conveyor"
    if trigger == "Manual release":
        return "Manual / Operator"
    if trigger == "Dispatch request":
        return "Customer WMS" if customer_system_involved == "Yes" else ("EP WMS / DAS" if ep_wms_used == "Yes" else "Manual / Operator")
    return "EP WMS / DAS" if ep_wms_used == "Yes" else "Other"


def _default_destination(ep_wms_used, customer_system_involved):
    if ep_wms_used == "Yes":
        return "EP WMS / DAS"
    if customer_system_involved == "Yes":
        return "Customer WMS"
    return "Fixed rule / predefined location"


def _route_nodes(trigger, task_sender, destination_source, execution, ep_wms_used):
    nodes = []

    start_node = TRIGGER_TO_SYSTEM.get(trigger, trigger)
    if start_node and start_node != task_sender:
        nodes.append(start_node)

    if task_sender:
        nodes.append(task_sender)

    if ep_wms_used == "Yes" and task_sender != "EP WMS / DAS":
        nodes.append("EP WMS / DAS")

    nodes.append("EP USP Fleet Manager")

    if execution:
        nodes.append(execution)

    return _dedupe_consecutive(nodes)


def _return_nodes(task_sender, destination_source, statuses, ep_wms_used):
    if not statuses:
        return []

    nodes = []
    if ep_wms_used == "Yes":
        nodes.extend(["EP USP Fleet Manager", "EP WMS / DAS"])

    if destination_source and destination_source not in ["Operator", "Other", "Fixed rule / predefined location"]:
        nodes.append(destination_source)
    elif task_sender and task_sender not in ["Operator", "Other"]:
        nodes.append(task_sender)

    return _dedupe_consecutive(nodes)


def _flow_html(forward_nodes, return_nodes=None, top_labels=None, bottom_labels=None):
    forward_nodes = forward_nodes or []
    return_nodes = return_nodes or []
    top_labels = top_labels or []
    bottom_labels = bottom_labels or []

    def _line(nodes, labels, reverse=False):
        parts = []
        for i, node in enumerate(nodes):
            parts.append(f"<div class='df-node'>{html.escape(str(node))}</div>")
            if i < len(nodes) - 1:
                label_html = ""
                if i < len(labels) and labels[i]:
                    label_html = f"<div class='df-label'>{html.escape(str(labels[i]))}</div>"
                arrow = "←" if reverse else "→"
                parts.append(f"<div class='df-link'>{label_html}<div class='df-arrow'>{arrow}</div></div>")
        return "".join(parts)

    return f"""
    <style>
    .df-wrap {{
        border: 1px solid #d9d9e3;
        border-radius: 14px;
        padding: 16px;
        margin: 8px 0 14px 0;
        background: #fafafa;
    }}
    .df-line {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 10px;
    }}
    .df-node {{
        min-width: 120px;
        max-width: 220px;
        text-align: center;
        padding: 18px 14px;
        border: 2px solid #444;
        border-radius: 12px;
        background: white;
        font-weight: 600;
    }}
    .df-link {{
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 72px;
    }}
    .df-label {{
        font-size: 12px;
        color: #555;
        margin-bottom: 4px;
        text-align: center;
        max-width: 120px;
    }}
    .df-arrow {{
        font-size: 24px;
        font-weight: 700;
        color: #4a4a4a;
        line-height: 1;
    }}
    .df-caption {{
        margin: 4px 0 10px 0;
        color: #666;
        font-size: 13px;
    }}
    </style>
    <div class='df-wrap'>
      <div class='df-caption'>Forward task flow</div>
      <div class='df-line'>{_line(forward_nodes, top_labels, reverse=False)}</div>
      {("<div class='df-caption'>Status / confirmation return</div><div class='df-line'>" + _line(return_nodes, bottom_labels, reverse=True) + "</div>") if return_nodes else ""}
    </div>
    """


def _diagram_text(forward_nodes, return_nodes=None):
    text = " → ".join(_dedupe_consecutive(forward_nodes or []))
    if return_nodes:
        text += "\nReturn: " + " → ".join(_dedupe_consecutive(return_nodes))
    return text


def build_data_flow_inputs(route_details=None, selected_apps=None):
    route_details = route_details or []
    selected_apps = selected_apps or []

    st.subheader("3. Data Flow & Integration")
    st.info(
        "Use this section to define who creates the transport task, which system assigns the destination, and whether external systems connect directly to EP equipment or through EP WMS / DAS."
    )

    integration_required = st.radio(
        "Is integration with other systems required?",
        ["Yes", "No"],
        horizontal=True,
        key="integration_required",
    )

    project_process_name = st.text_input(
        "Project / process name for the integration flow",
        placeholder="e.g. Put-away flow, production feeding, outbound replenishment",
        key="integration_process_name",
    )

    if integration_required == "No":
        return {
            "integration_required": "No",
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
            "ep_wms_used": "No",
            "customer_system_involved": "No",
        }

    col_left, col_right = st.columns(2)

    with col_left:
        ep_wms_used = st.radio(
            "Will EP WMS / DAS be used?",
            ["Yes", "No"],
            horizontal=True,
            key="ep_wms_used",
        )

        customer_system_involved = st.radio(
            "Is there an existing customer WMS / ERP / MES involved?",
            ["Yes", "No"],
            horizontal=True,
            key="customer_system_involved",
        )

        architecture_options = [
            "Customer system → EP WMS / DAS → EP equipment",
            "EP WMS / DAS → EP equipment",
            "Customer system → EP equipment directly",
            "Other",
        ]
        if ep_wms_used == "Yes":
            architecture_options = architecture_options[:2] + ["Other"]

        default_architecture = 0 if customer_system_involved == "Yes" and ep_wms_used == "Yes" else (1 if ep_wms_used == "Yes" else 2)
        system_architecture = st.selectbox(
            "System architecture",
            architecture_options,
            index=min(default_architecture, len(architecture_options) - 1),
            key="system_architecture",
        )

        task_master_options = ["EP WMS / DAS", "Customer WMS", "Customer ERP / MES", "Other"]
        if customer_system_involved == "No":
            task_master_options = ["EP WMS / DAS", "Other"] if ep_wms_used == "Yes" else ["Other"]

        default_task_master = "Customer WMS" if customer_system_involved == "Yes" else ("EP WMS / DAS" if ep_wms_used == "Yes" else "Other")
        if ep_wms_used == "Yes" and customer_system_involved == "Yes":
            default_task_master = "Customer WMS"
        task_master = st.selectbox(
            "Which system is the task master?",
            task_master_options,
            index=task_master_options.index(default_task_master) if default_task_master in task_master_options else 0,
            key="task_master",
        )

    with col_right:
        external_systems = st.multiselect(
            "Which external systems are involved?",
            EXTERNAL_SYSTEMS,
            default=[],
            key="external_systems",
        )

        direct_connection = st.radio(
            "Do the external systems connect directly to EP equipment?",
            ["No, via EP WMS / DAS", "Yes, directly to EP equipment"],
            horizontal=True,
            index=0 if ep_wms_used == "Yes" else 1,
            disabled=(ep_wms_used == "Yes"),
            key="direct_connection_mode",
        )

        interface_protocols = st.multiselect(
            "Interface / protocol type",
            PROTOCOL_OPTIONS,
            default=[],
            key="interface_protocols",
        )

        global_status_feedback = st.multiselect(
            "Which status feedback must EP return?",
            STATUS_OPTIONS,
            default=["Task completed"],
            key="global_status_feedback",
        )

        global_key_data = st.multiselect(
            "Key data items exchanged",
            KEY_DATA_OPTIONS,
            default=["Pallet ID / Barcode", "Pickup location", "Destination / Storage location", "Task completed"],
            key="global_key_data",
        )

    protocol_text = ", ".join(interface_protocols)
    architecture_summary = [
        f"Integration required: {integration_required}",
        f"EP WMS / DAS used: {ep_wms_used}",
        f"Customer system involved: {customer_system_involved}",
        f"System architecture: {system_architecture}",
        f"Task master: {task_master}",
    ]
    if ep_wms_used == "Yes":
        architecture_summary.append("EP WMS / DAS is used and remains the mandatory coordination layer for all defined routes.")

    route_flow_summaries = []
    task_flow_blocks = []
    diagram_blocks = []
    all_connected_nodes = set()
    all_statuses = set(global_status_feedback)
    all_key_data = set(global_key_data)

    st.markdown("### Route-based Data Flow")
    st.caption("Only the material-flow routes you defined are shown below.")

    if not route_details:
        st.warning("No material-flow routes found yet. Please define routes in the Material Flow tab first.")

    equipment_choices = _equipment_options(selected_apps)

    for idx, route in enumerate(route_details or []):
        route_name = f"{route.get('from', 'Start')} → {route.get('to', 'End')}"
        with st.expander(route_name, expanded=(idx == 0)):
            col1, col2 = st.columns(2)

            with col1:
                trigger = st.selectbox(
                    f"Trigger for {route_name}",
                    TRIGGER_OPTIONS,
                    key=f"df_trigger_{idx}",
                )

                sender_options = _route_sender_options(ep_wms_used, customer_system_involved)
                default_sender = _default_sender(trigger, ep_wms_used, customer_system_involved)
                task_sender = st.selectbox(
                    f"Who sends the task for {route_name}?",
                    sender_options,
                    index=sender_options.index(default_sender) if default_sender in sender_options else 0,
                    key=f"df_task_sender_{idx}",
                )

                destination_options = _route_destination_options(ep_wms_used, customer_system_involved)
                default_destination = _default_destination(ep_wms_used, customer_system_involved)
                destination_source = st.selectbox(
                    f"Which system assigns the destination / storage location for {route_name}?",
                    destination_options,
                    index=destination_options.index(default_destination) if default_destination in destination_options else 0,
                    key=f"df_destination_source_{idx}",
                )

            with col2:
                execution_default = equipment_choices[0] if len(equipment_choices) == 1 else equipment_choices[min(idx, len(equipment_choices) - 1)]
                execution = st.selectbox(
                    f"Which EP equipment executes {route_name}?",
                    equipment_choices,
                    index=equipment_choices.index(execution_default) if execution_default in equipment_choices else 0,
                    key=f"df_execution_{idx}",
                )

                route_statuses = st.multiselect(
                    f"Status returned for {route_name}",
                    STATUS_OPTIONS,
                    default=global_status_feedback or ["Task completed"],
                    key=f"df_statuses_{idx}",
                )

                route_key_data = st.multiselect(
                    f"Data exchanged for {route_name}",
                    KEY_DATA_OPTIONS,
                    default=global_key_data or ["Pallet ID / Barcode", "Pickup location", "Destination / Storage location", "Task completed"],
                    key=f"df_data_{idx}",
                )

            route_notes = st.text_area(
                f"Route notes for {route_name}",
                placeholder="Optional route-specific notes, handshake details, queue logic, or exceptions.",
                key=f"df_route_notes_{idx}",
            )

            forward_nodes = _route_nodes(trigger, task_sender, destination_source, execution, ep_wms_used)
            return_nodes = _return_nodes(task_sender, destination_source, route_statuses, ep_wms_used)

            top_labels = []
            if len(forward_nodes) >= 2:
                first_label = "Task trigger" if trigger else ""
                top_labels.append(first_label)
                for edge_i in range(1, len(forward_nodes) - 1):
                    if forward_nodes[edge_i] == "Customer WMS" and destination_source == "Customer WMS":
                        top_labels.append("Pickup + drop-off")
                    elif forward_nodes[edge_i] == "EP WMS / DAS":
                        top_labels.append("Task + destination")
                    elif forward_nodes[edge_i] == "EP USP Fleet Manager":
                        top_labels.append("Task assignment")
                    else:
                        top_labels.append("")
            bottom_labels = [", ".join(route_statuses)] + [""] * max(0, len(return_nodes) - 2) if return_nodes else []

            st.markdown("**Flow preview**")
            st.markdown(_flow_html(forward_nodes, return_nodes, top_labels, bottom_labels), unsafe_allow_html=True)

            diagram_line = _diagram_text(forward_nodes, return_nodes)
            task_block = [
                f"{route_name}:",
                f"Trigger: {trigger}",
                f"Task sender: {task_sender}",
                f"Destination source: {destination_source}",
                f"Execution: {execution}",
                f"Integration path: {' → '.join(forward_nodes)}",
            ]
            if return_nodes:
                task_block.append(f"Return path: {' → '.join(return_nodes)}")
            if route_statuses:
                task_block.append(f"Status returned: {', '.join(route_statuses)}")
            if route_key_data:
                task_block.append(f"Data exchanged: {', '.join(route_key_data)}")
            if route_notes.strip():
                task_block.append(f"Route notes: {route_notes.strip()}")

            task_flow_blocks.append("\n".join(task_block))
            diagram_blocks.append(f"{route_name}:\n{diagram_line}")
            all_connected_nodes.update(forward_nodes)
            all_connected_nodes.update(return_nodes)
            all_statuses.update(route_statuses)
            all_key_data.update(route_key_data)

            route_flow_summaries.append({
                "route_name": route_name,
                "trigger": trigger,
                "task_sender": task_sender,
                "destination_source": destination_source,
                "execution": execution,
                "statuses": route_statuses,
                "key_data": route_key_data,
                "notes": route_notes.strip(),
                "forward_nodes": forward_nodes,
                "return_nodes": return_nodes,
                "diagram_line": diagram_line,
            })

    integration_req = "\n".join(architecture_summary)
    data_flow_text = "\n\n".join(diagram_blocks)
    connections = external_systems
    connections_details = []
    if protocol_text:
        connections_details.append(f"Interface / protocol: {protocol_text}")
    if direct_connection:
        connections_details.append(f"Connection mode: {direct_connection}")
    connections_details_text = "\n".join(connections_details)

    additional_notes = st.text_area(
        "Additional Notes / Special Requirements (optional)",
        height=90,
        placeholder="Fallback behavior, retry logic, queue handling, cybersecurity notes, or any special customer IT requirements.",
        key="data_flow_additional_notes",
    )

    st.markdown("### Preview of generated data-flow summary")
    st.code("\n\n".join([integration_req, *task_flow_blocks]) if task_flow_blocks else integration_req)

    return {
        "integration_required": integration_required,
        "integration_process_name": project_process_name,
        "ep_wms_used": ep_wms_used,
        "customer_system_involved": customer_system_involved,
        "system_architecture": system_architecture,
        "task_master": task_master,
        "integration_req": integration_req,
        "data_flow_text": "\n\n".join(task_flow_blocks),
        "connections": connections,
        "connections_details": connections_details_text,
        "data_flow_additional_notes": additional_notes.strip(),
        "system_architecture_text": system_architecture,
        "integration_route_text": system_architecture,
        "data_flow_diagram_text": "\n\n".join(diagram_blocks),
        "task_flow_text": "\n\n".join(task_flow_blocks),
        "connected_systems_text": "\n".join(sorted(node for node in all_connected_nodes if node)),
        "status_feedback_text": "\n".join(sorted(s for s in all_statuses if s)),
        "key_data_exchange_text": "\n".join(sorted(k for k in all_key_data if k)),
        "route_flow_summaries": route_flow_summaries,
    }
