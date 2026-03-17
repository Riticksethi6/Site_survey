import os
import math
import streamlit as st
from datetime import datetime
from product_validators import validate_xpl201, validate_xqe122, validate_xna121_151

WIFI_CHECKLIST_PDF = "4.2_Requiements for the WiFI Checklist.pdf"
WIFI_TESTING_PDF = "4.3_Wifi_Testing_Procedure.pdf"


def _parse_load_height_m(dimensions_text: str) -> float:
    if not dimensions_text:
        return 0.0
    try:
        parts = str(dimensions_text).replace("x", "×").replace("X", "×").split("×")
        if len(parts) >= 3:
            return float(parts[2].strip()) / 1000.0
    except Exception:
        return 0.0
    return 0.0


def _build_pallet_block(index: int) -> dict:
    suffix = f"_{index}"
    st.markdown(f"#### Pallet {index}")

    pallet_type = st.radio(
        f"Type of Pallet {index}",
        ["Euro", "Industrial", "Other"],
        horizontal=True,
        key=f"pallet_type{suffix}"
    )

    other_pallet_type = ""
    other_pallet_pickable = ""

    if pallet_type == "Other":
        other_pallet_type = st.text_input(
            f"Specify pallet type {index}",
            key=f"other_pallet_type{suffix}"
        )

        other_pallet_pickable = st.radio(
            f"Can '{other_pallet_type if other_pallet_type else 'this pallet'}' be picked by a normal pallet truck?",
            ["Yes", "No"],
            horizontal=True,
            key=f"other_pallet_pickable{suffix}"
        )

        if other_pallet_pickable == "No":
            st.warning(
                "Please contact our engineering team and confirm the pallet handling requirement before proceeding."
            )

    load_dimensions = st.text_input(
        f"Load Dimensions (L×W×H) [mm] {index}",
        value="",
        placeholder="Example: 1200×800×1500",
        key=f"load_dimensions{suffix}"
    )

    pallet_width_mm = st.number_input(
        f"Insertion Depth (Fork Entry) [mm] {index}",
        min_value=0,
        value=0,
        step=1,
        key=f"pallet_width_mm{suffix}"
    )

    return {
        "pallet_type": pallet_type,
        "other_pallet_type": other_pallet_type,
        "other_pallet_pickable": other_pallet_pickable,
        "load_dimensions": load_dimensions,
        "pallet_width_mm": pallet_width_mm,
    }


def build_header_inputs():
    st.subheader("1. Basic Information")

    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name *", key="customer_name")
        customer_email = st.text_input("Customer Email *", key="customer_email")
        customer_mobile = st.text_input("Customer Mobile Number *", key="customer_mobile")
        project_name = st.text_input("Project Name", key="project_name")
        project_location = st.text_input("Project Location", key="project_location")
        warehouse_area = st.text_input("Warehouse / Workshop Area [sq m]", key="warehouse_area")

    with col2:
        survey_date = st.date_input("Survey Date", datetime.today(), key="survey_date")

    add_multiple_pallets = st.checkbox("Add Multiple Pallets", key="add_multiple_pallets")

    pallets = [_build_pallet_block(1)]

    if add_multiple_pallets:
        num_additional = st.number_input(
            "Number of Additional Pallets",
            min_value=1,
            max_value=5,
            value=1,
            step=1,
            key="num_additional_pallets"
        )
        for i in range(2, num_additional + 2):
            pallets.append(_build_pallet_block(i))

    primary_pallet = pallets[0] if pallets else {
        "pallet_type": "",
        "other_pallet_type": "",
        "other_pallet_pickable": "",
        "load_dimensions": "",
        "pallet_width_mm": 0,
    }

    st.markdown("### Application(s)")
    application = st.multiselect(
        "Select all that apply",
        ["Transport / Cross Docking", "Stacking/Conveyor", "Narrow Aisle", "Other"],
        key="application"
    )

    task_description = st.text_area(
        "Job-To-Do",
        height=120,
        key="task_description",
        placeholder="Example: Inbound → Buffer Storage → Floor Storage → Production → Outbound",
        help="Describe the operation flow in a simple sequence."
    )

    st.markdown("### Application-Specific Requirements")

    load_weight_kg = 0
    max_stacking_height_m = 0.0
    stacking_level = ""

    xpl_sub_type = None
    cross_docking_aisle = None

    pickup_type = None
    pickup_type_other = ""
    stacking_type = None
    stacking_type_other = ""
    storage_layout = ""
    box_distance_mm = 0
    aisle_width_mm = 0
    conveyor_height = 0
    conveyor_picture = None
    load_at_edge = ""
    distance_from_edge = 0

    aisle_width_m = 0.0
    xna_model = None

    if any(a in application for a in ["Transport / Cross Docking", "Stacking/Conveyor", "Narrow Aisle"]):
        load_weight_kg = st.number_input(
            "Load Weight [kg]",
            min_value=0,
            value=0,
            step=1,
            key="load_weight_kg"
        )

        if primary_pallet["pallet_type"] == "Euro" and load_weight_kg > 1500:
            st.warning(
                "Euro pallet cannot bear more than 1500 kg. Please select 'Other' and specify the correct pallet type and dimensions."
            )

    if "Transport / Cross Docking" in application:
        xpl_sub_type = st.radio(
            "Select Application Type",
            ["Transport", "Cross Docking"],
            key="xpl_sub_type"
        )

        cross_docking_aisle = st.number_input(
            "Aisle Width in Operation Zone [m]",
            min_value=0.0,
            value=0.0,
            step=0.1,
            key="cross_docking_aisle"
        )

    if "Stacking/Conveyor" in application:
        st.info("Stacking / Conveyor (XQE122): maximum 5.5 m at 900 kg")

        pickup_type = st.radio(
            "Pickup Type",
            ["Ground", "Conveyor", "Other"],
            key="pickup_type"
        )

        if pickup_type == "Other":
            pickup_type_other = st.text_input(
                "Specify Other Pickup Type",
                key="pickup_type_other"
            )

        elif pickup_type == "Conveyor":
            conveyor_height = st.number_input(
                "Conveyor Height [mm]",
                min_value=0,
                value=0,
                step=1,
                key="conveyor_height"
            )

            conveyor_picture = st.file_uploader(
                "Upload Conveyor Picture",
                type=["jpg", "jpeg", "png", "pdf"],
                key="conveyor_picture"
            )

            load_at_edge = st.radio(
                "Does the pallet arrive at the edge of the conveyor?",
                ["Yes", "No"],
                key="load_at_edge"
            )

            if load_at_edge == "No":
                distance_from_edge = st.number_input(
                    "Distance Between Conveyor Edge and Pallet [mm]",
                    min_value=0,
                    value=0,
                    step=1,
                    key="distance_from_edge"
                )

        stacking_type = st.radio(
            "Stacking Type",
            ["Floor Stacking", "Rack Stacking", "Other"],
            key="stacking_type"
        )

        if stacking_type == "Other":
            stacking_type_other = st.text_input(
                "Specify Other Stacking Type",
                key="stacking_type_other"
            )

        if stacking_type == "Floor Stacking":
            storage_layout = st.text_area(
                "Storage Layout Description",
                height=80,
                key="storage_layout"
            )

            box_distance_mm = st.number_input(
                "Distance Between 2 Pallets [mm]",
                min_value=0,
                value=0,
                step=1,
                key="floor_box_distance_mm"
            )

            if box_distance_mm and box_distance_mm < 200:
                st.error("Minimum distance between 2 pallets for floor stacking is 200 mm.")

            aisle_width_mm = st.number_input(
                "Floor Storage Aisle Width [mm]",
                min_value=0,
                value=0,
                step=1,
                key="floor_aisle_width_mm"
            )

            if aisle_width_mm and aisle_width_mm < 1640:
                st.error("Minimum aisle width for floor stacking is 1640 mm.")
            elif aisle_width_mm:
                st.info("The more the available aisle space, the faster and smoother the process.")

        elif stacking_type == "Rack Stacking":
            box_distance_mm = st.number_input(
                "Distance Between Pallets Stacked in Racks [mm]",
                min_value=0,
                value=0,
                step=1,
                key="rack_box_distance_mm"
            )

            if box_distance_mm and box_distance_mm < 75:
                st.error("Minimum distance between pallets stacked in racks is 75 mm.")

            aisle_width_mm = st.number_input(
                "Rack Stacking Aisle Width (Pallet to Pallet) [mm]",
                min_value=0,
                value=0,
                step=1,
                key="rack_aisle_width_mm"
            )

            if aisle_width_mm and aisle_width_mm < 2840:
                st.error("Minimum rack stacking aisle width is 2840 mm pallet-to-pallet.")
            elif aisle_width_mm:
                st.info("The more the available aisle space, the faster the process.")

    if "Narrow Aisle" in application:
        st.info("Narrow Aisle (XNA121 / XNA151): recommended aisle width 1.78–2.0 m")

        aisle_width_m = st.number_input(
            "Actual Aisle Width [m]",
            min_value=0.0,
            value=0.0,
            step=0.1,
            key="aisle_width_m"
        )

        xna_model = st.selectbox(
            "Preferred Model",
            ["XNA121 (up to 8.5m)", "XNA151 (up to 13m)"],
            key="xna_model"
        )

    if "Stacking/Conveyor" in application or "Narrow Aisle" in application:
        max_stacking_height_m = st.number_input(
            "Maximum Stacking Height [m]",
            min_value=0.0,
            value=0.0,
            step=0.1,
            key="max_stacking_height_m"
        )

        load_height_m = _parse_load_height_m(primary_pallet["load_dimensions"])
        auto_level = ""

        if load_height_m > 0 and max_stacking_height_m > 0:
            auto_level = str(math.floor(max_stacking_height_m / load_height_m))
            st.info(
                f"Based on load height {load_height_m:.2f} m and maximum stacking height {max_stacking_height_m:.2f} m, possible stacking level is {auto_level}."
            )

        stacking_level = st.text_input(
            "Level of Stacking",
            value=auto_level,
            key="stacking_level"
        )

        if "Stacking/Conveyor" in application:
            if load_weight_kg <= 900 and max_stacking_height_m > 5.5:
                st.error("XQE maximum stacking height is 5.5 m.")
            elif load_weight_kg > 900 and max_stacking_height_m > 5.5:
                st.error("At 900 kg XQE can go up to 5.5 m. Above that load, please verify with engineering.")
            elif load_weight_kg > 900 and max_stacking_height_m > 4.5:
                st.warning("Above 900 kg, stacking height may need to be reduced. Please verify with engineering.")

    if "Transport / Cross Docking" in application and cross_docking_aisle:
        is_valid, msg, color = validate_xpl201(cross_docking_aisle, load_weight_kg)
        if color == "red":
            st.error(msg)
        elif color == "orange":
            st.warning(msg)
        else:
            st.success(msg)

    if "Stacking/Conveyor" in application and load_weight_kg and max_stacking_height_m:
        is_valid, msg, color = validate_xqe122(load_weight_kg, max_stacking_height_m, 320)
        if color == "red":
            st.error(msg)
        elif color == "orange":
            st.warning(msg)
        else:
            st.success(msg)

    if "Narrow Aisle" in application and xna_model and aisle_width_m and max_stacking_height_m:
        is_valid, msg, color = validate_xna121_151(aisle_width_m, load_weight_kg, max_stacking_height_m, xna_model)
        if color == "red":
            st.error(msg)
        elif color == "orange":
            st.warning(msg)
        else:
            st.success(msg)

    st.markdown("### Operational Basics")
    col_op1, col_op2 = st.columns(2)

    with col_op1:
        pallets_per_hour = st.number_input(
            "Pallets per Hour",
            min_value=0,
            value=0,
            step=1,
            key="pallets_per_hour"
        )

        pallets_per_day = st.number_input(
            "Pallets per Day",
            min_value=0,
            value=0,
            step=1,
            key="pallets_per_day"
        )

        shifts_per_day = st.number_input(
            "Shifts per Day",
            min_value=0,
            max_value=10,
            value=0,
            step=1,
            key="shifts_per_day"
        )

        temperature_range = st.selectbox(
            "Temperature Range (°C)",
            ["Select temperature range", "Below 0°C", "1-10°C", "10-20°C", "20-30°C", "30-40°C"],
            key="temperature_range"
        )

        if temperature_range == "Below 0°C":
            st.error("This project is not possible for temperature below 0°C."),
            st.stop()

    with col_op2:
        hours_per_shift = st.text_input(
            "Hours per Shift",
            value="",
            key="peak_hours"
        )

        special_layout = st.text_area(
            "Special Layout Requirements",
            height=100,
            key="special_layout",
            help="Mention any platform, uneven area, different aisle widths, one-way route, or special layout condition."
        )

        site_wifi_available = st.radio(
            "Is WiFi available on site?",
            ["Yes", "No"],
            horizontal=True,
            key="site_wifi_available"
        )

        if site_wifi_available == "Yes":
            st.info(
                "Please refer to the following documents to check the latency and configuration required by AGVs, and to verify whether the full zone is covered."
            )

            wifi_col1, wifi_col2 = st.columns(2)

            with wifi_col1:
                if os.path.exists(WIFI_CHECKLIST_PDF):
                    with open(WIFI_CHECKLIST_PDF, "rb") as pdf_file:
                        st.download_button(
                            "Download WiFi Checklist",
                            pdf_file,
                            WIFI_CHECKLIST_PDF,
                            "application/pdf",
                            key="download_wifi_checklist"
                        )

            with wifi_col2:
                if os.path.exists(WIFI_TESTING_PDF):
                    with open(WIFI_TESTING_PDF, "rb") as pdf_file:
                        st.download_button(
                            "Download WiFi Testing Procedure",
                            pdf_file,
                            WIFI_TESTING_PDF,
                            "application/pdf",
                            key="download_wifi_testing_procedure"
                        )

            network_status = st.text_area(
                "Site Network Status / WiFi Coverage",
                height=80,
                key="network_status"
            )
        else:
            st.warning("WiFi is not available on site.")
            st.info("Please talk to your IT team and share the WiFi checklist.")

            if os.path.exists(WIFI_CHECKLIST_PDF):
                with open(WIFI_CHECKLIST_PDF, "rb") as pdf_file:
                    st.download_button(
                        "Download WiFi Checklist",
                        pdf_file,
                        WIFI_CHECKLIST_PDF,
                        "application/pdf",
                        key="download_wifi_checklist_no_wifi"
                    )

            network_status = st.text_area(
                "Site Network Status / WiFi Coverage",
                height=80,
                key="network_status"
            )

    clearance_required = st.checkbox(
        "Is there any clearance under platform / obstacles?",
        key="clearance_required"
    )

    clearance_height_m = 0.0
    if clearance_required:
        clearance_height_m = st.number_input(
            "Clearance Height Under Platform / Obstacles [m]",
            min_value=0.0,
            value=0.0,
            step=0.1,
            key="clearance_height_m"
        )

    st.markdown("### Site Layout")
    cad_file = st.file_uploader(
        "Upload CAD file, floor plan, or layout drawing",
        type=["dwg", "nwd", "pdf", "png", "jpg", "jpeg", "zip"],
        key="cad_layout_file"
    )

    return {
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_mobile": customer_mobile,
        "project_name": project_name,
        "project_location": project_location,
        "warehouse_area": warehouse_area,
        "survey_date": survey_date.strftime("%Y-%m-%d"),
        "application": application,
        "task_description": task_description,
        "temperature_range": temperature_range,
        "pallets": pallets,
        "pallet_type": primary_pallet["pallet_type"],
        "other_pallet_type": primary_pallet["other_pallet_type"],
        "other_pallet_pickable": primary_pallet["other_pallet_pickable"],
        "load_dimensions": primary_pallet["load_dimensions"],
        "pallet_width_mm": primary_pallet["pallet_width_mm"],
        "xpl_sub_type": xpl_sub_type,
        "cross_docking_aisle": cross_docking_aisle,
        "pickup_type": pickup_type,
        "pickup_type_other": pickup_type_other,
        "stacking_type": stacking_type,
        "stacking_type_other": stacking_type_other,
        "storage_layout": storage_layout,
        "box_distance_mm": box_distance_mm,
        "aisle_width_mm": aisle_width_mm,
        "conveyor_height": conveyor_height,
        "conveyor_picture": conveyor_picture,
        "load_at_edge": load_at_edge,
        "distance_from_edge": distance_from_edge,
        "aisle_width_m": aisle_width_m,
        "xna_model": xna_model,
        "load_weight_kg": load_weight_kg,
        "max_stacking_height_m": max_stacking_height_m,
        "stacking_level": stacking_level,
        "pallets_per_hour": pallets_per_hour,
        "pallets_per_day": pallets_per_day,
        "shifts_per_day": shifts_per_day,
        "peak_hours": hours_per_shift,
        "special_layout": special_layout,
        "site_wifi_available": site_wifi_available,
        "network_status": network_status,
        "clearance_required": clearance_required,
        "clearance_height_m": clearance_height_m,
        "cad_file": cad_file,
    }