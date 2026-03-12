# secondary_tab.py

import streamlit as st


FLOW_OPTIONS = [
    "Inbound",
    "Buffer Storage",
    "Rack Storage",
    "Floor Storage",
    "Production",
    "Outbound",
    "Conveyor",
    "Packing",
    "Sorting",
    "Charging Area",
    "Quality Check",
    "Other"
]


def build_material_flow_inputs():
    st.subheader("2. Material Flow")

    st.markdown("### Material Flow Sequence")
    st.caption("Example: Inbound → Buffer Storage → Stacking → Production")

    num_steps = st.number_input(
        "Number of Steps in Material Flow",
        min_value=2,
        max_value=20,
        value=3,
        step=1,
        key="num_flow_steps"
    )

    flow_steps = []

    for i in range(1, num_steps + 1):
        step_value = st.selectbox(
            f"Step {i}",
            FLOW_OPTIONS,
            key=f"flow_step_{i}"
        )

        if step_value == "Other":
            step_value = st.text_input(
                f"Specify Step {i}",
                key=f"flow_step_other_{i}"
            )

        flow_steps.append(step_value)

    route_summary = " → ".join([step for step in flow_steps if step])

    st.markdown("### Flow Details Between Steps")

    distances = []
    pallets_per_hour_list = []
    step_images = []

    for i in range(len(flow_steps) - 1):
        st.markdown(f"#### From Step {i+1} to Step {i+2}")
        st.write(f"**{flow_steps[i]} → {flow_steps[i+1]}**")

        col1, col2 = st.columns(2)

        with col1:
            pallets_per_hour = st.number_input(
                f"Pallets per Hour ({flow_steps[i]} → {flow_steps[i+1]})",
                min_value=0,
                value=50,
                step=1,
                key=f"pallets_per_hour_{i}"
            )

        with col2:
            avg_distance = st.number_input(
                f"Average Distance in meters ({flow_steps[i]} → {flow_steps[i+1]})",
                min_value=0.0,
                value=10.0,
                step=0.5,
                key=f"avg_distance_{i}"
            )

        step_image = st.file_uploader(
            f"Upload image for {flow_steps[i]}",
            type=["jpg", "jpeg", "png", "pdf"],
            key=f"step_image_{i}"
        )

        pallets_per_hour_list.append(pallets_per_hour)
        distances.append(avg_distance)
        step_images.append(step_image)

    material_flow_text = st.text_area(
        "Material Flow Details",
        height=120,
        placeholder="Describe how pallets move through the site, including pickup and drop-off points.",
        key="material_flow_text"
    )

    special_comments = st.text_area(
        "Special Comments / Exceptions",
        height=100,
        placeholder="Mention any special routes, priority flows, blocked zones, or special handling requirements.",
        key="special_comments"
    )

    return {
        "flow_steps": flow_steps,
        "route_summary": route_summary,
        "distances": distances,
        "pallets_per_hour_flow": pallets_per_hour_list,
        "photos": step_images,
        "material_flow_text": material_flow_text,
        "special_comments": special_comments,
    }