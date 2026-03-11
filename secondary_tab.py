# secondary_tab.py

import streamlit as st


FLOW_OPTIONS = [
    "Inbound",
    "Production",
    "Buffer Storage",
    "Rack Storage",
    "Floor Storage",
    "Outbound",
]


def build_material_flow_inputs():
    st.subheader("2. Material Flow")
    st.markdown("### Material Flow Sequence")
    st.caption("Example: Inbound → Buffer Storage → Stacking → Production")
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

        source_image = st.file_uploader(
            f"Upload Image / Layout for {source_step}",
            type=["jpg", "jpeg", "png", "pdf"],
            key=f"route_source_image_{i}"
        )

        route_details.append({
            "from": source_step,
            "to": target_step,
            "pallets_per_hour": pallets_per_hour,
            "avg_distance_m": avg_distance,
            "source_image": source_image,
        })

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

    # Readable summary for Word template
    route_summary_lines = []
    for route in route_details:
        route_summary_lines.append(
            f"{route['from']} → {route['to']} | "
            f"Pallets/hour: {route['pallets_per_hour']} | "
            f"Average distance: {route['avg_distance_m']} m"
        )

    route_summary = "\n".join(route_summary_lines)

    return {
        "flow_sequence": flow_sequence,
        "flow_steps": flow_steps,
        "route_details": route_details,
        "route_summary": route_summary,
        "material_flow_text": material_flow_text,
        "special_comments": special_comments,
        "distances": distances,
        "photos": [img for img in route_images if img],
    }