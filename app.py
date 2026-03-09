import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
from io import BytesIO
import zipfile
import os

# ── CONFIG ─────────────────────────────────────────────
TEMPLATE_PATH = "template.docx"
LOGO_PATH = "Picture2.png"
PROJECTS_ROOT = r"C:\Users\RitickSethi\10380 - E-P Equipment Europe\X-Mover - XP15\99 System solutions\2 Projects"
os.makedirs(PROJECTS_ROOT, exist_ok=True)

st.set_page_config(page_title="EP Site Survey Dashboard", layout="wide")

# ── HEADER ─────────────────────────────────────────────
col_logo, col_title = st.columns([1,5])
with col_logo: st.image(LOGO_PATH, width=220)
with col_title: st.title("EP Equipment – Site Survey Dashboard")
st.markdown("Interactive tool: Fill forms → Get recommendations → Generate reports")

# ── TABS ───────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Basic Information",
    "2. Material Flow",
    "3. Data Flow & Integration",
    "4. Site Conditions & Safety"
])

with tab1:
    from header_tab import build_header_inputs
    header_data = build_header_inputs()

# Assume secondary_tab, data_flow_tab, site_conditions_tab already exist
# Import them similarly
from secondary_tab import build_material_flow_inputs
material_flow_data = build_material_flow_inputs()
from data_flow_tab import build_data_flow_inputs
data_flow_data = build_data_flow_inputs()
from site_conditions_tab import build_site_conditions_inputs
site_data = build_site_conditions_inputs()

# ── COMBINE DATA ──────────────────────────────────────
all_data = {**header_data, **material_flow_data, **data_flow_data, **site_data}
selected_apps = all_data.get("application", [])

# ── DERIVED FIELDS ───────────────────────────────────
distances = material_flow_data.get("distances", [])
all_data["min_transport_m"] = min(distances) if distances else 0.0
all_data["avg_transport_m"] = sum(distances)/len(distances) if distances else 0.0

# ── GENERATE REPORT ───────────────────────────────────
if st.button("Generate Word Report & Recommendations", type="primary"):
    required_fields = ["customer_name", "customer_email", "customer_mobile", "application"]
    missing = [f for f in required_fields if not all_data.get(f)]
    if missing:
        st.error(f"Missing required fields: {', '.join(missing)}")
    else:
        try:
            from product_validators import validate_xpl201, validate_xqe122, validate_xna121_151
            context = {**all_data}

            # ── VALIDATIONS & RECOMMENDATIONS ─────────────
            validation_summary = []
            recommendations = []
            fleet_estimates = []
            pallets_hr = all_data.get("pallets_per_hour", 0)
            avg_dist = all_data.get("avg_transport_m", 0)
            shifts = all_data.get("shifts_per_day", 1)

            if "Transport / Cross Docking" in selected_apps:
                aisle = all_data.get("cross_docking_aisle",1.8)
                weight = all_data.get("load_weight_kg",1000)
                is_valid,msg,color = validate_xpl201(aisle,weight)
                validation_summary.append(f"XPL201 ({all_data.get('xpl_sub_type','N/A')}): {msg} ({color})")
                if is_valid or color=="orange":
                    speed = 1.75
                    cycle_time = (avg_dist*2/speed)+30
                    fleet_size = max(1, round((pallets_hr*cycle_time/3600)*1.2))
                    recommendations.append(f"XPL201 – {all_data.get('xpl_sub_type','Cross Docking')} – Fast transport")
                    fleet_estimates.append(f"XPL201: ~{fleet_size} vehicles")

            if "Stacking/Conveyor" in selected_apps:
                is_valid,msg,color = validate_xqe122(
                    all_data.get("load_weight_kg",1000),
                    all_data.get("max_stacking_height_m",3.0)
                )
                validation_summary.append(f"XQE122: {msg} ({color})")
                if is_valid or color=="orange":
                    recommendations.append("XQE122 – Stacking up to 5.5 m, 1200–1500 kg")

            if "Narrow Aisle" in selected_apps:
                model = all_data.get("xna_model","XNA121 (up to 8.5m)")
                is_valid,msg,color = validate_xna121_151(
                    all_data.get("aisle_width_m",1.8),
                    all_data.get("load_weight_kg",1000),
                    all_data.get("max_stacking_height_m",3.0),
                    model
                )
                validation_summary.append(f"{model}: {msg} ({color})")
                if is_valid or color=="orange":
                    recommendations.append(f"{model} – Narrow aisle stacking")

            context["recommendation"] = "\n\n".join(recommendations) or "No clear match"
            context["fleet_recommendation"] = "\n".join(fleet_estimates)
            context["validation_summary"] = "\n".join(validation_summary) or "All valid"

            # ── RENDER WORD & ZIP ──────────────────────────
            doc = DocxTemplate(TEMPLATE_PATH)
            doc.render(context)
            report_buffer = BytesIO()
            doc.save(report_buffer)
            report_buffer.seek(0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            safe_name = all_data.get("customer_name","customer").replace(" ","_")
            filename = f"site_survey_{safe_name}_{timestamp}.docx"

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer,"a",zipfile.ZIP_DEFLATED,False) as zip_file:
                zip_file.writestr(filename, report_buffer.read())
                # Photos
                for i, photo in enumerate(material_flow_data.get("photos",[])):
                    if photo: zip_file.writestr(f"photo_{i}.png", photo.getbuffer())
                # Conveyor
                conveyor_picture = all_data.get("conveyor_picture")
                if conveyor_picture: zip_file.writestr("conveyor_picture.png", conveyor_picture.getbuffer())
                # CAD
                cad_file = all_data.get("cad_file")
                if cad_file: zip_file.writestr(cad_file.name, cad_file.getbuffer())

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