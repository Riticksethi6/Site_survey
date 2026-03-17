import os
import zipfile
from io import BytesIO
from datetime import datetime

import streamlit as st
from docxtpl import DocxTemplate

TEMPLATE_PATH = "template.docx"
LOGO_PATH = "Picture2.png"
XQE_PDF = "1.10_XQE_Layout_planning_Specification.pdf"
XPL_PDF = "1.9_XPL_Layout_Planning_Specification.pdf"


APP_LABELS = {
    "Transport / Cross Docking": "XPL",
    "Stacking/Conveyor": "XQE",
    "Narrow Aisle": "XNA",
}


def build_feedback_text(feedback_data: dict) -> str:
    return f"""EP Equipment Site Survey Feedback

Overall experience: {feedback_data.get('experience', '')}
Were any important questions missing?: {feedback_data.get('missing_questions', '')}
What should we improve?: {feedback_data.get('improvements', '')}
Would you like EP team to contact you?: {feedback_data.get('contact_needed', '')}
Additional comments: {feedback_data.get('comments', '')}
"""


@st.dialog("Help us improve")
def feedback_dialog():
    st.write("Please share quick feedback before downloading the final ZIP.")

    experience = st.selectbox(
        "Overall experience",
        ["Excellent", "Good", "Average", "Poor"],
        key="feedback_experience",
    )
    missing_questions = st.text_area(
        "Were any important questions missing?",
        placeholder="Write any missing question or information that should be added.",
        key="feedback_missing_questions",
    )
    improvements = st.text_area(
        "What should we improve?",
        placeholder="Tell us what can be improved in the interface or report.",
        key="feedback_improvements",
    )
    contact_needed = st.radio(
        "Would you like EP team to contact you?",
        ["No", "Yes"],
        horizontal=True,
        key="feedback_contact_needed",
    )
    comments = st.text_area(
        "Additional comments",
        placeholder="Any extra comments",
        key="feedback_comments",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Feedback", key="submit_feedback_btn", type="primary"):
            st.session_state["generated_feedback"] = {
                "experience": experience,
                "missing_questions": missing_questions,
                "improvements": improvements,
                "contact_needed": contact_needed,
                "comments": comments,
            }
            st.session_state["feedback_saved"] = True
            st.session_state["feedback_popup_done"] = True
            st.rerun()

    with col2:
        if st.button("Skip Feedback", key="skip_feedback_btn"):
            st.session_state["generated_feedback"] = None
            st.session_state["feedback_saved"] = False
            st.session_state["feedback_popup_done"] = True
            st.rerun()


def clean_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if str(v).strip())
    return value


def parse_float(value) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value).replace(",", ".").strip())
    except (TypeError, ValueError):
        return 0.0


def add_line(lines: list[str], label: str, value, suffix: str = "") -> None:
    if value not in (None, "", [], 0, 0.0):
        lines.append(f"{label}: {value}{suffix}")


def join_lines(lines: list[str]) -> str:
    return "\n".join(line for line in lines if line not in (None, "")).strip()


st.set_page_config(page_title="EP Equipment – Site Survey Dashboard", layout="wide")

for key, default in {
    "report_ready": False,
    "generated_report_buffer": None,
    "generated_safe_name": "customer",
    "generated_timestamp": "",
    "generated_cad_file": None,
    "generated_conveyor_picture": None,
    "generated_photos": [],
    "generated_feedback": None,
    "feedback_saved": False,
    "feedback_popup_done": False,
    "feedback_popup_open": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=220)
with col_title:
    st.title("EP Equipment – Site Survey Dashboard")

st.markdown("Interactive tool for customer interactions: Fill forms → Get recommendations → Generate reports")

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Basic Information",
    "2. Material Flow",
    "3. Data Flow & Integration",
    "4. Site Conditions & Safety",
])

with tab1:
    from header_tab import build_header_inputs

    header_data = build_header_inputs()

temperature_blocked = header_data.get("temperature_range") == "Below 0°C"

with tab2:
    if temperature_blocked:
        st.warning("Project not possible: temperature below 0°C. Material flow questions are disabled.")
        material_flow_data = {
            "flow_sequence": [],
            "flow_steps": "",
            "route_details": [],
            "route_summary": "",
            "material_flow_text": "",
            "special_comments": "",
            "distances": [],
            "photos": [],
            "flow_pairs_text": "",
            "step_details_text": "",
            "process_efficiency_text": "",
            "simultaneous_pallets_per_hour": 0,
            "operational_efficiency_note": "",
        }
    else:
        from secondary_tab import build_material_flow_inputs

        material_flow_data = build_material_flow_inputs()

with tab3:
    if temperature_blocked:
        st.warning("Project not possible: temperature below 0°C. Data flow and integration questions are disabled.")
        data_flow_data = {
            "integration_req": "",
            "data_flow_text": "",
            "connections": [],
            "connections_details": "",
            "data_flow_additional_notes": "",
        }
    else:
        from data_flow_tab import build_data_flow_inputs

        data_flow_data = build_data_flow_inputs()

with tab4:
    if temperature_blocked:
        st.warning("Project not possible: temperature below 0°C. Site condition follow-up questions are disabled.")
        site_data = {
            "other_agvs": "",
            "other_traffic": "",
            "ramp_gradient_deg": "",
            "parking_area": "",
            "charging_status": "",
            "battery_heating": False,
            "network_coverage": "",
            "charging_stations": "",
            "ground_gaps_mm": "",
            "special_demand": "",
        }
    else:
        from site_conditions_tab import build_site_conditions_inputs

        site_data = build_site_conditions_inputs()

all_data = {**header_data, **material_flow_data, **data_flow_data, **site_data}
selected_apps = all_data.get("application", [])

route_distances = material_flow_data.get("distances", [])
all_data["avg_transport_m"] = round(sum(route_distances) / len(route_distances), 2) if route_distances else ""

simultaneous_pallets_per_hour = int(material_flow_data.get("simultaneous_pallets_per_hour", 0) or 0)
all_data["pallets_per_hour"] = simultaneous_pallets_per_hour or all_data.get("pallets_per_hour", 0)
hours_per_shift = parse_float(all_data.get("peak_hours"))
shifts_per_day = parse_float(all_data.get("shifts_per_day"))
computed_pallets_per_day = int(simultaneous_pallets_per_hour * hours_per_shift * shifts_per_day) if simultaneous_pallets_per_hour and hours_per_shift and shifts_per_day else 0
all_data["pallets_per_day"] = computed_pallets_per_day or all_data.get("pallets_per_day", 0)

st.header("Reference – Layout Specifications")
col_pdf1, col_pdf2 = st.columns(2)
with col_pdf1:
    st.subheader("XQE – Stacking AMR Layout Planning")
    if os.path.exists(XQE_PDF):
        with open(XQE_PDF, "rb") as pdf_file:
            st.download_button("Download Full XQE PDF", pdf_file, XQE_PDF, "application/pdf")
with col_pdf2:
    st.subheader("XPL – Pallet Mover Layout Planning")
    if os.path.exists(XPL_PDF):
        with open(XPL_PDF, "rb") as pdf_file:
            st.download_button("Download Full XPL PDF", pdf_file, XPL_PDF, "application/pdf")

st.markdown("### Generate Report")
st.info(
    "By generating the report, you agree that if any changes are required in the layout, "
    "the final solution must follow the standard requirement."
)

agree = st.checkbox("I agree to the statement above", key="agree_generate_report")
if temperature_blocked:
    st.error("This project is not possible for temperature below 0°C. No further questions can be answered and report generation is blocked.")
    st.stop()

if st.button("Generate Report", type="primary", disabled=(not agree or temperature_blocked)):
    required_fields = ["customer_name", "project_name", "project_location", "application"]
    missing = [field for field in required_fields if not all_data.get(field)]

    if missing:
        st.error(f"Missing required fields: {', '.join(missing)}")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("Preparing report data...")
            progress_bar.progress(10)

            context = {k: clean_value(v) for k, v in all_data.items()}
            pallets = all_data.get("pallets", [])

            if pallets:
                primary_pallet = pallets[0]
                context["pallet_type"] = primary_pallet.get("pallet_type", "")
                context["other_pallet_type"] = primary_pallet.get("other_pallet_type", "")
                context["other_pallet_pickable"] = primary_pallet.get("other_pallet_pickable", "")
                context["load_dimensions"] = primary_pallet.get("load_dimensions", "")
                context["pallet_width_mm"] = primary_pallet.get("pallet_width_mm", "")
            else:
                context["pallet_type"] = ""
                context["other_pallet_type"] = ""
                context["other_pallet_pickable"] = ""
                context["load_dimensions"] = ""
                context["pallet_width_mm"] = ""

            cad_file = all_data.get("cad_file")
            conveyor_picture = all_data.get("conveyor_picture")
            photos = material_flow_data.get("photos", [])

            context["cad_filename"] = cad_file.name if cad_file else ""
            context["conveyor_picture_name"] = conveyor_picture.name if conveyor_picture else ""
            context["job_to_do"] = material_flow_data.get("job_to_do_flow", all_data.get("task_description", ""))

            if not all_data.get("clearance_required"):
                context["clearance_height_m"] = ""

            aisle_lines = []
            if "Transport / Cross Docking" in selected_apps and all_data.get("cross_docking_aisle"):
                aisle_lines.append(f"XPL available aisle width: {all_data.get('cross_docking_aisle')} m")
            if "Stacking/Conveyor" in selected_apps and all_data.get("aisle_width_mm"):
                aisle_lines.append(f"XQE available aisle width: {all_data.get('aisle_width_mm')} mm")
            if "Narrow Aisle" in selected_apps and all_data.get("aisle_width_m"):
                aisle_lines.append(f"XNA available aisle width: {all_data.get('aisle_width_m')} m")
            context["aisle_width_text"] = join_lines(aisle_lines)

            load_weight_lines = []
            if all_data.get("load_weight_kg"):
                for app in selected_apps:
                    label = APP_LABELS.get(app)
                    if label:
                        load_weight_lines.append(f"{label} load weight: {all_data.get('load_weight_kg')} kg")
            context["load_weight_text"] = join_lines(load_weight_lines)

            stacking_height_lines = []
            if all_data.get("max_stacking_height_m"):
                if "Stacking/Conveyor" in selected_apps:
                    stacking_height_lines.append(f"XQE maximum stacking height: {all_data.get('max_stacking_height_m')} m")
                if "Narrow Aisle" in selected_apps:
                    stacking_height_lines.append(f"XNA maximum stacking height: {all_data.get('max_stacking_height_m')} m")
            context["stacking_height_text"] = join_lines(stacking_height_lines)

            stacking_level_lines = []
            if all_data.get("stacking_level") not in (None, "", 0):
                if "Stacking/Conveyor" in selected_apps:
                    stacking_level_lines.append(f"XQE stacking level: {all_data.get('stacking_level')}")
                if "Narrow Aisle" in selected_apps:
                    stacking_level_lines.append(f"XNA stacking level: {all_data.get('stacking_level')}")
            context["stacking_level_text"] = join_lines(stacking_level_lines)

            context["clearance_height_text"] = (
                f"Clearance height under platform / obstacles: {all_data.get('clearance_height_m')} m"
                if all_data.get("clearance_required") and all_data.get("clearance_height_m")
                else ""
            )

            storage_location_lines = []
            if "Stacking/Conveyor" in selected_apps and all_data.get("storage_locations"):
                storage_location_lines.append(f"XQE storage locations: {all_data.get('storage_locations')}")
            elif "Stacking/Conveyor" in selected_apps and all_data.get("storage_layout"):
                storage_location_lines.append(f"XQE storage layout / locations: {all_data.get('storage_layout')}")
            context["storage_locations_text"] = join_lines(storage_location_lines)

            application_lines = []
            if "Transport / Cross Docking" in selected_apps:
                application_lines.append("XPL – Transport / Cross Docking:")
                add_line(application_lines, "Application type", all_data.get("xpl_sub_type"))
                application_lines.append("")
            if "Stacking/Conveyor" in selected_apps:
                application_lines.append("XQE – Stacking / Conveyor:")
                add_line(application_lines, "Pickup type", all_data.get("pickup_type"))
                add_line(application_lines, "Pickup type (other)", all_data.get("pickup_type_other"))
                add_line(application_lines, "Stacking type", all_data.get("stacking_type"))
                add_line(application_lines, "Stacking type (other)", all_data.get("stacking_type_other"))
                add_line(application_lines, "Storage layout description", all_data.get("storage_layout"))
                add_line(application_lines, "Storage locations", all_data.get("storage_locations"))
                add_line(application_lines, "Distance between pallets / boxes", all_data.get("box_distance_mm"), " mm")
                add_line(application_lines, "Available aisle width", all_data.get("aisle_width_mm"), " mm")
                add_line(application_lines, "Conveyor height", all_data.get("conveyor_height"), " mm")
                add_line(application_lines, "Load arrives at conveyor edge", all_data.get("load_at_edge"))
                add_line(application_lines, "Distance from conveyor edge to pallet", all_data.get("distance_from_edge"), " mm")
                application_lines.append("")
            if "Narrow Aisle" in selected_apps:
                application_lines.append("XNA – Narrow Aisle:")
                add_line(application_lines, "Available aisle width", all_data.get("aisle_width_m"), " m")
                add_line(application_lines, "Preferred model", all_data.get("xna_model"))
                application_lines.append("")
            context["application_specific_text"] = join_lines(application_lines)

            summary_lines = []
            if "Transport / Cross Docking" in selected_apps:
                xpl_parts = []
                if all_data.get("xpl_sub_type"):
                    xpl_parts.append(f"Type: {all_data.get('xpl_sub_type')}")
                if all_data.get("cross_docking_aisle"):
                    xpl_parts.append(f"Aisle: {all_data.get('cross_docking_aisle')} m")
                if all_data.get("load_weight_kg"):
                    xpl_parts.append(f"Load: {all_data.get('load_weight_kg')} kg")
                if xpl_parts:
                    summary_lines.append("XPL summary: " + " | ".join(xpl_parts))
            if "Stacking/Conveyor" in selected_apps:
                xqe_parts = []
                if all_data.get("pickup_type"):
                    xqe_parts.append(f"Pickup: {all_data.get('pickup_type')}")
                if all_data.get("stacking_type"):
                    xqe_parts.append(f"Stacking: {all_data.get('stacking_type')}")
                if all_data.get("max_stacking_height_m"):
                    xqe_parts.append(f"Height: {all_data.get('max_stacking_height_m')} m")
                if all_data.get("load_weight_kg"):
                    xqe_parts.append(f"Load: {all_data.get('load_weight_kg')} kg")
                if xqe_parts:
                    summary_lines.append("XQE summary: " + " | ".join(xqe_parts))
            if "Narrow Aisle" in selected_apps:
                xna_parts = []
                if all_data.get("xna_model"):
                    xna_parts.append(f"Model: {all_data.get('xna_model')}")
                if all_data.get("aisle_width_m"):
                    xna_parts.append(f"Aisle: {all_data.get('aisle_width_m')} m")
                if all_data.get("max_stacking_height_m"):
                    xna_parts.append(f"Height: {all_data.get('max_stacking_height_m')} m")
                if all_data.get("load_weight_kg"):
                    xna_parts.append(f"Load: {all_data.get('load_weight_kg')} kg")
                if xna_parts:
                    summary_lines.append("XNA summary: " + " | ".join(xna_parts))
            context["xqe_xpl_xna_summary_text"] = join_lines(summary_lines)

            integration_support_lines = []
            if all_data.get("network_coverage"):
                integration_support_lines.append(f"Network / RF coverage details: {all_data.get('network_coverage')}")
            if all_data.get("battery_heating"):
                integration_support_lines.append("Battery heating required for low-temperature operation: Yes")
            if all_data.get("data_flow_additional_notes"):
                integration_support_lines.append(f"Additional positioning / support notes: {all_data.get('data_flow_additional_notes')}")
            context["integration_support_text"] = join_lines(integration_support_lines)

            context["ground_gaps_text"] = (
                f"Ground gaps / depressions: {all_data.get('ground_gaps_mm')} mm"
                if all_data.get("ground_gaps_mm") not in (None, "", 0, 0.0)
                else ""
            )
            context["special_demand"] = all_data.get("special_demand", "")
            context["transport_distance_text"] = material_flow_data.get("flow_pairs_text", "")
            context["material_step_details_text"] = material_flow_data.get("step_details_text", "")
            context["process_efficiency_text"] = material_flow_data.get("process_efficiency_text", "")
            context["operational_efficiency_note"] = material_flow_data.get("operational_efficiency_note", "")
            context["special_comments"] = all_data.get("special_comments", "")

            if pallets:
                pallet_lines = []
                for idx, pallet in enumerate(pallets, start=1):
                    pallet_label = pallet.get("pallet_type", "")
                    if pallet_label == "Other" and pallet.get("other_pallet_type"):
                        pallet_label = pallet.get("other_pallet_type")
                    parts = [f"Pallet {idx}: {pallet_label}"]
                    if pallet.get("load_dimensions"):
                        parts.append(f"Dimensions: {pallet.get('load_dimensions')}")
                    if pallet.get("pallet_width_mm"):
                        parts.append(f"Insertion Depth: {pallet.get('pallet_width_mm')} mm")
                    if pallet.get("other_pallet_pickable"):
                        parts.append(f"Can be picked by normal pallet truck: {pallet.get('other_pallet_pickable')}")
                    pallet_lines.append(", ".join(parts))
                context["pallets_summary"] = "\n".join(pallet_lines)
            else:
                context["pallets_summary"] = ""

            status_text.text("Calculating recommendations...")
            progress_bar.progress(25)

            from product_validators import validate_xpl201, validate_xqe122, validate_xna121_151

            recommendations = []
            fleet_estimates = []
            validation_summary = []

            pallets_hr = parse_float(all_data.get("pallets_per_hour"))
            avg_dist = parse_float(all_data.get("avg_transport_m"))

            if "Transport / Cross Docking" in selected_apps and all_data.get("cross_docking_aisle"):
                aisle = parse_float(all_data.get("cross_docking_aisle"))
                weight = parse_float(all_data.get("load_weight_kg"))
                is_valid, msg, color = validate_xpl201(aisle, weight)
                validation_summary.append(f"XPL201 ({all_data.get('xpl_sub_type', 'N/A')}): {msg} ({color})")
                if is_valid or color == "orange":
                    speed = 1.75
                    cycle_time = (avg_dist * 2 / speed) + 30 if avg_dist else 30
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2)) if pallets_hr else 1
                    recommendations.append(f"XPL201 – {all_data.get('xpl_sub_type', 'Transport')} – Fast floor-level transport up to 2000 kg")
                    fleet_estimates.append(f"XPL201: ~{fleet_size} vehicles")

            if "Stacking/Conveyor" in selected_apps and all_data.get("load_weight_kg") and all_data.get("max_stacking_height_m"):
                is_valid, msg, color = validate_xqe122(
                    parse_float(all_data.get("load_weight_kg")),
                    parse_float(all_data.get("max_stacking_height_m")),
                    320,
                )
                validation_summary.append(f"XQE122: {msg} ({color})")
                if is_valid or color == "orange":
                    speed = 1.0
                    cycle_time = (avg_dist * 2 / speed) + 45 if avg_dist else 45
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2)) if pallets_hr else 1
                    recommendations.append("XQE122 – Stacking / conveyor handling")
                    fleet_estimates.append(f"XQE122: ~{fleet_size} vehicles")

            if "Narrow Aisle" in selected_apps and all_data.get("aisle_width_m") and all_data.get("xna_model"):
                model = all_data.get("xna_model", "XNA121 (up to 8.5m)")
                is_valid, msg, color = validate_xna121_151(
                    parse_float(all_data.get("aisle_width_m")),
                    parse_float(all_data.get("load_weight_kg")),
                    parse_float(all_data.get("max_stacking_height_m")),
                    model,
                )
                validation_summary.append(f"{model}: {msg} ({color})")
                if is_valid or color == "orange":
                    speed = 1.0
                    cycle_time = (avg_dist * 2 / speed) + 60 if avg_dist else 60
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2)) if pallets_hr else 1
                    recommendations.append(f"{model} – Narrow aisle stacking")
                    fleet_estimates.append(f"{model}: ~{fleet_size} vehicles")

            context["recommendation"] = "\n\n".join(recommendations) if recommendations else ""
            context["fleet_recommendation"] = "\n".join(fleet_estimates) if fleet_estimates else ""
            context["validation_summary"] = "\n".join(validation_summary) if validation_summary else ""

            status_text.text("Generating Word report...")
            progress_bar.progress(50)

            if not os.path.exists(TEMPLATE_PATH):
                raise FileNotFoundError(f"Template file not found: {TEMPLATE_PATH}")

            doc = DocxTemplate(TEMPLATE_PATH)
            doc.render(context)

            report_buffer = BytesIO()
            doc.save(report_buffer)
            report_buffer.seek(0)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = all_data.get("customer_name", "customer").strip().replace(" ", "_").lower()

            st.session_state["generated_report_buffer"] = report_buffer.getvalue()
            st.session_state["generated_cad_file"] = cad_file
            st.session_state["generated_conveyor_picture"] = conveyor_picture
            st.session_state["generated_photos"] = photos
            st.session_state["generated_safe_name"] = safe_name
            st.session_state["generated_timestamp"] = timestamp
            st.session_state["generated_feedback"] = None
            st.session_state["feedback_saved"] = False
            st.session_state["feedback_popup_done"] = False
            st.session_state["feedback_popup_open"] = True
            st.session_state["report_ready"] = True

            status_text.text("Report ready.")
            progress_bar.progress(100)
            st.success("Report generated successfully.")

            st.subheader("Dashboard Summary")
            st.table({
                "Key Metric": [
                    "Recommended Products",
                    "Fleet Estimate",
                    "Validation Summary",
                ],
                "Value": [
                    context["recommendation"],
                    context["fleet_recommendation"],
                    context["validation_summary"],
                ],
            })

        except Exception as e:
            progress_bar.progress(0)
            status_text.text("Failed.")
            st.error(f"Error during report generation: {str(e)}")

if st.session_state.get("report_ready") and st.session_state.get("feedback_popup_open"):
    st.session_state["feedback_popup_open"] = False
    feedback_dialog()

if st.session_state.get("report_ready") and st.session_state.get("feedback_popup_done"):
    report_bytes = st.session_state.get("generated_report_buffer")
    cad_file = st.session_state.get("generated_cad_file")
    conveyor_picture = st.session_state.get("generated_conveyor_picture")
    photos = st.session_state.get("generated_photos", [])
    safe_name = st.session_state.get("generated_safe_name", "customer")
    timestamp = st.session_state.get("generated_timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
    feedback_data = st.session_state.get("generated_feedback")

    final_zip_buffer = BytesIO()
    docx_filename = f"site_survey_{safe_name}_{timestamp}.docx"
    zip_filename = f"site_survey_{safe_name}_{timestamp}.zip"

    with zipfile.ZipFile(final_zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        if report_bytes:
            zip_file.writestr(docx_filename, report_bytes)

        for i, photo in enumerate(photos):
            if photo:
                ext = photo.name.split(".")[-1] if "." in photo.name else "png"
                zip_file.writestr(f"material_flow_photo_{i + 1}.{ext}", photo.getbuffer())

        if conveyor_picture:
            ext = conveyor_picture.name.split(".")[-1] if "." in conveyor_picture.name else "png"
            zip_file.writestr(f"conveyor_picture.{ext}", conveyor_picture.getbuffer())

        if cad_file:
            zip_file.writestr(cad_file.name, cad_file.getbuffer())

        if feedback_data:
            zip_file.writestr("feedback.txt", build_feedback_text(feedback_data))

    final_zip_buffer.seek(0)

    if feedback_data:
        st.success("Feedback saved. Download the final ZIP below.")
    else:
        st.info("Feedback skipped. Download the final ZIP below.")

    st.download_button(
        label="Download Final ZIP",
        data=final_zip_buffer,
        file_name=zip_filename,
        mime="application/zip",
        key="download_final_zip",
    )
