import streamlit as st


FLOW_OPTIONS = [
    "Inbound",
    "Production",
    "Buffer Storage",
    "Rack Storage",
    "Floor Storage",
    "Outbound",
]

PROCESS_TIMING_OPTIONS = [
    "Simultaneous / continuous",
    "On request / intermittent",
]


def _format_route_summary(route: dict) -> str:
    return (
        f"{route['from']} → {route['to']} | "
        f"Pallets/hour: {route['pallets_per_hour']} | "
        f"Average distance: {route['avg_distance_m']} m | "
        f"Flow type: {route['process_type']}"
    )


def _format_step_detail(route: dict) -> str:
    base = (
        f"From {route['from']} to {route['to']}: "
        f"{route['avg_distance_m']} m, with a capacity of {route['pallets_per_hour']} pallets per hour"
    )
    if route["process_type"] == "On request / intermittent":
        return base + " (on request)."
    return base + "."


def _format_process_efficiency(route: dict) -> str:
    line = f"{route['from']} → {route['to']}: {route['pallets_per_hour']} pallets/hour"
    if route["process_type"] == "On request / intermittent":
        line += " (on request)"
    return line


def build_material_flow_inputs():
    st.subheader("2. Material Flow")

    st.markdown("### Material Flow Sequence")

    num_steps = st.number_input(
        "Number of Steps in Material Flow",
        min_value=2,
        max_value=6,
        value=3,
        step=1,
        key="num_flow_steps"
    )

    flow_sequence = []
    used_steps = []

    for i in range(1, num_steps + 1):
        remaining_options = [opt for opt in FLOW_OPTIONS if opt not in used_steps]

        step_value = st.selectbox(
            f"Step {i}",
            remaining_options,
            key=f"flow_step_{i}"
        )

        flow_sequence.append(step_value)
        used_steps.append(step_value)

    flow_steps = " → ".join(flow_sequence)

    st.markdown("### Flow Details Between Steps")
    st.caption(
        "For each route, enter the transport distance and route capacity. "
        "Mark whether the flow is continuous/simultaneous or only triggered on request."
    )

    route_details = []
    distances = []
    route_images = []

    for i in range(len(flow_sequence) - 1):
        source_step = flow_sequence[i]
        target_step = flow_sequence[i + 1]

        st.markdown(f"#### {source_step} → {target_step}")

        col1, col2 = st.columns(2)

        with col1:
            pallets_per_hour = st.number_input(
                f"Pallets per Hour: {source_step} → {target_step}",
                min_value=0,
                value=50,
                step=1,
                key=f"route_pallets_per_hour_{i}"
            )

        with col2:
            avg_distance = st.number_input(
                f"Average Distance [m]: {source_step} → {target_step}",
                min_value=0.0,
                value=25.0,
                step=0.5,
                key=f"route_avg_distance_{i}"
            )

        process_type = st.radio(
            f"Flow Timing: {source_step} → {target_step}",
            PROCESS_TIMING_OPTIONS,
            horizontal=True,
            key=f"route_process_type_{i}"
        )

        source_image = st.file_uploader(
            f"Upload Image / Layout for {source_step}",
            type=["jpg", "jpeg", "png", "pdf"],
            key=f"route_source_image_{i}"
        )

        route = {
            "from": source_step,
            "to": target_step,
            "pallets_per_hour": pallets_per_hour,
            "avg_distance_m": avg_distance,
            "process_type": process_type,
            "source_image": source_image,
        }
        route_details.append(route)
        distances.append(avg_distance)
        route_images.append(source_image)

    st.markdown("### Material Flow Summary")

    material_flow_text = st.text_area(
        "Material Flow Details",
        height=140,
        placeholder="Describe how pallets move through the site, including pickup and drop-off points.",
        key="material_flow_text"
    )

    special_comments = st.text_area(
        "Special Comments / Exceptions",
        height=100,
        placeholder="Mention any special routes, priority flows, blocked zones, or special handling requirements.",
        key="special_comments"
    )

    route_summary = "\n".join(_format_route_summary(route) for route in route_details)
    step_details_text = "\n".join(_format_step_detail(route) for route in route_details)
    process_efficiency_text = "\n".join(_format_process_efficiency(route) for route in route_details)
    flow_pairs_text = "\n".join(f"{route['from']} → {route['to']}: {route['avg_distance_m']} m" for route in route_details)

    simultaneous_total = sum(
        route["pallets_per_hour"]
        for route in route_details
        if route["process_type"] == "Simultaneous / continuous"
    )

    on_request_routes = [
        f"{route['from']} → {route['to']}"
        for route in route_details
        if route["process_type"] == "On request / intermittent"
    ]

    operational_efficiency_note = ""
    if on_request_routes:
        route_list = ", ".join(on_request_routes)
        operational_efficiency_note = (
            f"The following flows do not always happen simultaneously and are triggered only when required: {route_list}."
        )

    return {
        "flow_sequence": flow_sequence,
        "flow_steps": flow_steps,
        "route_details": route_details,
        "route_summary": route_summary,
        "material_flow_text": material_flow_text,
        "special_comments": special_comments,
        "distances": distances,
        "photos": [img for img in route_images if img],
        "flow_pairs_text": flow_pairs_text,
        "step_details_text": step_details_text,
        "process_efficiency_text": process_efficiency_text,
        "simultaneous_pallets_per_hour": simultaneous_total,
        "operational_efficiency_note": operational_efficiency_note,
    }
