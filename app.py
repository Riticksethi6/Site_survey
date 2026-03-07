# app.py – Finalized Streamlit version of EP Equipment Site Survey Tool
# Tab 5 removed – section 5 is for internal/CHN team only (filled manually in Word)
# All fields from tabs are collected and rendered in template.docx
# Conveyor picture handling added
# Transport / Cross Docking sub-type and aisle width for both
# Short description under Job to do in template
# Customer email & mobile in header

import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from datetime import datetime
import os
import shutil
from PIL import Image

# ── CONFIG ────────────────────────────────────────────────────────────────
TEMPLATE_PATH = "template.docx"
LOGO_PATH = "Picture2.png" 
XPL_PDF = r"C:\Users\RitickSethi\10380 - E-P Equipment Europe\X-Mover - XP15\99 System solutions\1 Pre Sales\Appendix-System Solutions\Site_survey\1.9_XPL_Layout_Planning_Specification.pdf"
XQE_PDF = r"C:\Users\RitickSethi\10380 - E-P Equipment Europe\X-Mover - XP15\99 System solutions\1 Pre Sales\Appendix-System Solutions\Site_survey\1.10_XQE_Layout_planning_Specification.pdf"

PROJECTS_ROOT = r"C:\Users\RitickSethi\10380 - E-P Equipment Europe\X-Mover - XP15\99 System solutions\2 Projects"
os.makedirs(PROJECTS_ROOT, exist_ok=True)

st.set_page_config(page_title="EP Site Survey Dashboard", layout="wide")

# ── HEADER ────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
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

# ── COMBINE ALL DATA ─────────────────────────────────────────────────────
all_data = {
    **header_data,
    **material_flow_data,
    **data_flow_data,
    **site_data,
}

# Compute derived fields
distances = material_flow_data.get("distances", [])
all_data["min_transport_m"] = min(distances) if distances else 0.0
all_data["avg_transport_m"] = sum(distances) / len(distances) if distances else 0.0

if 'load_dimensions' in all_data and all_data.get('max_stacking_height_m'):
    try:
        h = float(all_data['load_dimensions'].split('×')[-1]) / 1000
        all_data['boxes_stacked'] = int(all_data['max_stacking_height_m'] / h)
    except:
        all_data['boxes_stacked'] = 'N/A'

# ── PRODUCT SPECS DISPLAY ─────────────────────────────────────────────────
st.header("Product Standards & Recommendations")
from products import PRODUCT_SPECS
selected_apps = all_data.get("application", [])
for app in selected_apps:
    if app == "Transport / Cross Docking":
        st.subheader("XPL201 Specs")
        st.json(PRODUCT_SPECS["XPL201"])
    elif app == "Stacking/Conveyor":
        st.subheader("XQE122 Specs")
        st.json(PRODUCT_SPECS["XQE122"])
    elif app == "Narrow Aisle":
        st.subheader("XNA Specs")
        st.json(PRODUCT_SPECS["XNA121"])
        st.json(PRODUCT_SPECS["XNA151"])

# ── REFERENCE PDFs ────────────────────────────────────────────────────────
st.header("Reference – Layout Specifications (Euro Pallets)")

col_pdf1, col_pdf2 = st.columns(2)

with col_pdf1:
    st.subheader("XQE – Stacking AMR Layout Planning")
    if os.path.exists(XQE_PDF):
        with open(XQE_PDF, "rb") as pdf_file:
            st.download_button(
                label="Download Full XQE PDF",
                data=pdf_file,
                file_name="1.10_XQE_Layout_planning_Specification.pdf",
                mime="application/pdf"
            )

with col_pdf2:
    st.subheader("XPL – Pallet Mover Layout Planning")
    if os.path.exists(XPL_PDF):
        with open(XPL_PDF, "rb") as pdf_file:
            st.download_button(
                label="Download Full XPL PDF",
                data=pdf_file,
                file_name="1.9_XPL_Layout_Planning_Specification.pdf",
                mime="application/pdf"
            )

# ── GENERATE REPORT ───────────────────────────────────────────────────────
if st.button("Generate Word Report & Recommendations", type="primary"):
    required_fields = ["customer_name", "customer_email", "customer_mobile", "application"]
    missing = [f for f in required_fields if not all_data.get(f)]
    if missing:
        st.error(f"Missing required fields: {', '.join(missing)}")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Preparing data & recommendations...")
        progress_bar.progress(10)

        try:
            context = {**all_data}

            # Recommendation + fleet estimate
            recommendations = []
            fleet_estimates = []
            from product_validators import validate_xpl201, validate_xqe122, validate_xna121_151
            validation_summary = []
            pallets_hr = all_data.get("pallets_per_hour", 0)
            avg_dist = all_data.get("avg_transport_m", 0)
            shifts = all_data.get("shifts_per_day", 1)

            if "Transport / Cross Docking" in selected_apps:
                aisle = all_data.get("cross_docking_aisle", 1.8)
                weight = all_data.get("load_weight_kg", 1000)
                is_valid, msg, color = validate_xpl201(aisle, weight)
                validation_summary.append(f"XPL201 ({all_data.get('xpl_sub_type', 'N/A')}): {msg} ({color})")
                if is_valid or color == "orange":
                    speed = 1.75
                    cycle_time = (avg_dist * 2 / speed) + 30
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2))
                    recommendations.append(f"XPL201 – {all_data.get('xpl_sub_type', 'Cross Docking')} – Fast transport, floor-level, up to 2000 kg")
                    fleet_estimates.append(f"XPL201: ~{fleet_size} vehicles")

            if "Stacking/Conveyor" in selected_apps:
                is_valid, msg, color = validate_xqe122(
                    all_data.get("load_weight_kg", 1000),
                    all_data.get("max_stacking_height_m", 3.0),
                    all_data.get("fork_entry_width", 320)
                )
                validation_summary.append(f"XQE122: {msg} ({color})")
                if is_valid or color == "orange":
                    speed = 1.0
                    cycle_time = (avg_dist * 2 / speed) + 45
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2))
                    recommendations.append("XQE122 – Stacking up to 5.5 m, 1200–1500 kg")
                    fleet_estimates.append(f"XQE122: ~{fleet_size} vehicles")

            if "Narrow Aisle" in selected_apps:
                model = all_data.get("xna_model", "XNA121 (up to 8.5m)")
                is_valid, msg, color = validate_xna121_151(
                    all_data.get("aisle_width_m", 1.8),
                    all_data.get("load_weight_kg", 1000),
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

            context["recommendation"] = "\n\n".join(recommendations) or "No clear match"
            context["fleet_recommendation"] = "\n".join(fleet_estimates)
            context["validation_summary"] = "\n".join(validation_summary) or "All valid"

            # ROI hint
            workers = site_data.get("whiteboard_workers", 0) + site_data.get("night_workers", 0)
            labor_savings = workers * shifts * 20000
            context["roi_hint"] = f"Potential annual labor savings: €{labor_savings:,}"

            # Handle material flow photos
            photos = material_flow_data.get("photos", [])
            doc = DocxTemplate(TEMPLATE_PATH)
            for i, photo in enumerate(photos):
                if photo:
                    photo_path = os.path.join("temp", f"photo_{i}.png")
                    os.makedirs("temp", exist_ok=True)
                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())
                    img = Image.open(photo_path)
                    context[f"logistics_image{i+1}"] = InlineImage(doc, photo_path, width=img.width // 2, height=img.height // 2)

            # Handle conveyor picture if uploaded
            conveyor_picture = all_data.get("conveyor_picture")
            if conveyor_picture:
                conveyor_path = os.path.join("temp", "conveyor_picture.png")
                with open(conveyor_path, "wb") as f:
                    f.write(conveyor_picture.getbuffer())
                img = Image.open(conveyor_path)
                context["conveyor_picture"] = InlineImage(doc, conveyor_path, width=img.width // 2, height=img.height // 2)

            # CAD filename
            cad_file = all_data.get("cad_file")
            context["cad_filename"] = cad_file.name if cad_file else "No CAD file uploaded"

            doc.render(context)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = (all_data.get("customer_name", "unnamed")).replace(" ", "_").lower()
            filename = f"report_{safe_name}_{timestamp}.docx"
            output_path = os.path.join("reports", filename)
            os.makedirs("reports", exist_ok=True)
            doc.save(output_path)

            # Save to customer folder
            customer_folder_name = f"{safe_name}_{timestamp}"
            customer_folder = os.path.join(PROJECTS_ROOT, customer_folder_name)
            os.makedirs(customer_folder, exist_ok=True)
            shutil.copy(output_path, os.path.join(customer_folder, filename))

            # Copy photos
            for i, photo in enumerate(photos):
                if photo:
                    photo_path = os.path.join(customer_folder, f"photo_{i}.png")
                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())

            # Save conveyor picture
            if conveyor_picture:
                conveyor_save_path = os.path.join(customer_folder, "conveyor_picture.png")
                with open(conveyor_save_path, "wb") as f:
                    f.write(conveyor_picture.getbuffer())

            # Save CAD file
            if cad_file:
                cad_extension = cad_file.name.split('.')[-1] if '.' in cad_file.name else "file"
                cad_path = os.path.join(customer_folder, f"cad_layout.{cad_extension}")
                with open(cad_path, "wb") as f:
                    f.write(cad_file.getbuffer())
                st.info(f"CAD/layout file saved: {cad_path}")

            status_text.text("Done!")
            progress_bar.progress(100)

            st.success(f"Report generated & saved to: **{customer_folder}**")
            st.success(f"Report file: **{filename}**")

            with open(output_path, "rb") as f:
                st.download_button(
                    label="Download Generated Report",
                    data=f,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_report"
                )

            # Dashboard Summary
            st.subheader("Dashboard Summary")
            st.table({
                "Key Metric": ["Recommended Products", "Fleet Estimate", "Validation Summary", "ROI Hint"],
                "Value": [context["recommendation"], context["fleet_recommendation"], context["validation_summary"], context["roi_hint"]]
            })

        except Exception as e:
            st.error(f"Error during report generation: {str(e)}")
            progress_bar.progress(0)