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

    # ── Transport / Cross Docking ───────────────────────────────────────────────
    xpl_sub_type = None
    cross_docking_aisle = None
    if "Transport / Cross Docking" in application:
        xpl_sub_type = st.radio(
            "Select Application Type",
            ["Transport", "Cross Docking"],
            key="xpl_sub_type"
        )

        cross_docking_aisle = st.number_input(
            "Aisle Width in Operation Zone [m]",
            min_value=1.0,
            value=1.8,
            step=0.1,
            help="Recommended minimum 1.8 m for one-way driving/loading (conservative value). "
                 "Refer to XPL Layout and Aisle Planning Specification for details "
                 "(e.g., 1.5–1.8 m driving, 3.0 m loading one side, etc.).",
            key="cross_docking_aisle"
        )

    # ── Stacking / Conveyor ──────────────────────────────────────────────────────
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
        fork_entry_width = st.number_input("Fork Entry Width Required (min 320 mm)", min_value=0, value=320, step=1, key="fork_entry_width")  # integer

        pickup_type = st.radio("Pickup Type", ["Ground", "Conveyor", "Other"], key="pickup_type")

        # Stacking Type shows for all pickup types
        stacking_type = st.radio("Stacking Type", ["Floor Stacking", "Rack Stacking", "Other"], key="stacking_type")

        if stacking_type == "Floor Stacking":
            storage_layout = st.text_area("Storage Layout Description", height=80, key="storage_layout")
            box_distance_mm = st.number_input("Distance between 2 boxes stacked next to each other [mm]", min_value=0, value=200, step=1, key="box_distance_mm")  # integer
            if box_distance_mm < 200:
                st.error("Minimum distance between boxes for floor stacking is 200 mm. Not accepted.")
            aisle_width_mm = st.number_input("Aisle Width for Floor Stacking [mm]", min_value=0, value=1640, step=1, key="aisle_width_mm")  # integer
            if aisle_width_mm < 1640:
                st.error("Minimum aisle width for floor stacking is 1640 mm (1240 mm truck width + 200 mm both sides). Not accepted.")

        if stacking_type == "Rack Stacking":
            box_distance_mm = st.number_input("Distance between boxes on racks [mm]", min_value=0, value=75, step=1, key="box_distance_mm")  # integer
            if box_distance_mm < 75:
                st.error("Minimum distance between boxes for rack stacking is 75 mm. Not accepted.")
            aisle_width_mm = st.number_input("Aisle Width for Rack Stacking [mm] (pallet to pallet)", min_value=0, value=2850, step=1, key="aisle_width_mm")  # integer
            if aisle_width_mm < 2850:
                st.error("Minimum aisle width for rack stacking is 2850 mm (pallet to pallet). Not accepted.")

        if pickup_type == "Conveyor":
            conveyor_height = st.number_input("Conveyor Height [mm]", min_value=0, value=0, step=1, key="conveyor_height")  # integer
            conveyor_picture = st.file_uploader("Upload Conveyor Picture", type=["jpg", "png", "pdf"], key="conveyor_picture")
            load_at_edge = st.radio("Does the load arrive at the edge of the conveyor?", ["Yes", "No"], key="load_at_edge")
            if load_at_edge == "No":
                distance_from_edge = st.number_input("Specify distance from conveyor edge to pallet [mm]", min_value=0, value=0, step=1, key="distance_from_edge")  # integer

    # ── Narrow Aisle ─────────────────────────────────────────────────────────────
    if "Narrow Aisle" in application:
        st.info("Narrow Aisle (XNA121 / XNA151): 1.78–2.0 m aisle width")
        aisle_width_m = st.number_input("Actual Aisle Width [m] (must be 1.78–2.0 m)", min_value=1.5, value=1.8, step=0.1, key="aisle_width_m")
        xna_model = st.selectbox("Preferred Model", ["XNA121 (up to 8.5m)", "XNA151 (up to 13m)"], key="xna_model")

    # ── Load weight (if relevant) ────────────────────────────────────────────────
    load_weight_kg = 1200
    if any(app in application for app in ["Transport / Cross Docking", "Stacking/Conveyor", "Narrow Aisle"]):
        load_weight_kg = st.number_input("Load Weight [kg]", min_value=0, value=1200, step=1, key="load_weight_kg")  # integer
        if pallets and pallets[0]["pallet_type"] == "Euro" and load_weight_kg > 1500:
            st.warning("Euro pallet cannot bear more than 1500 kg. Please select 'Other' in type of pallet and specify the type and dimensions.")

    # ── Max stacking height (if relevant) ────────────────────────────────────────
    max_stacking_height_m = 3.0
    if "Stacking/Conveyor" in application or "Narrow Aisle" in application:
        max_stacking_height_m = st.number_input("Maximum Stacking Height [m]", min_value=0.0, value=3.0, step=0.1, key="max_stacking_height_m")
        if load_weight_kg <= 1200 and max_stacking_height_m > 4.5:
            st.warning("Standard max stacking height is 4.5 m for 1200 kg; special arrangements needed for up to 5.5 m.")
        elif load_weight_kg > 1200 and max_stacking_height_m > 3.5:
            st.warning("Max stacking height is 3.5 m for 1500 kg.")

    # ── Validations ──────────────────────────────────────────────────────────────
    if "Transport / Cross Docking" in application and cross_docking_aisle is not None:
        is_valid, msg, color = validate_xpl201(cross_docking_aisle, load_weight_kg)
        if color == "red":
            st.error(msg)
        elif color == "orange":
            st.warning(msg)
        else:
            st.success(msg)

    if "Stacking/Conveyor" in application:
        is_valid, msg, color = validate_xqe122(load_weight_kg, max_stacking_height_m, st.session_state.get("fork_entry_width", 320))
        if color == "red": st.error(msg)
        elif color == "orange": st.warning(msg)
        else: st.success(msg)

    if "Narrow Aisle" in application:
        is_valid, msg, color = validate_xna121_151(st.session_state.get("aisle_width_m", 1.8), load_weight_kg, max_stacking_height_m, st.session_state.get("xna_model", "XNA121 (up to 8.5m)"))
        if color == "red": st.error(msg)
        elif color == "orange": st.warning(msg)
        else: st.success(msg)

    # ── Operational Basics ───────────────────────────────────────────────────────
    st.markdown("### Operational Basics")
    col_op1, col_op2 = st.columns(2)

    with col_op1:
        peak_congestion = st.text_area("Site Peak Congestion Description", height=100, key="peak_congestion")
        max_transport_m = st.number_input("Maximum Transport Distance [m]", min_value=0.0, value=50.0, key="max_transport_m")
        pallets_per_hour = st.number_input("Pallets per Hour (peak)", min_value=0, value=50, key="pallets_per_hour")
        shifts_per_day = st.number_input("Shifts per Day", 1, 3, value=2, key="shifts_per_day")

    with col_op2:
        peak_hours = st.text_input("Operational Peak Hours", "08:00–12:00 & 14:00–18:00", key="peak_hours")
        special_layout = st.text_area("Special Layout Requirements", height=80, key="special_layout")
        network_status = st.text_area("Site Network Status / WiFi Coverage", height=80, key="network_status")

    picking_aisle_mm = st.number_input("Picking Aisle Width [mm]", min_value=0.0, value=1800.0, key="picking_aisle_mm")
    unloading_aisle_mm = st.number_input("Unloading Aisle Width [mm]", min_value=0.0, value=2900.0, key="unloading_aisle_mm")
    clearance_height_m = st.number_input("Clearance Height Under Platform / Obstacles [m]", min_value=0.0, value=5.0, key="clearance_height_m")

    # ── CAD upload ───────────────────────────────────────────────────────────────
    st.markdown("### Site Layout / CAD Upload")
    cad_file = st.file_uploader(
        "Upload CAD file, floor plan or layout drawing (DWG, PDF, PNG, JPG, etc.)",
        type=["dwg", "pdf", "png", "jpg", "jpeg", "zip"],
        help="This file will be saved with the report and referenced in the generated document.",
        key="cad_layout_file"
    )

    return {
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_mobile": customer_mobile,
        "project_name": project_name,
        "project_location": project_location,
        "survey_date": survey_date.strftime("%Y-%m-%d"),
        "application": application,
        "task_description": task_description,
        "pallets": pallets,  # list of pallet dicts
    
        "cross_docking_aisle": cross_docking_aisle,
        "fork_entry_width": st.session_state.get("fork_entry_width", 320),
        "aisle_width_m": st.session_state.get("aisle_width_m", 1.8),
        "picking_aisle_mm": picking_aisle_mm,
        "unloading_aisle_mm": unloading_aisle_mm,
        "clearance_height_m": clearance_height_m,
        "cad_file": cad_file,
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
        "peak_congestion": peak_congestion,
        "max_transport_m": max_transport_m,
        "pallets_per_hour": pallets_per_hour,
        "shifts_per_day": shifts_per_day,
        "peak_hours": peak_hours,
        "special_layout": special_layout,
        "network_status": network_status,
        "load_weight_kg": load_weight_kg,
        "max_stacking_height_m": max_stacking_height_m,
        
    }