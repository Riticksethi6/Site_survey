# secondary_tab.py – Material Flow / Transport Paths / Photos

import streamlit as st
from io import BytesIO
from PIL import Image

def build_material_flow_inputs():
    st.subheader("2. Material Flow & Transport Paths")

    st.markdown("**Specify key transport paths and distances in the warehouse**")

    # Collect multiple flow steps dynamically
    num_flows = st.number_input(
        "Number of Transport Flows / Jobs",
        min_value=1,
        max_value=10,
        value=1,
        step=1,
        key="num_flows"
    )

    flow_steps = []
    distances = []
    photos = []

    for i in range(num_flows):
        st.markdown(f"**Flow Step #{i+1}**")
        col1, col2 = st.columns(2)

        with col1:
            start_point = st.text_input(
                f"Start Location #{i+1}",
                placeholder="e.g. Receiving Area",
                key=f"start_{i}"
            )
            end_point = st.text_input(
                f"End Location #{i+1}",
                placeholder="e.g. Storage Zone A",
                key=f"end_{i}"
            )
        with col2:
            distance_m = st.number_input(
                f"Distance [m] Step #{i+1}",
                min_value=1.0,
                max_value=500.0,
                value=50.0,
                step=1.0,
                key=f"distance_{i}"
            )
            photo = st.file_uploader(
                f"Upload Photo (optional) Step #{i+1}",
                type=["png", "jpg", "jpeg"],
                key=f"photo_{i}"
            )

        flow_steps.append({
            "start": start_point.strip(),
            "end": end_point.strip(),
            "distance_m": distance_m
        })
        distances.append(distance_m)
        if photo:
            photos.append(BytesIO(photo.read()))
        else:
            photos.append(None)

    # Optional extra notes
    general_notes = st.text_area(
        "Additional Notes / Special Requirements",
        height=80,
        placeholder="e.g. high-traffic zones, forklifts crossing, conveyor integration",
        key="material_flow_notes"
    )

    return {
        "flow_steps": flow_steps,
        "distances": distances,
        "photos": photos,
        "material_flow_notes": general_notes.strip()
    }