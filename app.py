# app.py

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


def build_feedback_text(feedback_data: dict) -> str:
    return f"""EP Equipment Site Survey Feedback

Overall experience: {feedback_data.get('experience', '')}
Were any important questions missing?: {feedback_data.get('missing_questions', '')}
What should we improve?: {feedback_data.get('improvements', '')}
Would you like EP team to contact you?: {feedback_data.get('contact_needed', '')}
Additional comments: {feedback_data.get('comments', '')}
"""


st.set_page_config(page_title="EP Equipment – Site Survey Dashboard", layout="wide")

# ── SESSION STATE DEFAULTS ────────────────────────────────────────────────
if "report_ready" not in st.session_state:
    st.session_state["report_ready"] = False

if "generated_report_buffer" not in st.session_state:
    st.session_state["generated_report_buffer"] = None

if "generated_safe_name" not in st.session_state:
    st.session_state["generated_safe_name"] = "customer"

if "generated_timestamp" not in st.session_state:
    st.session_state["generated_timestamp"] = ""

if "generated_cad_file" not in st.session_state:
    st.session_state["generated_cad_file"] = None

if "generated_conveyor_picture" not in st.session_state:
    st.session_state["generated_conveyor_picture"] = None

if "generated_photos" not in st.session_state:
    st.session_state["generated_photos"] = []

if "generated_feedback" not in st.session_state:
    st.session_state["generated_feedback"] = None

if "feedback_saved" not in st.session_state:
    st.session_state["feedback_saved"] = False


# ── HEADER ────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=220)

with col_title:
    st.title("EP Equipment – Site Survey Dashboard")

st.markdown("Interactive tool for customer interactions: Fill forms → Get recommendations → Generate reports")

# ── TABS ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Basic Information",
    "2. Material Flow",
    "3. Data Flow & Integration",
    "4. Site Conditions & Safety"
])

with tab1:
    from header_tab import build_header_inputs
    header_data = build_header_inputs()

with tab2:
    from secondary_tab import build_material_flow_inputs
    material_flow_data = build_material_flow_inputs()

with tab3:
    from data_flow_tab import build_data_flow_inputs
    data_flow_data = build_data_flow_inputs()

with tab4:
    from site_conditions_tab import build_site_conditions_inputs
    site_data = build_site_conditions_inputs()

# ── COMBINE DATA ──────────────────────────────────────────────────────────
all_data = {
    **header_data,
    **material_flow_data,
    **data_flow_data,
    **site_data,
}

selected_apps = all_data.get("application", [])

# ── DERIVED FIELDS ────────────────────────────────────────────────────────
distances = material_flow_data.get("distances", [])
all_data["min_transport_m"] = min(distances) if distances else 0.0
all_data["avg_transport_m"] = sum(distances) / len(distances) if distances else 0.0

if all_data.get("load_dimensions") and all_data.get("max_stacking_height_m"):
    try:
        dims = str(all_data["load_dimensions"]).replace("x", "×").split("×")
        load_height_m = float(dims[-1].strip()) / 1000
        all_data["boxes_stacked"] = int(all_data["max_stacking_height_m"] / load_height_m) if load_height_m > 0 else ""
    except Exception:
        all_data["boxes_stacked"] = ""
else:
    all_data["boxes_stacked"] = ""

# ── REFERENCE PDF DOWNLOADS ───────────────────────────────────────────────
st.header("Reference – Layout Specifications")

col_pdf1, col_pdf2 = st.columns(2)

with col_pdf1:
    st.subheader("XQE – Stacking AMR Layout Planning")
    if os.path.exists(XQE_PDF):
        with open(XQE_PDF, "rb") as pdf_file:
            st.download_button(
                label="Download Full XQE PDF",
                data=pdf_file,
                file_name=XQE_PDF,
                mime="application/pdf"
            )

with col_pdf2:
    st.subheader("XPL – Pallet Mover Layout Planning")
    if os.path.exists(XPL_PDF):
        with open(XPL_PDF, "rb") as pdf_file:
            st.download_button(
                label="Download Full XPL PDF",
                data=pdf_file,
                file_name=XPL_PDF,
                mime="application/pdf"
            )

# ── AGREEMENT ─────────────────────────────────────────────────────────────
st.markdown("### Generate Report")
st.info(
    "By generating the report, you agree that if any changes are required in the layout, "
    "the final solution must follow the standard requirement."
)

agree = st.checkbox("I agree to the statement above", key="agree_generate_report")
temperature_blocked = all_data.get("temperature_range") == "Below 0°C"

# ── GENERATE REPORT ───────────────────────────────────────────────────────
if st.button(
    "Generate Report",
    type="primary",
    disabled=(not agree or temperature_blocked)
):
    required_fields = ["customer_name", "customer_email", "customer_mobile", "application"]
    missing = [field for field in required_fields if not all_data.get(field)]

    if missing:
        st.error(f"Missing required fields: {', '.join(missing)}")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("Preparing report data...")
            progress_bar.progress(10)

            context = dict(all_data)

            def clean_value(value):
                if value is None:
                    return ""
                if isinstance(value, bool):
                    return "Yes" if value else "No"
                if isinstance(value, list):
                    return ", ".join(str(v) for v in value)
                return value

            for key, value in list(context.items()):
                context[key] = clean_value(value)

            # Primary pallet for template compatibility
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

            # File names for template
            cad_file = all_data.get("cad_file")
            conveyor_picture = all_data.get("conveyor_picture")

            context["cad_filename"] = cad_file.name if cad_file else ""
            context["conveyor_picture_name"] = conveyor_picture.name if conveyor_picture else ""

            # Material flow summary
            context["route_summary"] = material_flow_data.get("route_summary", "")

            if isinstance(distances, list) and distances:
                context["distances"] = ", ".join(str(d) for d in distances)
            else:
                context["distances"] = ""

            # Pallet summary
            if isinstance(pallets, list) and pallets:
                pallet_lines = []
                for idx, pallet in enumerate(pallets, start=1):
                    pallet_label = pallet.get("pallet_type", "")
                    if pallet_label == "Other" and pallet.get("other_pallet_type"):
                        pallet_label = pallet.get("other_pallet_type")
                    pallet_lines.append(
                        f"Pallet {idx}: {pallet_label}, "
                        f"Dimensions: {pallet.get('load_dimensions', '')}, "
                        f"Insertion Depth: {pallet.get('pallet_width_mm', '')} mm"
                    )
                context["pallets_summary"] = "\n".join(pallet_lines)
            else:
                context["pallets_summary"] = ""

            status_text.text("Calculating recommendations...")
            progress_bar.progress(25)

            from product_validators import validate_xpl201, validate_xqe122, validate_xna121_151

            recommendations = []
            fleet_estimates = []
            validation_summary = []

            pallets_hr = all_data.get("pallets_per_hour", 0)
            avg_dist = all_data.get("avg_transport_m", 0)

            if "Transport / Cross Docking" in selected_apps:
                aisle = all_data.get("cross_docking_aisle", 1.8)
                weight = all_data.get("load_weight_kg", 1200)
                is_valid, msg, color = validate_xpl201(aisle, weight)
                validation_summary.append(f"XPL201 ({all_data.get('xpl_sub_type', 'N/A')}): {msg} ({color})")

                if is_valid or color == "orange":
                    speed = 1.75
                    cycle_time = (avg_dist * 2 / speed) + 30
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2))
                    recommendations.append(
                        f"XPL201 – {all_data.get('xpl_sub_type', 'Transport')} – Fast floor-level transport up to 2000 kg"
                    )
                    fleet_estimates.append(f"XPL201: ~{fleet_size} vehicles")

            if "Stacking/Conveyor" in selected_apps:
                is_valid, msg, color = validate_xqe122(
                    all_data.get("load_weight_kg", 1200),
                    all_data.get("max_stacking_height_m", 3.0),
                    320
                )
                validation_summary.append(f"XQE122: {msg} ({color})")

                if is_valid or color == "orange":
                    speed = 1.0
                    cycle_time = (avg_dist * 2 / speed) + 45
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2))
                    recommendations.append("XQE122 – Stacking / conveyor handling")
                    fleet_estimates.append(f"XQE122: ~{fleet_size} vehicles")

            if "Narrow Aisle" in selected_apps:
                model = all_data.get("xna_model", "XNA121 (up to 8.5m)")
                is_valid, msg, color = validate_xna121_151(
                    all_data.get("aisle_width_m", 1.8),
                    all_data.get("load_weight_kg", 1200),
                    all_data.get("max_stacking_height_m", 3.0),
                    model
                )
                validation_summary.append(f"{model}: {msg} ({color})")

                if is_valid or color == "orange":
                    speed = 1.0
                    cycle_time = (avg_dist * 2 / speed) + 60
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2))
                    recommendations.append(f"{model} – Narrow aisle stacking")
                    fleet_estimates.append(f"{model}: ~{fleet_size} vehicles")

            context["recommendation"] = "\n\n".join(recommendations) if recommendations else "No clear match"
            context["fleet_recommendation"] = "\n".join(fleet_estimates) if fleet_estimates else ""
            context["validation_summary"] = "\n".join(validation_summary) if validation_summary else "No validation messages"

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

            # Save in session state for feedback + final ZIP
            st.session_state["generated_report_buffer"] = report_buffer.getvalue()
            st.session_state["generated_cad_file"] = cad_file
            st.session_state["generated_conveyor_picture"] = conveyor_picture
            st.session_state["generated_photos"] = material_flow_data.get("photos", [])
            st.session_state["generated_safe_name"] = safe_name
            st.session_state["generated_timestamp"] = timestamp
            st.session_state["generated_feedback"] = None
            st.session_state["feedback_saved"] = False
            st.session_state["report_ready"] = True

            status_text.text("Report ready.")
            progress_bar.progress(100)

            st.success("Report generated successfully.")
            st.info("Please submit feedback below, then download the final ZIP.")

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
                ]
            })

        except Exception as e:
            progress_bar.progress(0)
            status_text.text("Failed.")
            st.error(f"Error during report generation: {str(e)}")

# ── FEEDBACK FORM ─────────────────────────────────────────────────────────
if st.session_state.get("report_ready"):
    st.markdown("### Help us improve")
    st.info("Please share quick feedback before downloading the final ZIP.")

    with st.form("feedback_form"):
        experience = st.selectbox(
            "Overall experience",
            ["Excellent", "Good", "Average", "Poor"]
        )

        missing_questions = st.text_area(
            "Were any important questions missing?",
            placeholder="Write any missing question or information that should be added."
        )

        improvements = st.text_area(
            "What should we improve?",
            placeholder="Tell us what can be improved in the interface or report."
        )

        contact_needed = st.radio(
            "Would you like EP team to contact you?",
            ["No", "Yes"],
            horizontal=True
        )

        comments = st.text_area(
            "Additional comments",
            placeholder="Any extra comments"
        )

        feedback_submitted = st.form_submit_button("Submit Feedback")

    if feedback_submitted:
        st.session_state["generated_feedback"] = {
            "experience": experience,
            "missing_questions": missing_questions,
            "improvements": improvements,
            "contact_needed": contact_needed,
            "comments": comments,
        }
        st.session_state["feedback_saved"] = True
        st.success("Feedback saved. Please download the final ZIP below.")

    # Final ZIP appears only after feedback submit
    if st.session_state.get("feedback_saved"):
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

        st.download_button(
            label="Download Final ZIP",
            data=final_zip_buffer,
            file_name=zip_filename,
            mime="application/zip",
            key="download_final_zip"
        )