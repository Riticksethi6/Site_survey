import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from datetime import datetime
from io import BytesIO
import zipfile
import os
from pathlib import Path

TEMPLATE_PATH = "template.docx"
LOGO_PATH = "Picture2.png"
PROJECTS_ROOT = Path("projects")
PROJECTS_ROOT.mkdir(exist_ok=True)

st.set_page_config(page_title="EP Site Survey Dashboard", layout="wide")

# Header
col_logo, col_title = st.columns([1,5])
with col_logo:
    st.image(LOGO_PATH, width=220)
with col_title:
    st.title("EP Equipment – Site Survey Dashboard")
st.markdown("Interactive tool: Fill forms → Generate reports → Email/Download")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Basic Information",
    "2. Material Flow",
    "3. Data Flow & Integration",
    "4. Site Conditions & Safety"
])

with tab1:
    from header_tab import build_header_inputs
    header_data = build_header_inputs()

# Placeholder for other tabs
material_flow_data = {}
data_flow_data = {}
site_data = {}

# Combine all
all_data = {**header_data, **material_flow_data, **data_flow_data, **site_data}

# Derived fields
if 'pallets' in all_data and all_data['pallets']:
    first_pallet = all_data['pallets'][0]
    all_data['pallet_type'] = first_pallet.get('pallet_type')
    all_data['pallet_width_mm'] = first_pallet.get('pallet_width_mm')
    all_data['other_pallet_type'] = first_pallet.get('other_pallet_type')
    all_data['load_dimensions'] = first_pallet.get('load_dimensions')

# Generate report
if st.button("Generate Word Report & Recommendations"):
    # Folder for project
    safe_name = all_data.get("customer_name", "project").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    project_folder = PROJECTS_ROOT / f"{safe_name}_{timestamp}"
    project_folder.mkdir(exist_ok=True)

    # Render Word
    doc = DocxTemplate(TEMPLATE_PATH)
    context = all_data.copy()

    # Save CAD and images in folder
    cad_file = all_data.get("cad_file")
    if cad_file:
        cad_path = project_folder / cad_file.name
        with open(cad_path, "wb") as f:
            f.write(cad_file.getbuffer())
        context["cad_filename"] = cad_file.name

    conveyor_picture = all_data.get("conveyor_picture")
    if conveyor_picture:
        img_path = project_folder / "conveyor_picture.png"
        with open(img_path, "wb") as f:
            f.write(conveyor_picture.getbuffer())

    doc.render(context)
    report_path = project_folder / f"{safe_name}_{timestamp}.docx"
    doc.save(report_path)

    # Zip all contents
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in project_folder.iterdir():
            zip_file.write(file, arcname=file.name)
    zip_buffer.seek(0)

    # Show popup and download
    st.success("Report generated successfully. Please download and email it to ritick.sethi@ep-equipment.eu")
    st.download_button(
        label="⬇️ Download Project ZIP",
        data=zip_buffer,
        file_name=f"{safe_name}_{timestamp}.zip",
        mime="application/zip"
    )