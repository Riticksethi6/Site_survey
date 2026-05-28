import os
import zipfile
import base64
from io import BytesIO
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from docxtpl import DocxTemplate

TEMPLATE_PATH = "template.docx"
LOGO_PATH = "Picture2.png"

XQE_PDF_CANDIDATES = [
    "1.10_XQE_Layout_planning_Specification.pdf",
    "1.10_XQE_Layout_Planning_Specification.pdf",
]

XPL_PDF_CANDIDATES = [
    "1.9_XPL_Layout_planning_Specification.pdf",
    "1.9_XPL_Layout_Planning_Specification.pdf",
]


def find_existing_file(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def build_feedback_text(feedback_data: dict) -> str:
    return f'''EP Equipment Site Survey Feedback

Overall experience: {feedback_data.get("experience", "")}
Were any important questions missing?: {feedback_data.get("missing_questions", "")}
What should we improve?: {feedback_data.get("improvements", "")}
Would you like EP team to contact you?: {feedback_data.get("contact_needed", "")}
Additional comments: {feedback_data.get("comments", "")}
'''


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


@st.dialog("ZIP download started")
def zip_download_popup():
    st.success("Your ZIP download has started automatically.")
    st.info("Please email this ZIP to: ritick.sethi@ep-equipment.eu")
    st.write("If the browser blocks the automatic download, use the fallback download button below.")


def trigger_auto_download(file_bytes: bytes, filename: str, mime: str = "application/zip"):
    b64 = base64.b64encode(file_bytes).decode()
    components.html(
        f"""
        <html>
          <body>
            <a id="auto-download-link" download="{filename}" href="data:{mime};base64,{b64}"></a>
            <script>
              const link = document.getElementById("auto-download-link");
              if (link) {{
                link.click();
              }}
            </script>
          </body>
        </html>
        """,
        height=0,
    )


def clean_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if str(v).strip())
    return value


def _format_number(value):
    if value in (None, ""):
        return ""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.2f}".rstrip("0").rstrip(".")


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_operational_metrics(route_details):
    process_lines = []
    notes = []
    simultaneous_total = 0.0

    for route in route_details or []:
        from_step = route.get("from", "")
        to_step = route.get("to", "")
        capacity = _to_float(route.get("pallets_per_hour"))
        flow_type = route.get("flow_type", "Simultaneous / continuous")

        if not (from_step and to_step):
            continue

        if flow_type == "No - not handled by EP automation":
            line = f"{from_step} → {to_step}: outside EP automation scope"
        else:
            line = f"{from_step} → {to_step}: {_format_number(capacity)} pallets/hour"
            if flow_type == "On request / intermittent":
                line += " (on request)"
            else:
                simultaneous_total += capacity

        process_lines.append(line)

    if any(route.get("flow_type") == "On request / intermittent" for route in (route_details or [])):
        notes.append("Some routes are triggered only on request.")
    if any(route.get("flow_type") == "No - not handled by EP automation" for route in (route_details or [])):
        notes.append("Routes outside EP automation scope are excluded from EP throughput and fleet calculations.")

    return {
        "pallets_per_hour": "\n".join(process_lines),
        "pallets_per_hour_total": simultaneous_total,
        "pallets_per_day": "",
        "operational_efficiency_note": "\n".join(notes),
    }


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
    "auto_zip_download_done": False,
    "zip_popup_open": False,
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

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "1. Basic Information",
        "2. Material Flow",
        "3. Data Flow & Integration",
        "4. Site Conditions & Safety",
    ]
)

with tab1:
    from header_tab import build_header_inputs
    header_data = build_header_inputs()

with tab2:
    from secondary_tab import build_material_flow_inputs
    material_flow_data = build_material_flow_inputs()

with tab3:
    from data_flow_tab import build_data_flow_inputs
    data_flow_data = build_data_flow_inputs(
        route_details=material_flow_data.get("route_details", []),
        selected_apps=header_data.get("application", []),
    )

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
route_details = material_flow_data.get("route_details", [])
distances = [
    _to_float(route.get("avg_distance_m"))
    for route in route_details
    if _to_float(route.get("avg_distance_m")) > 0
]
all_data["avg_transport_m"] = round(sum(distances) / len(distances), 2) if distances else ""

st.header("Reference – Layout Specifications")

col_pdf1, col_pdf2 = st.columns(2)

xqe_pdf_path = find_existing_file(XQE_PDF_CANDIDATES)
xpl_pdf_path = find_existing_file(XPL_PDF_CANDIDATES)

with col_pdf1:
    st.subheader("XQE – Stacking AMR Layout Planning")
    if xqe_pdf_path:
        with open(xqe_pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download Full XQE PDF",
                data=pdf_file,
                file_name=os.path.basename(xqe_pdf_path),
                mime="application/pdf",
            )
    else:
        st.warning("XQE PDF file not found in app folder.")

with col_pdf2:
    st.subheader("XPL – Pallet Mover Layout Planning")
    if xpl_pdf_path:
        with open(xpl_pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download Full XPL PDF",
                data=pdf_file,
                file_name=os.path.basename(xpl_pdf_path),
                mime="application/pdf",
            )
    else:
        st.warning("XPL PDF file not found in app folder.")

st.markdown("### Generate Report")
st.info(
    "By generating the report, you agree that if any changes are required in the layout, "
    "the final solution must follow the standard requirement."
)

agree = st.checkbox("I agree to the statement above", key="agree_generate_report")
temperature_blocked = all_data.get("temperature_range") == "Below 0°C"

if st.button("Generate Report", type="primary", disabled=(not agree or temperature_blocked)):
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

            context = {k: clean_value(v) for k, v in all_data.items()}

            operational_metrics = _build_operational_metrics(route_details)
            context["pallets_per_hour"] = operational_metrics["pallets_per_hour"]
            context["pallets_per_day"] = operational_metrics["pallets_per_day"]
            context["pallets_per_hour_total"] = operational_metrics["pallets_per_hour_total"]
            context["operational_efficiency_note"] = operational_metrics["operational_efficiency_note"]

            pallets = all_data.get("pallets", [])
            if pallets:
                primary_pallet = pallets[0]
                context["pallet_type"] = primary_pallet.get("pallet_type", "")
                context["other_pallet_type"] = primary_pallet.get("other_pallet_type", "")
                context["other_pallet_pickable"] = primary_pallet.get("other_pallet_pickable", "")
                context["load_dimensions"] = primary_pallet.get("load_dimensions", "")
                raw_width = primary_pallet.get("pallet_width_mm", 0)
                context["pallet_width_mm"] = raw_width if raw_width else ""
            else:
                primary_pallet = {}
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
            job_to_do_val = material_flow_data.get("job_to_do_flow") or all_data.get("task_description", "")
            context["job_to_do"] = job_to_do_val

            if not all_data.get("clearance_required"):
                context["clearance_height_m"] = ""

            def add_line(lines, label, value, suffix=""):
                if value not in (None, "", [], 0, 0.0):
                    lines.append(f"{label}: {value}{suffix}")

            aisle_lines = []
            if "Transport / Cross Docking" in selected_apps and all_data.get("cross_docking_aisle"):
                aisle_lines.append(f"XPL available aisle width: {all_data.get('cross_docking_aisle')} m")
            if "Stacking/Conveyor" in selected_apps and all_data.get("aisle_width_mm"):
                aisle_lines.append(f"XQE available aisle width: {all_data.get('aisle_width_mm')} mm")
            if "Narrow Aisle" in selected_apps and all_data.get("aisle_width_m"):
                aisle_lines.append(f"XNA available aisle width: {all_data.get('aisle_width_m')} m")
            context["aisle_width_text"] = "\n".join(aisle_lines)

            load_weight_lines = []
            if all_data.get("load_weight_kg"):
                if "Transport / Cross Docking" in selected_apps:
                    load_weight_lines.append(f"XPL load weight: {all_data.get('load_weight_kg')} kg")
                if "Stacking/Conveyor" in selected_apps:
                    load_weight_lines.append(f"XQE load weight: {all_data.get('load_weight_kg')} kg")
                if "Narrow Aisle" in selected_apps:
                    load_weight_lines.append(f"XNA load weight: {all_data.get('load_weight_kg')} kg")
            context["load_weight_text"] = "\n".join(load_weight_lines)

            stacking_height_lines = []
            if all_data.get("max_stacking_height_m"):
                if "Stacking/Conveyor" in selected_apps:
                    stacking_height_lines.append(f"XQE maximum stacking height: {all_data.get('max_stacking_height_m')} m")
                if "Narrow Aisle" in selected_apps:
                    stacking_height_lines.append(f"XNA maximum stacking height: {all_data.get('max_stacking_height_m')} m")
            context["stacking_height_text"] = "\n".join(stacking_height_lines)

            stacking_level_lines = []
            if all_data.get("stacking_level") not in (None, "", 0):
                if "Stacking/Conveyor" in selected_apps:
                    stacking_level_lines.append(f"XQE stacking level: {all_data.get('stacking_level')}")
                if "Narrow Aisle" in selected_apps:
                    stacking_level_lines.append(f"XNA stacking level: {all_data.get('stacking_level')}")
            context["stacking_level_text"] = "\n".join(stacking_level_lines)

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
            context["storage_locations_text"] = "\n".join(storage_location_lines)

            application_lines = []

            if "Transport / Cross Docking" in selected_apps:
                application_lines.append("XPL - Transport / Cross Docking:")
                add_line(application_lines, "Application type", all_data.get("xpl_sub_type"))

            if "Stacking/Conveyor" in selected_apps:
                application_lines.append("")
                application_lines.append("XQE - Stacking / Conveyor:")
                add_line(application_lines, "Pickup type", all_data.get("pickup_type"))
                add_line(application_lines, "Pickup type (other)", all_data.get("pickup_type_other"))
                add_line(application_lines, "Stacking type", all_data.get("stacking_type"))
                add_line(application_lines, "Stacking type (other)", all_data.get("stacking_type_other"))
                add_line(application_lines, "Storage layout description", all_data.get("storage_layout"))
                add_line(application_lines, "Storage locations", all_data.get("storage_locations"))

            if "Narrow Aisle" in selected_apps:
                application_lines.append("")
                application_lines.append("XNA - Narrow Aisle:")
                add_line(application_lines, "Preferred model", all_data.get("xna_model"))

            context["application_specific_text"] = "\n".join([line for line in application_lines if line is not None]).strip()

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

            context["xqe_xpl_xna_summary_text"] = "\n".join(summary_lines)

            integration_support_lines = []
            if all_data.get("data_flow_additional_notes"):
                integration_support_lines.append(f"Additional integration / positioning notes: {all_data.get('data_flow_additional_notes')}")
            context["integration_support_text"] = "\n".join(integration_support_lines)

            context["ground_gaps_text"] = (
                f"Ground gaps / depressions: {all_data.get('ground_gaps_mm')} mm"
                if all_data.get("ground_gaps_mm") not in (None, "", 0, 0.0)
                else ""
            )
            context["special_demand"] = all_data.get("special_demand", "")
            context["transport_distance_text"] = material_flow_data.get("flow_pairs_text", "")
            context["material_step_details_text"] = material_flow_data.get("step_details_text", "")
            context["special_comments"] = all_data.get("special_comments", "")

            context["system_architecture_text"] = all_data.get("system_architecture_text", "")
            context["integration_route_text"] = all_data.get("integration_route_text", "")
            context["data_flow_diagram_text"] = all_data.get("data_flow_diagram_text", "")
            context["task_flow_text"] = all_data.get("task_flow_text", "")
            context["connected_systems_text"] = all_data.get("connected_systems_text", "")
            context["status_feedback_text"] = all_data.get("status_feedback_text", "")
            context["key_data_exchange_text"] = all_data.get("key_data_exchange_text", "")

            # ── pallets_summary ──────────────────────────────────────────
            if pallets:
                pallet_lines = []
                for idx, pallet in enumerate(pallets, start=1):
                    pallet_label = pallet.get("pallet_type", "")
                    if pallet_label == "Other" and pallet.get("other_pallet_type"):
                        pallet_label = pallet.get("other_pallet_type")
                    parts = [f"Pallet {idx}: {pallet_label}"]
                    if pallet.get("load_dimensions"):
                        parts.append(f"Dimensions: {pallet.get('load_dimensions')}")
                    raw_w = pallet.get("pallet_width_mm", 0)
                    if raw_w:
                        parts.append(f"Fork entry depth: {raw_w} mm")
                    if pallet.get("other_pallet_pickable"):
                        parts.append(f"Can be picked by normal pallet truck: {pallet.get('other_pallet_pickable')}")
                    pallet_lines.append(", ".join(parts))
                context["pallets_summary"] = "\n".join(pallet_lines)
            else:
                context["pallets_summary"] = ""

            # ── pallet_display_text (single smart field for report cell) ──
            pallet_lines_disp = []
            ptype = primary_pallet.get("pallet_type", "")
            if ptype:
                pallet_lines_disp.append(f"Pallet type: {ptype}")
            if ptype == "Other":
                if primary_pallet.get("other_pallet_type"):
                    pallet_lines_disp.append(f"Type description: {primary_pallet.get('other_pallet_type')}")
                if primary_pallet.get("other_pallet_pickable"):
                    pallet_lines_disp.append(f"Can be picked by normal pallet truck: {primary_pallet.get('other_pallet_pickable')}")
            if primary_pallet.get("load_dimensions"):
                pallet_lines_disp.append(f"Dimensions (L×W×H): {primary_pallet.get('load_dimensions')}")
            raw_w = primary_pallet.get("pallet_width_mm", 0)
            if raw_w:
                pallet_lines_disp.append(f"Fork entry depth: {raw_w} mm")
            if len(pallets) > 1:
                pallet_lines_disp.append(f"All pallets:\n{context['pallets_summary']}")
            context["pallet_display_text"] = "\n".join(pallet_lines_disp)

            # ── wifi_info_text ────────────────────────────────────────────
            wifi_lines = []
            if all_data.get("site_wifi_available"):
                wifi_lines.append(f"Wi-Fi available: {all_data.get('site_wifi_available')}")
            if all_data.get("network_status"):
                wifi_lines.append(f"Network status: {all_data.get('network_status')}")
            if all_data.get("network_coverage"):
                wifi_lines.append(f"Coverage details: {all_data.get('network_coverage')}")
            context["wifi_info_text"] = "\n".join(wifi_lines)

            # ── avg_transport_text ────────────────────────────────────────
            avg_t = context.get("avg_transport_m", "")
            context["avg_transport_text"] = f"{avg_t} m" if avg_t not in (None, "", 0, 0.0) else ""

            # ── operational_text ──────────────────────────────────────────
            op_lines = []
            if all_data.get("shifts_per_day") not in (None, 0, ""):
                op_lines.append(f"Shifts per day: {all_data.get('shifts_per_day')}")
            if all_data.get("peak_hours") not in (None, 0, 0.0, ""):
                op_lines.append(f"Hours per shift: {all_data.get('peak_hours')}")
            if operational_metrics["pallets_per_hour"]:
                op_lines.append(f"Pallets per hour:\n{operational_metrics['pallets_per_hour']}")
            context["operational_text"] = "\n".join(op_lines)

            # ── material_flow_display_text ────────────────────────────────
            mf_lines = []
            if all_data.get("flow_steps") or material_flow_data.get("flow_steps"):
                mf_lines.append(f"Flow sequence: {material_flow_data.get('flow_steps', '')}")
            if material_flow_data.get("step_details_text"):
                mf_lines.append(f"Step details:\n{material_flow_data.get('step_details_text')}")
            if material_flow_data.get("material_flow_text"):
                mf_lines.append(f"Process description:\n{material_flow_data.get('material_flow_text')}")
            if all_data.get("special_comments"):
                mf_lines.append(f"Notes:\n{all_data.get('special_comments')}")
            context["material_flow_display_text"] = "\n".join(mf_lines)

            # ── cad_info_text ─────────────────────────────────────────────
            cad_lines = []
            if cad_file:
                cad_lines.append(f"CAD / layout file attached: {cad_file.name}")
            if conveyor_picture:
                cad_lines.append(f"Conveyor picture attached: {conveyor_picture.name}")
            context["cad_info_text"] = "\n".join(cad_lines)

            # ── charging_parking_text ─────────────────────────────────────
            cp_lines = []
            if all_data.get("charging_status"):
                cp_lines.append(f"Charging area: {all_data.get('charging_status')}")
            if all_data.get("parking_area"):
                cp_lines.append(f"Parking / rest area: {all_data.get('parking_area')}")
            context["charging_parking_text"] = "\n".join(cp_lines)

            # ── special_info_text ─────────────────────────────────────────
            si_lines = []
            if all_data.get("special_demand"):
                si_lines.append(all_data.get("special_demand"))
            if all_data.get("special_comments"):
                si_lines.append(f"Additional notes: {all_data.get('special_comments')}")
            context["special_info_text"] = "\n".join(si_lines)

            # ── job_to_do_text ────────────────────────────────────────────
            jd_lines = []
            if selected_apps:
                jd_lines.append(f"Application(s): {', '.join(selected_apps)}")
            if job_to_do_val:
                jd_lines.append(f"Job-To-Do: {job_to_do_val}")
            context["job_to_do_text"] = "\n".join(jd_lines)

            # ── data_flow_display_text ────────────────────────────────────
            if all_data.get("integration_required") == "Yes":
                df_lines = []
                if all_data.get("system_architecture_text"):
                    df_lines.append(f"System architecture:\n{all_data.get('system_architecture_text')}")
                if all_data.get("integration_route_text"):
                    df_lines.append(f"Integration route: {all_data.get('integration_route_text')}")
                if all_data.get("task_flow_text"):
                    df_lines.append(f"Task flow:\n{all_data.get('task_flow_text')}")
                if all_data.get("connected_systems_text"):
                    df_lines.append(f"Connected systems:\n{all_data.get('connected_systems_text')}")
                if all_data.get("status_feedback_text"):
                    df_lines.append(f"Status feedback:\n{all_data.get('status_feedback_text')}")
                if all_data.get("key_data_exchange_text"):
                    df_lines.append(f"Key data exchanged:\n{all_data.get('key_data_exchange_text')}")
                if all_data.get("connections_details"):
                    df_lines.append(all_data.get("connections_details"))
                context["data_flow_display_text"] = "\n\n".join(df_lines)
            else:
                context["data_flow_display_text"] = "No external system integration required."

            status_text.text("Calculating recommendations...")
            progress_bar.progress(25)

            from product_validators import validate_xpl201, validate_xqe122, validate_xna121_151

            recommendations = []
            fleet_estimates = []
            validation_summary = []

            pallets_hr = _to_float(context.get("pallets_per_hour_total"))
            avg_dist = _to_float(all_data.get("avg_transport_m"))

            if "Transport / Cross Docking" in selected_apps and all_data.get("cross_docking_aisle"):
                aisle = all_data.get("cross_docking_aisle", 0)
                weight = all_data.get("load_weight_kg", 0)
                is_valid, msg, color = validate_xpl201(aisle, weight)
                validation_summary.append(f"XPL201 ({all_data.get('xpl_sub_type', 'N/A')}): {msg} ({color})")
                if is_valid or color == "orange":
                    speed = 1.75
                    cycle_time = (avg_dist * 2 / speed) + 30 if avg_dist else 30
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2)) if pallets_hr else 1
                    recommendations.append(f"XPL201 - {all_data.get('xpl_sub_type', 'Transport')} - Fast floor-level transport up to 2000 kg")
                    fleet_estimates.append(f"XPL201: ~{fleet_size} vehicles")

            if "Stacking/Conveyor" in selected_apps and all_data.get("load_weight_kg") and all_data.get("max_stacking_height_m"):
                is_valid, msg, color = validate_xqe122(
                    all_data.get("load_weight_kg", 0),
                    all_data.get("max_stacking_height_m", 0),
                    320
                )
                validation_summary.append(f"XQE122: {msg} ({color})")
                if is_valid or color == "orange":
                    speed = 1.0
                    cycle_time = (avg_dist * 2 / speed) + 45 if avg_dist else 45
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2)) if pallets_hr else 1
                    recommendations.append("XQE122 - Stacking / conveyor handling")
                    fleet_estimates.append(f"XQE122: ~{fleet_size} vehicles")

            if "Narrow Aisle" in selected_apps and all_data.get("aisle_width_m") and all_data.get("xna_model"):
                model = all_data.get("xna_model", "XNA121 (up to 8.5m)")
                is_valid, msg, color = validate_xna121_151(
                    all_data.get("aisle_width_m", 0),
                    all_data.get("load_weight_kg", 0),
                    all_data.get("max_stacking_height_m", 0),
                    model
                )
                validation_summary.append(f"{model}: {msg} ({color})")
                if is_valid or color == "orange":
                    speed = 1.0
                    cycle_time = (avg_dist * 2 / speed) + 60 if avg_dist else 60
                    fleet_size = max(1, round((pallets_hr * cycle_time / 3600) * 1.2)) if pallets_hr else 1
                    recommendations.append(f"{model} - Narrow aisle stacking")
                    fleet_estimates.append(f"{model}: ~{fleet_size} vehicles")

            context["recommendation"] = "\n\n".join(recommendations) if recommendations else ""
            context["fleet_recommendation"] = "\n".join(fleet_estimates) if fleet_estimates else ""
            context["validation_summary"] = "\n".join(validation_summary) if validation_summary else ""

            # Per-product texts for Word report product table
            xqe_rec_parts = [r for r in recommendations if "XQE" in r]
            xqe_rec_parts += [e for e in fleet_estimates if "XQE" in e]
            xqe_rec_parts += [v.split(": ", 1)[-1].rsplit(" (", 1)[0] for v in validation_summary if "XQE" in v]
            context["recommendation_text"] = "\n".join(xqe_rec_parts) if xqe_rec_parts else ""

            xpl_rec_parts = [r for r in recommendations if "XPL" in r]
            xpl_rec_parts += [e for e in fleet_estimates if "XPL" in e]
            xpl_rec_parts += [v.split(": ", 1)[-1].rsplit(" (", 1)[0] for v in validation_summary if "XPL" in v]
            context["xpl_recommendation"] = "\n".join(xpl_rec_parts) if xpl_rec_parts else ""

            if all_data.get("ep_wms_used") == "Yes":
                context["dasp_info"] = "EP WMS / DAS included as coordination layer above EP USP Fleet Manager."
            else:
                context["dasp_info"] = ""

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
            st.session_state["auto_zip_download_done"] = False
            st.session_state["zip_popup_open"] = False
            st.session_state["report_ready"] = True

            status_text.text("Report ready.")
            progress_bar.progress(100)

            st.success("Report generated successfully.")

            st.subheader("Dashboard Summary")
            st.table(
                {
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
                }
            )

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
    final_zip_bytes = final_zip_buffer.getvalue()

    if not st.session_state.get("auto_zip_download_done"):
        st.session_state["auto_zip_download_done"] = True
        st.session_state["zip_popup_open"] = True
        trigger_auto_download(final_zip_bytes, zip_filename, "application/zip")
        st.rerun()

    if st.session_state.get("zip_popup_open"):
        st.session_state["zip_popup_open"] = False
        zip_download_popup()

    st.download_button(
        label="Download Final ZIP (fallback)",
        data=final_zip_bytes,
        file_name=zip_filename,
        mime="application/zip",
        key="download_final_zip",
    )
