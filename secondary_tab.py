# secondary_tab.py

import streamlit as st


def build_material_flow_inputs():
    st.subheader("2. Material Flow")

    flow_steps = st.text_area(
        "Material Flow Steps",
        height=120,
        placeholder="Example: Goods receipt → buffer area → storage → picking → shipping",
        key="flow_steps"
    )

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

    st.markdown("### Transport Distances")

    num_routes = st.number_input(
        "Number of Main Transport Routes",
        min_value=0,
        max_value=10,
        value=1,
        step=1,
        key="num_routes"
    )

    distances = []
    for i in range(1, num_routes + 1):
        dist = st.number_input(
            f"Distance for Route {i} [m]",
            min_value=0.0,
            value=25.0 if i == 1 else 0.0,
            step=0.5,
            key=f"distance_route_{i}"
        )
        distances.append(dist)

    st.markdown("### Material Flow Photos")
    photos = st.file_uploader(
        "Upload Site / Material Flow Photos",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key="material_flow_photos"
    )

    st.markdown("### Zone Layout Uploads")
    inbound_zone_file = st.file_uploader(
        "Upload Inbound Zone Layout / Picture",
        type=["jpg", "jpeg", "png", "pdf", "dwg", "zip"],
        key="inbound_zone_file"
    )

    outbound_zone_file = st.file_uploader(
        "Upload Outbound Zone Layout / Picture",
        type=["jpg", "jpeg", "png", "pdf", "dwg", "zip"],
        key="outbound_zone_file"
    )

    storage_zone_file = st.file_uploader(
        "Upload Storage Zone Layout / Picture",
        type=["jpg", "jpeg", "png", "pdf", "dwg", "zip"],
        key="storage_zone_file"
    )

    production_zone_file = st.file_uploader(
        "Upload Production Zone Layout / Picture",
        type=["jpg", "jpeg", "png", "pdf", "dwg", "zip"],
        key="production_zone_file"
    )

    staging_zone_file = st.file_uploader(
        "Upload Staging / Buffer Zone Layout / Picture",
        type=["jpg", "jpeg", "png", "pdf", "dwg", "zip"],
        key="staging_zone_file"
    )

    other_zone_file = st.file_uploader(
        "Upload Other Zone Layout / Picture",
        type=["jpg", "jpeg", "png", "pdf", "dwg", "zip"],
        key="other_zone_file"
    )

    return {
        "flow_steps": flow_steps,
        "material_flow_text": material_flow_text,
        "special_comments": special_comments,
        "distances": distances,
        "photos": photos if photos else [],
        "inbound_zone_file": inbound_zone_file,
        "outbound_zone_file": outbound_zone_file,
        "storage_zone_file": storage_zone_file,
        "production_zone_file": production_zone_file,
        "staging_zone_file": staging_zone_file,
        "other_zone_file": other_zone_file,
    }