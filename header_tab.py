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

    # Pallet section
    add_multiple_pallets = st.checkbox("Add Multiple Pallets", key="add_multiple_pallets")
    pallets = []

    def build_pallet_input(i):
        st.markdown(f"#### Pallet {i}")
        pallet_type = st.radio(f"Type of Pallets {i}", ["Euro", "Industrial", "Other"], horizontal=True, key=f"pallet_type_{i}")
        other_pallet_type = ""
        if pallet_type == "Other":
            other_pallet_type = st.text_input(f"Specify pallet type {i}", key=f"other_pallet_type_{i}")

        load_dimensions = st.text_input(f"Load Dimensions (L×W×H) [mm] {i}", "1200×800×1500", key=f"load_dimensions_{i}")
        dimensions_parts = load_dimensions.split('×')
        options = []
        if len(dimensions_parts) >= 2:
            try:
                l = int(dimensions_parts[0].strip())
                w = int(dimensions_parts[1].strip())
                options = [l, w]
            except ValueError:
                pass

        pallet_width_mm = st.selectbox(f"Insertion Depth (Fork Entry) [mm] {i}", options if options else [1200], key=f"pallet_width_mm_{i}")
        return {
            "pallet_type": pallet_type,
            "other_pallet_type": other_pallet_type,
            "load_dimensions": load_dimensions,
            "pallet_width_mm": pallet_width_mm
        }

    pallets.append(build_pallet_input(1))

    if add_multiple_pallets:
        num_additional = st.number_input("Number of Additional Pallets", 1, 5, 1, key="num_additional_pallets")
        for i in range(2, num_additional + 2):
            pallets.append(build_pallet_input(i))

    # Application and task
    st.markdown("### Application(s) * (select all that apply)")
    application = st.multiselect(
        "Select all that apply",
        ["Transport / Cross Docking", "Stacking/Conveyor", "Narrow Aisle", "Other"],
        key="application"
    )
    task_description = st.text_area("Job-To-Do", height=120, key="task_description")

    # Application-specific inputs
    xpl_sub_type = None
    cross_docking_aisle = None
    if "Transport / Cross Docking" in application:
        xpl_sub_type = st.radio("Select Application Type", ["Transport", "Cross Docking"], key="xpl_sub_type")
        cross_docking_aisle = st.number_input(
            "Aisle Width in Operation Zone [m]", min_value=1.0, value=1.8, step=0.1,
            help="Recommended minimum 1.8 m", key="cross_docking_aisle"
        )

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
        st.info("Stacking / Conveyor (XQE122)")
        pickup_type = st.radio("Pickup Type", ["Ground", "Conveyor", "Other"], key="pickup_type")
        stacking_type = st.radio("Stacking Type", ["Floor Stacking", "Rack Stacking", "Other"], key="stacking_type")

        if stacking_type == "Floor Stacking":
            storage_layout = st.text_area("Storage Layout Description", height=80, key="storage_layout")
            box_distance_mm = st.number_input("Distance between boxes [mm]", min_value=0, value=200, key="box_distance_mm")
            aisle_width_mm = st.number_input("Floor Storage Aisle Width [mm]", min_value=0, value=1640, key="aisle_width_mm")

        if stacking_type == "Rack Stacking":
            box_distance_mm = st.number_input("Distance between boxes on racks [mm]", min_value=0, value=75, key="box_distance_mm")
            aisle_width_mm = st.number_input("Aisle Width for Rack Stacking [mm]", min_value=0, value=2850, key="aisle_width_mm")

        if pickup_type == "Conveyor":
            conveyor_height = st.number_input("Conveyor Height [mm]", min_value=0, value=0, key="conveyor_height")
            conveyor_picture = st.file_uploader("Upload Conveyor Picture", type=["jpg", "png", "pdf"], key="conveyor_picture")
            load_at_edge = st.radio("Does the load arrive at edge?", ["Yes", "No"], key="load_at_edge")
            if load_at_edge == "No":
                distance_from_edge = st.number_input("Distance from edge [mm]", min_value=0, value=0, key="distance_from_edge")

    # Load weight and stacking height
    load_weight_kg = st.number_input("Load Weight [kg]", min_value=0, value=1200, step=1, key="load_weight_kg")
    max_stacking_height_m = st.number_input("Maximum Stacking Height [m]", min_value=0.0, value=3.0, step=0.1, key="max_stacking_height_m")

    # Narrow aisle
    aisle_width_m = None
    xna_model = None
    if "Narrow Aisle" in application:
        st.info("Narrow Aisle (XNA121 / XNA151)")
        aisle_width_m = st.number_input("Actual Aisle Width [m]", min_value=1.5, value=1.8, step=0.1, key="aisle_width_m")
        xna_model = st.selectbox("Preferred Model", ["XNA121 (up to 8.5m)", "XNA151 (up to 13m)"], key="xna_model")

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
        "fork_entry_width": pallets[0]["pallet_width_mm"] if pallets else None,
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
        "load_weight_kg": load_weight_kg,
        "max_stacking_height_m": max_stacking_height_m
    }