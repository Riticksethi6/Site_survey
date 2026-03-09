# header_tab.py – Customer, Project & Application Inputs

import streamlit as st

def build_header_inputs():
    st.subheader("1. Basic Information / Customer Details")

    # Customer Details
    col1, col2 = st.columns(2)
    with col1:
        customer_name = st.text_input(
            "Customer Name",
            placeholder="e.g. ABC Logistics",
            key="customer_name"
        )
        customer_email = st.text_input(
            "Customer Email",
            placeholder="e.g. contact@abc-logistics.com",
            key="customer_email"
        )
    with col2:
        customer_mobile = st.text_input(
            "Customer Mobile / Phone",
            placeholder="e.g. +49 123 456789",
            key="customer_mobile"
        )
        customer_address = st.text_area(
            "Site Address",
            height=60,
            placeholder="Street, City, Country",
            key="customer_address"
        )

    # Warehouse Details
    st.markdown("**Warehouse & Layout Details**")
    warehouse_area = st.number_input(
        "Warehouse Area [m²]",
        min_value=50.0,
        value=2000.0,
        step=50.0,
        key="warehouse_area"
    )

    ceiling_height_m = st.number_input(
        "Ceiling Height [m]",
        min_value=2.0,
        value=6.0,
        step=0.1,
        key="ceiling_height_m"
    )

    max_stacking_height_m = st.number_input(
        "Max Stacking Height [m]",
        min_value=1.0,
        value=3.0,
        step=0.1,
        key="max_stacking_height_m"
    )

    st.markdown("**Application / Job Type**")
    application = st.multiselect(
        "Select Application(s)",
        ["Transport / Cross Docking", "Stacking / Conveyor", "Narrow Aisle", "Custom"],
        default=["Transport / Cross Docking"],
        key="application"
    )

    # Pallet / Load Details
    col3, col4 = st.columns(2)
    with col3:
        pallet_type = st.selectbox(
            "Pallet Type",
            ["EUR / EPAL", "Custom", "Other"],
            key="pallet_type"
        )
        pallet_dimensions = st.text_input(
            "Pallet Dimensions [L×W×H mm]",
            placeholder="e.g. 1200×800×144",
            key="pallet_dimensions"
        )
        max_weight_kg = st.number_input(
            "Max Load Weight [kg]",
            min_value=50.0,
            value=1000.0,
            step=10.0,
            key="load_weight_kg"
        )

    with col4:
        forklift_entry_width_mm = st.number_input(
            "Fork Entry Width [mm]",
            min_value=200,
            value=320,
            step=10,
            key="fork_entry_width"
        )
        max_transport_m = st.number_input(
            "Max Transport Distance [m]",
            min_value=5.0,
            value=50.0,
            step=1.0,
            key="max_transport_m"
        )
        stacking_type = st.selectbox(
            "Stacking Type",
            ["Single", "Double", "Mixed"],
            key="stacking_type"
        )

    # Optional / Special Requirements
    special_layout = st.text_area(
        "Special Layout / Constraints",
        height=60,
        placeholder="e.g. narrow aisles, pallet types, high bay racks",
        key="special_layout"
    )

    conveyor_picture = st.file_uploader(
        "Upload Conveyor / Layout Picture (optional)",
        type=["png", "jpg", "jpeg"],
        key="conveyor_picture"
    )

    cad_file = st.file_uploader(
        "Upload CAD / Layout File (optional)",
        type=["dwg", "dxf", "pdf"],
        key="cad_file"
    )

    return {
        "customer_name": customer_name.strip(),
        "customer_email": customer_email.strip(),
        "customer_mobile": customer_mobile.strip(),
        "customer_address": customer_address.strip(),
        "warehouse_area": warehouse_area,
        "ceiling_height_m": ceiling_height_m,
        "max_stacking_height_m": max_stacking_height_m,
        "application": application,
        "pallet_type": pallet_type,
        "pallet_dimensions": pallet_dimensions.strip(),
        "load_weight_kg": max_weight_kg,
        "fork_entry_width": forklift_entry_width_mm,
        "max_transport_m": max_transport_m,
        "stacking_type": stacking_type,
        "special_layout": special_layout.strip(),
        "conveyor_picture": conveyor_picture,
        "cad_file": cad_file
    }