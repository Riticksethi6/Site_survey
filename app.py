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

st.set_page_config(page_title="EP Equipment – Site Survey Dashboard", layout="wide")

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

all_data = {
    **header_data,
    **material_flow_data,
    **data_flow_data,
    **site_data,
}

selected_apps = all_data.get("application", [])

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

st.markdown("### Generate Report")
st.info(
    "By generating the report, you agree that if any changes are required in the layout, "
    "the final solution must follow the standard requirement."
)
agree = st.checkbox("I agree to the statement above", key="agree_generate_report")

if st.button("Generate Word Report & Recommendations", type="primary", disabled=not agree):
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
                return value

            for key, value in list(context.items()):
                context[key] = clean_value(value)

            pallets = context.get("pallets", [])
            if pallets:
                primary_pallet = pallets[0]
                context["pallet_type"] = primary_pallet.get("pallet_type", "")
                context["other_pallet_type"] = primary_pallet.get("other_pallet_type", "")
                context["load_dimensions"] = primary_pallet.get("load_dimensions", "")
                context["pallet_width_mm"] = primary_pallet.get("pallet_width_mm", "")
            else:
                context["pallet_type"] = ""
                context["other_pallet_type"] = ""
                context["load_dimensions"] = ""
                context["pallet_width_mm"] = ""

            cad_file = all_data.get("cad_file")
            context["cad_filename"] = cad_file.name if cad_file else ""

            if isinstance(context.get("application"), list):
                context["application"] = ", ".join(context["application"])

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
            shifts = all_data.get("shifts_per_day", 1)

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

            workers = site_data.get("whiteboard_workers", 0) + site_data.get("night_workers", 0)
            labor_savings = workers * shifts * 20000
            context["roi_hint"] = f"Potential annual labor savings: €{labor_savings:,}"

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
            docx_filename = f"site_survey_{safe_name}_{timestamp}.docx"
            zip_filename = f"site_survey_{safe_name}_{timestamp}.zip"

            status_text.text("Preparing ZIP package...")
            progress_bar.progress(75)

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(docx_filename, report_buffer.read())

                photos = material_flow_data.get("photos", [])
                for i, photo in enumerate(photos):
                    if photo:
                        ext = photo.name.split(".")[-1] if "." in photo.name else "png"
                        zip_file.writestr(f"photo_{i + 1}.{ext}", photo.getbuffer())

                conveyor_picture = all_data.get("conveyor_picture")
                if conveyor_picture:
                    ext = conveyor_picture.name.split(".")[-1] if "." in conveyor_picture.name else "png"
                    zip_file.writestr(f"conveyor_picture.{ext}", conveyor_picture.getbuffer())

                if cad_file:
                    zip_file.writestr(cad_file.name, cad_file.getbuffer())

            zip_buffer.seek(0)

            status_text.text("Done.")
            progress_bar.progress(100)

            st.success("Report generated successfully.")
            st.info("Please download the ZIP file and send it to ritick.sethi@ep-equipment.eu")

            st.download_button(
                label="Download Report ZIP",
                data=zip_buffer,
                file_name=zip_filename,
                mime="application/zip",
                key="download_report_zip"
            )

            st.subheader("Dashboard Summary")
            st.table({
                "Key Metric": [
                    "Recommended Products",
                    "Fleet Estimate",
                    "Validation Summary",
                    "ROI Hint"
                ],
                "Value": [
                    context["recommendation"],
                    context["fleet_recommendation"],
                    context["validation_summary"],
                    context["roi_hint"]
                ]
            })

        except Exception as e:
            progress_bar.progress(0)
            status_text.text("Failed.")
            st.error(f"Error during report generation: {str(e)}")