# customer_requirements_tab.py – Specification + Customer Demands
# Internal / Pre-Sales Use Only – mapped to template.docx

import streamlit as st

def build_customer_requirements_inputs():
    st.subheader("5. Specification + Customer Demands (Internal / Pre-Sales Use Only)")
    st.info("For EP internal team only. Fill after site survey and analysis.")

    # System integration & data flow
    integration_req = st.text_area(
        "System Integration / Data Flow Requirements (final)",
        height=160,
        placeholder="Summarize final integration needs after discussion with customer",
        value=st.session_state.get("integration_req_prefill", ""),
        key="demands_integration_req"
    )

    # Product specs & quantity
    product_specs = st.text_input(
        "Product Specifications & Quantity",
        placeholder="e.g. 8 × XPL201, 4 × XQE122, 2 × XNA151, specific customization",
        key="product_specs"
    )

    # Payment terms
    payment_terms = st.text_input(
        "Payment Terms",
        placeholder="e.g. 30% advance, 60% on delivery, 10% after commissioning",
        key="payment_terms"
    )

    # Desired timeline
    timeline = st.text_area(
        "Desired Project Timeline / Phases",
        height=100,
        placeholder="e.g. Q2 2026: Design & PO, Q3: Production, Q4: Delivery & commissioning",
        key="timeline"
    )

    # Acceptance conditions
    acceptance = st.text_area(
        "Acceptance Conditions / Criteria",
        height=100,
        placeholder="e.g. 95% uptime in first month, FAT/SAT passed, training completed",
        key="acceptance"
    )

    # Key technical points & risks
    risks = st.text_area(
        "Key Technical Points / Risks Identified",
        height=120,
        placeholder="e.g. narrow aisle tolerance, cold storage battery life, Wi-Fi dead zones, ramp gradient limit",
        key="risks"
    )

    # Project team / contacts
    team = st.text_area(
        "Project Team / Contacts",
        height=100,
        placeholder=(
            "Project Manager: John Doe (john@ep-equipment.eu)\n"
            "Sales Rep: Jane Smith\n"
            "Technical Lead: Alex Chen (CHN)\n"
            "Customer Contact: Customer XYZ"
        ),
        key="team"
    )

    # Preliminary conclusion
    conclusion = st.selectbox(
        "Preliminary Conclusion",
        ["Approve", "Reject", "Revise", "Postpone"],
        key="conclusion"
    )

    # Improvement suggestions / notes
    improvements = st.text_area(
        "Improvement Suggestions / Notes",
        height=100,
        placeholder="e.g. Recommend adding safety fencing in high-traffic area, upgrade Wi-Fi APs, consider XPL with higher speed",
        key="improvements"
    )

    return {
        "integration_req": integration_req.strip(),
        "product_specs": product_specs.strip(),
        "payment_terms": payment_terms.strip(),
        "timeline": timeline.strip(),
        "acceptance": acceptance.strip(),
        "risks": risks.strip(),
        "team": team.strip(),
        "conclusion": conclusion,
        "improvements": improvements.strip()
    }