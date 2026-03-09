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
from io import BytesIO
import zipfile

# ── CONFIG ────────────────────────────────────────────────────────────────
TEMPLATE_PATH = "template.docx"
LOGO_PATH = "Picture2.png"  # relative path – file must be in repo root

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

selected_apps = all_data.get("application", [])
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

# ── PRODUCT SPECS DISPLAY + RECOMMENDED STANDARD LAYOUT ─────────────────
st.header("Product Standards & Recommended Layouts")
from products import PRODUCT_SPECS

if selected_apps:
    for app in selected_apps:
        if app == "Transport / Cross Docking":
            st.subheader("XPL201 Specs & Recommended Layout")
            st.json(PRODUCT_SPECS["XPL201"])
        elif app == "Stacking/Conveyor":
            st.subheader("XQE122 Specs & Recommended Layout")
            st.json(PRODUCT_SPECS["XQE122"])
        elif app == "Narrow Aisle":
            st.subheader("XNA Specs & Recommended Layout")
            st.json(PRODUCT_SPECS["XNA121"])
            st.json(PRODUCT_SPECS["XNA151"])

# ── REFERENCE PDFs ────────────────────────────────────────────────────────
st.header("Reference – Layout Specifications (Euro Pallets)")
col_pdf1, col_pdf2 = st.columns(2)

with col_pdf1:
    st.subheader("XQE – Stacking AMR Layout Planning")
    try:
        with open("1.10_XQE_Layout_planning_Specification.pdf", "rb") as pdf_file:
            st.download_button(
                label="Download Full XQE PDF",
                data=pdf_file,
                file_name="1.10_XQE_Layout_planning_Specification.pdf",
                mime="application/pdf"
            )
    except FileNotFoundError:
        st.error("XQE PDF not found in repo root. Upload '1.10_XQE_Layout_planning_Specification.pdf'")

with col_pdf2:
    st.subheader("XPL – Pallet Mover Layout Planning")
    try:
        with open("1.9_XPL_Layout_Planning_Specification.pdf", "rb") as pdf_file:
            st.download_button(
                label="Download Full XPL PDF",
                data=pdf_file,
                file_name="1.9_XPL_Layout_Planning_Specification.pdf",
                mime="application/pdf"
            )
    except FileNotFoundError:
        st.error("XPL PDF not found in repo root. Upload '1.9_XPL_Layout_Planning_Specification.pdf'")

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

            # ── Fix unanswered/default fields ───────────────────────────────
            defaults = {
                "aisle_width_m": 1.8,
                "general_aisle_m": 1.8,
                "picking_aisle_mm": 1800.0,
                "unloading_aisle_mm": 2900.0,
                "clearance_height_m": 5.0,
                "cross_docking_aisle": 1.8,
                "box_distance_mm": 0.0,
                "aisle_width_mm": 0.0,
                "conveyor_height": 0.0,
                "distance_from_edge": 0.0,
                "load_weight_kg": 1000.0,
                "max_stacking_height_m": 3.0,
                "max_transport_m": 50.0,
                "pallets_per_hour": 50,
                "shifts_per_day": 2,
                "fork_entry_width": 320.0,
                "ground_gaps_mm": 0.0,
                "ramp_gradient_deg": 0.0,
                "whiteboard_workers": 0,
                "night_workers": 0,
                "storage_locations": 0
            }

            for key, default_val in defaults.items():
                if context.get(key) == default_val:
                    context[key] = 'N/A'  # or '' to hide completely

            string_defaults = [
                "warehouse_area", "peak_congestion", "special_layout", "network_status", "other_agvs",
                "other_traffic", "parking_area", "charging_status", "safety_assessment", "network_coverage",
                "positioning_req", "docking_equipment", "special_demand", "storage_layout",
                "other_pallet_type", "other_pallet_dimensions"
            ]
            for key in string_defaults:
                if not context.get(key):
                    context[key] = 'N/A'

            none_defaults = ["xpl_sub_type", "pickup_type", "stacking_type", "load_at_edge", "environment", "xna_model"]
            for key in none_defaults:
                if context.get(key) is None:
                    context[key] = 'N/A'

            if context.get("battery_heating") == False:
                context["battery_heating"] = 'No'

            # ── Render Word ────────────────────────────────
            doc = DocxTemplate(TEMPLATE_PATH)
            doc.render(context)
            report_buffer = BytesIO()
            doc.save(report_buffer)
            report_buffer.seek(0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            safe_name = all_data.get("customer_name","customer").replace(" ","_")
            filename = f"site_survey_{safe_name}_{timestamp}.docx"

            # ── ZIP creation ─────────────────────────────
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                zip_file.writestr(filename, report_buffer.read())
                # Add photos
                photos = material_flow_data.get("photos", [])
                for i, photo in enumerate(photos):
                    if photo:
                        zip_file.writestr(f"photo_{i}.png", photo.getbuffer())
                # Conveyor picture
                conveyor_picture = all_data.get("conveyor_picture")
                if conveyor_picture:
                    zip_file.writestr("conveyor_picture.png", conveyor_picture.getbuffer())
                # CAD file
                cad_file = all_data.get("cad_file")
                if cad_file:
                    zip_file.writestr(cad_file.name, cad_file.getbuffer())

            zip_buffer.seek(0)
            with st.expander("📩 Next Step"):
                st.markdown(
                    "**Report generated successfully.**\n\n"
                    "Please download the report below and email it to:\n\n"
                    "**ritick.sethi@ep-equipment.eu**"
                )
                st.download_button(
                    label="⬇️ Download Report ZIP",
                    data=zip_buffer,
                    file_name=f"report_{safe_name}_{timestamp}.zip",
                    mime="application/zip"
                )
        except Exception as e:
            st.error(f"Error: {str(e)}")
            progress_bar.progress(0)