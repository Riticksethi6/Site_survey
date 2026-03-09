# header_tab.py – Complete version with Transport/Cross Docking sub-type, aisle for both,
# pickup type for Stacking/Conveyor, conveyor picture, short description after application

import streamlit as st
from datetime import datetime
from product_validators import validate_xpl201, validate_xqe122, validate_xna121_151

def build_header_inputs():
    st.subheader("1. Basic Information")

    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name *", key="customer_name")
        customer_email = st.text_input("Customer Email *", key="customer_email")
        customer_mobile = st.text_input("Customer Mobile Number *", key="customer_mobile")

        project_name = st.text_input("Project Name", key="project_name")
        project_location = st.text_input("Project Location", key="project_location")

    with col2:
        survey_date = st.date_input("Survey Date", datetime.today(), key="survey_date")

    # Checkbox to add multiple pallets
    add_multiple_pallets = st.checkbox("Add Multiple Pallets", key="add_multiple_pallets")

    # List to hold pallet data
    pallets = []

    # First pallet always shown
    st.markdown("#### Pallet 1")
    pallet_type_1 = st.radio("Type of Pallets", ["Euro", "Industrial", "Other"], horizontal=True, key="pallet_type_1")

    other_pallet_type_1 = ""
    if pallet_type_1 == "Other":
        other_pallet_type_1 = st.text_input("Specify pallet type", key="other_pallet_type_1")

    load_dimensions_1 = st.text_input("Load Dimensions (L×W×H) [mm]", "1200×800×1500", key="load_dimensions_1")

    # Parse L and W for insertion depth options
    dimensions_parts = load_dimensions_1.split('×')
    options = []
    if len(dimensions_parts) >= 2:
        try:
            l = int(dimensions_parts[0].strip())
            w = int(dimensions_parts[1].strip())
            options = [l, w]
        except ValueError:
            pass

    pallet_width_mm_1 = st.selectbox("Insertion Depth (Fork Entry) [mm]", options if options else [1200], key="pallet_width_mm_1")

    pallets.append({
        "pallet_type": pallet_type_1,
        "other_pallet_type": other_pallet_type_1,
        "load_dimensions": load_dimensions_1,
        "pallet_width_mm": pallet_width_mm_1
    })

    # Additional pallets if checkbox is selected
    if add_multiple_pallets:
        num_additional = st.number_input("Number of Additional Pallets", min_value=1, max_value=5, value=1, key="num_additional_pallets")
        for i in range(1, num_additional + 1):
            st.markdown(f"#### Pallet {i+1}")
            pallet_type_i = st.radio(f"Type of Pallets {i+1}", ["Euro", "Industrial", "Other"], horizontal=True, key=f"pallet_type_{i+1}")

            other_pallet_type_i = ""
            if pallet_type_i == "Other":
                other_pallet_type_i = st.text_input(f"Specify pallet type {i+1}", key=f"other_pallet_type_{i+1}")

            load_dimensions_i = st.text_input(f"Load Dimensions (L×W×H) [mm] {i+1}", "1200×800×1500", key=f"load_dimensions_{i+1}")

            # Parse L and W for insertion depth options
            dimensions_parts_i = load_dimensions_i.split('×')
            options_i = []
            if len(dimensions_parts_i) >= 2:
                try:
                    l_i = int(dimensions_parts_i[0].strip())
                    w_i = int(dimensions_parts_i[1].strip())
                    options_i = [l_i, w_i]
                except ValueError:
                    pass

            pallet_width_mm_i = st.selectbox(f"Insertion Depth (Fork Entry) [mm] {i+1}", options_i if options_i else [1200], key=f"pallet_width_mm_{i+1}")

            pallets.append({
                "pallet_type": pallet_type_i,
                "other_pallet_type": other_pallet_type_i,
                "load_dimensions": load_dimensions_i,
                "pallet_width_mm": pallet_width_mm_i
            })

    # Application(s) after customer info
    st.markdown("### Application(s) * (select all that apply)")
    application = st.multiselect(
        "Select all that apply",
        ["Transport / Cross Docking", "Stacking/Conveyor", "Narrow Aisle", "Other"],
        key="application"
    )

    # Short description right after application
    task_description = st.text_area("Job-To-Do", height=120, key="task_description")

    st.markdown("### Application-Specific Requirements")

    # Transport / Cross Docking
    xpl_sub_type = None
    cross_docking_aisle = None
    if "Transport / Cross Docking" in application:
        xpl_sub_type = st.radio("Select Application Type", ["Transport", "Cross Docking"], key="xpl_sub_type")
        cross_docking_aisle = st.number_input(
            "Aisle Width in Operation Zone [m]",
            min_value=1.0,
            value=1.8,
            step=0.1,
            help="Recommended minimum 1.8 m for one-way driving/loading (conservative value).",
            key="cross_docking_aisle"
        )

    # Stacking / Conveyor
    pickup_type = None
    stacking_type = None
    storage_layout = ""
    box_distance_mm = 0
    aisle_width_mm = 0
    conveyor_height = 0
    conveyor_picture = None
    load_at_edge = "Yes"
    distance_from_edge = 0

    if "Stacking/Conveyor" in application:
        st.info("Stacking / Conveyor (XQE122): 1200 kg up to 4.5 m, 1500 kg up to 3.5 m")
        pickup_type = st.radio("Pickup Type", ["Ground", "Conveyor", "Other"], key="pickup_type")
        stacking_type = st.radio("Stacking Type", ["Floor Stacking", "Rack Stacking", "Other"], key="stacking_type")

        if stacking_type == "Floor Stacking":
            storage_layout = st.text_area("Storage Layout Description", height=80, key="storage_layout")
            box_distance_mm = st.number_input("Distance between 2 boxes stacked next to each other [mm]", min_value=0, value=200, step=1, key="box_distance_mm")
            aisle_width_mm = st.number_input("Floor Storage Aisle Width [mm]", min_value=0, value=1640, step=1, key="aisle_width_mm")
        if stacking_type == "Rack Stacking":
            box_distance_mm = st.number_input("Distance between boxes on racks [mm]", min_value=0, value=75, step=1, key="box_distance_mm")
            aisle_width_mm = st.number_input("Aisle Width for Rack Stacking [mm] (pallet to pallet)", min_value=0, value=2850, step=1, key="aisle_width_mm")
        if pickup_type == "Conveyor":
            conveyor_height = st.number_input("Conveyor Height [mm]", min_value=0, value=0, step=1, key="conveyor_height")
            conveyor_picture = st.file_uploader("Upload Conveyor Picture", type=["jpg", "png", "pdf"], key="conveyor_picture")
            load_at_edge = st.radio("Does the load arrive at the edge of the conveyor?", ["Yes", "No"], key="load_at_edge")
            if load_at_edge == "No":
                distance_from_edge = st.number_input("Specify distance from conveyor edge to pallet [mm]", min_value=0, value=0, step=1, key="distance_from_edge")

    # Load weight
    load_weight_kg = st.number_input("Load Weight [kg]", min_value=0, value=1200, step=1, key="load_weight_kg")

    # Max stacking height
    max_stacking_height_m = st.number_input("Maximum Stacking Height [m]", min_value=0.0, value=3.0, step=0.1, key="max_stacking_height_m")

    # Narrow Aisle
    aisle_width_m = st.number_input("Actual Aisle Width [m] (Narrow Aisle)", min_value=1.5, value=1.8, step=0.1, key="aisle_width_m")
    xna_model = st.selectbox("Preferred Model", ["XNA121 (up to 8.5m)", "XNA151 (up to 13m)"], key="xna_model")

    # Validations
    if "Transport / Cross Docking" in application and cross_docking_aisle is not None:
        is_valid, msg, color = validate_xpl201(cross_docking_aisle, load_weight_kg)
        if color == "red": st.error(msg)
        elif color == "orange": st.warning(msg)
        else: st.success(msg)

    if "Stacking/Conveyor" in application:
        is_valid, msg, color = validate_xqe122(load_weight_kg, max_stacking_height_m)
        if color == "red": st.error(msg)
        elif color == "orange": st.warning(msg)
        else: st.success(msg)

    if "Narrow Aisle" in application:
        is_valid, msg, color = validate_xna121_151(aisle_width_m, load_weight_kg, max_stacking_height_m, xna_model)
        if color == "red": st.error(msg)
        elif color == "orange": st.warning(msg)
        else: st.success(msg)

    # Operational Basics & CAD
    avg_transport_m = st.number_input("Average Travelling Distance [m]", min_value=0.0, value=30.0, key="avg_transport_m")
    pallets_per_hour = st.number_input("Pallets per Hour (peak)", min_value=0, value=50, key="pallets_per_hour")
    shifts_per_day = st.number_input("Shifts per Day", 1, 3, value=2, key="shifts_per_day")
    cad_file = st.file_uploader("Upload CAD file", type=["dwg", "pdf", "png", "jpg", "jpeg", "zip"], key="cad_layout_file")

    return {
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_mobile": customer_mobile,
        "project_name": project_name,
        "project_location": project_location,
        "survey_date": survey_date.strftime("%Y-%m-%d"),
        "application": application,
        "task_description": task_description,
        "pallets": pallets,
        "cross_docking_aisle": cross_docking_aisle,
        "fork_entry_width": st.session_state.get("fork_entry_width", 320),  # keep for template
        "aisle_width_m": aisle_width_m,
        "xpl_sub_type": xpl_sub_type,
        "pickup_type": pickup_type,
        "stacking_type": stacking_type,
        "storage_layout": storage_layout,
        "box_distance_mm": box_distance_mm,
        "aisle_width_mm": aisle_width_mm,
        "conveyor_height": conveyor_height,
        "conveyor_picture": conveyor_picture,
        "load_at_edge": load_at_edge,
        "distance_from_edge": distance_from_edge,
        "avg_transport_m": avg_transport_m,
        "pallets_per_hour": pallets_per_hour,
        "shifts_per_day": shifts_per_day,
        "load_weight_kg": load_weight_kg,
        "max_stacking_height_m": max_stacking_height_m,
        "cad_file": cad_file,
        "xna_model": xna_model
    }