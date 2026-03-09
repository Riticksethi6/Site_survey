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

    # Pallet inputs
    add_multiple_pallets = st.checkbox("Add Multiple Pallets", key="add_multiple_pallets")
    pallets = []

    # Pallet 1
    st.markdown("#### Pallet 1")
    pallet_type_1 = st.radio("Type of Pallets", ["Euro", "Industrial", "Other"], horizontal=True, key="pallet_type_1")
    other_pallet_type_1 = ""
    if pallet_type_1 == "Other":
        other_pallet_type_1 = st.text_input("Specify pallet type", key="other_pallet_type_1")
    load_dimensions_1 = st.text_input("Load Dimensions (L×W×H) [mm]", "1200×800×1500", key="load_dimensions_1")
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

    # Additional pallets
    if add_multiple_pallets:
        num_additional = st.number_input("Number of Additional Pallets", 1, 5, value=1, key="num_additional_pallets")
        for i in range(1, num_additional + 1):
            st.markdown(f"#### Pallet {i+1}")
            pallet_type_i = st.radio(f"Type of Pallets {i+1}", ["Euro", "Industrial", "Other"], horizontal=True, key=f"pallet_type_{i+1}")
            other_pallet_type_i = ""
            if pallet_type_i == "Other":
                other_pallet_type_i = st.text_input(f"Specify pallet type {i+1}", key=f"other_pallet_type_{i+1}")
            load_dimensions_i = st.text_input(f"Load Dimensions (L×W×H) [mm] {i+1}", "1200×800×1500", key=f"load_dimensions_{i+1}")
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

    # Applications
    st.markdown("### Application(s) * (select all that apply)")
    application = st.multiselect("Select all that apply", ["Transport / Cross Docking", "Stacking/Conveyor", "Narrow Aisle", "Other"], key="application")
    task_description = st.text_area("Job-To-Do", height=120, key="task_description")

    # Application-specific
    xpl_sub_type = None
    cross_docking_aisle = None
    pickup_type = None
    stacking_type = None
    storage_layout = ""
    box_distance_mm = 0
    aisle_width_mm = 0
    conveyor_height = 0
    conveyor_picture = None
    load_at_edge = "Yes"
    distance_from_edge = 0
    fork_entry_width = st.session_state.get("fork_entry_width", 320)
    max_stacking_height_m = 3.0
    load_weight_kg = 1200

    if "Transport / Cross Docking" in application:
        xpl_sub_type = st.radio("Select Application Type", ["Transport", "Cross Docking"], key="xpl_sub_type")
        cross_docking_aisle = st.number_input("Aisle Width in Operation Zone [m]", min_value=1.0, value=1.8, step=0.1, key="cross_docking_aisle")

    if "Stacking/Conveyor" in application:
        st.info("Stacking / Conveyor (XQE122): 1200 kg up to 4.5 m, 1500 kg up to 3.5 m")
        pickup_type = st.radio("Pickup Type", ["Ground", "Conveyor", "Other"], key="pickup_type")
        stacking_type = st.radio("Stacking Type", ["Floor Stacking", "Rack Stacking", "Other"], key="stacking_type")
        if pickup_type == "Conveyor":
            conveyor_height = st.number_input("Conveyor Height [mm]", min_value=0, value=0, step=1, key="conveyor_height")
            conveyor_picture = st.file_uploader("Upload Conveyor Picture", type=["jpg", "png", "pdf"], key="conveyor_picture")
            load_at_edge = st.radio("Does the load arrive at the edge of the conveyor?", ["Yes", "No"], key="load_at_edge")
            if load_at_edge == "No":
                distance_from_edge = st.number_input("Distance from conveyor edge to pallet [mm]", min_value=0, value=0, step=1, key="distance_from_edge")

    # Load weight and max stacking height
    if any(app in application for app in ["Transport / Cross Docking", "Stacking/Conveyor", "Narrow Aisle"]):
        load_weight_kg = st.number_input("Load Weight [kg]", min_value=0, value=1200, step=1, key="load_weight_kg")
    if "Stacking/Conveyor" in application or "Narrow Aisle" in application:
        max_stacking_height_m = st.number_input("Maximum Stacking Height [m]", min_value=0.0, value=3.0, step=0.1, key="max_stacking_height_m")

    # ── Validations ──
    if "Transport / Cross Docking" in application and cross_docking_aisle is not None:
        is_valid, msg, color = validate_xpl201(cross_docking_aisle, load_weight_kg)
        if color == "red": st.error(msg)
        elif color == "orange": st.warning(msg)
        else: st.success(msg)

    if "Stacking/Conveyor" in application:
        is_valid, msg, color = validate_xqe122(load_weight_kg, max_stacking_height_m, fork_entry_width)
        if color == "red": st.error(msg)
        elif color == "orange": st.warning(msg)
        else: st.success(msg)

    if "Narrow Aisle" in application:
        xna_model = st.session_state.get("xna_model", "XNA121 (up to 8.5m)")
        is_valid, msg, color = validate_xna121_151(st.session_state.get("aisle_width_m", 1.8), load_weight_kg, max_stacking_height_m, xna_model)
        if color == "red": st.error(msg)
        elif color == "orange": st.warning(msg)
        else: st.success(msg)

    # Return all collected data
    cad_file = st.file_uploader("Upload CAD / Layout", type=["dwg","pdf","png","jpg","jpeg","zip"], key="cad_layout_file")
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
        "fork_entry_width": fork_entry_width,
        "max_stacking_height_m": max_stacking_height_m,
        "load_weight_kg": load_weight_kg,
        "pickup_type": pickup_type,
        "stacking_type": stacking_type,
        "conveyor_height": conveyor_height,
        "conveyor_picture": conveyor_picture,
        "load_at_edge": load_at_edge,
        "distance_from_edge": distance_from_edge,
        "cad_file": cad_file
    }