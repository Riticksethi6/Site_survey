# secondary_tab.py – Material Flow (CAD upload moved to header tab)

import streamlit as st

def build_material_flow_inputs():
    st.subheader("2. Material Flow")

    flow_steps = st.multiselect(
        "Material Flow Sequence (in order)",
        options=["Inbound", "Rack Storage", "Floor/Block Storage", "Production", "Outbound", "Buffer Storage", "Other"],
        default=["Inbound", "Rack Storage", "Production", "Outbound"],
        key="flow_steps"
    )

    flow_summary = "Flow Sequence: " + " → ".join(flow_steps) + "\n\n"
    distances = []
    photos = []

    for i, step in enumerate(flow_steps):
        st.markdown(f"**Step {i+1}: {step}**")

        desc = st.text_area(
            f"Description for {step}",
            height=80,
            key=f"{step}_desc_{i}"  # unique key to avoid collision
        )

        photo = st.file_uploader(
            f"Photo / Diagram for {step}",
            type=["jpg", "jpeg", "png", "pdf"],
            key=f"{step}_photo_{i}"
        )

        pph = st.number_input(
            f"Pallets per Hour in {step}",
            min_value=0,
            value=30,
            step=1,
            key=f"{step}_pph_{i}"
        )

        distance = 0.0
        if i < len(flow_steps) - 1:
            next_step = flow_steps[i + 1]
            distance = st.number_input(
                f"Distance from {step} to {next_step} [m]",
                min_value=0.0,
                value=30.0,
                step=0.5,
                key=f"dist_{step}_{next_step}_{i}"
            )

        # Build summary text
        flow_summary += f"{step}: {desc} ({pph} pallets/hour)"
        if distance > 0:
            flow_summary += f" – {distance} m to {next_step}"
            distances.append(distance)
        flow_summary += "\n\n"

        if photo:
            photos.append(photo)

    special_comments = st.text_area(
        "Special Comments / Direct Flows / Notes",
        height=100,
        key="special_comments"
    )

    if special_comments.strip():
        flow_summary += f"\n\nSpecial Comments / Direct Flows (highlighted):\n{special_comments}"

    return {
        "material_flow_text": flow_summary.strip(),
        "flow_steps": " → ".join(flow_steps),
        "special_comments": special_comments,
        "distances": distances,
        "photos": photos  # list of uploaded file objects → handled in app.py
    }