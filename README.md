# EP Equipment – Smart Products Site Survey Tool

A web-based presales and site survey tool for EP Equipment AGV/AMR projects.  
Helps sales engineers collect customer requirements on-site, validate product configurations, and generate a structured Word report packaged as a ZIP.

🌐 **Live app:** [ep-intelligent-survey-tool.streamlit.app](https://ep-intelligent-survey-tool.streamlit.app)

---

## What it does

- **4-tab survey form** — Basic Information, Material Flow, Data Flow & Integration, Site Conditions
- **Live product validation** — real-time ✅/❌ checks for XPL201, XQE122, XNA121/XNA151 against aisle width, load weight, stacking height, pallet type
- **Smart defaults** — pre-fills typical values when an application is selected
- **Fleet size estimation** — auto-calculates recommended number of vehicles from throughput and cycle time
- **Word report generation** — renders a structured `.docx` report via `template.docx` and packages it with uploaded photos, CAD files, and feedback into a ZIP
- **Save / Resume session** — export form state as JSON and reload in a future visit
- **7 languages** — English, Deutsch, Français, Nederlands, Español, Italiano, Polski
- **Guided mode** — step-by-step view for non-technical users, or Expert tab view for engineers
- **Resource library** — downloadable layout specs, white books, and system requirements

---

## Products covered

| Product | Application | Max Weight | Max Height | Min Aisle |
|---|---|---|---|---|
| XPL201 | Transport / Cross Docking | 2000 kg | Floor level | 1.5 m |
| XQE122 | Stacking / Conveyor | 1500 kg | 5.5 m | 2900 mm |
| XNA121 | Narrow Aisle | 1200 kg | 8.5 m | 1.78 m |
| XNA151 | Narrow Aisle | 1500 kg | 13.0 m | 1.78 m |

---

## Project structure

```
app.py                  Main entrypoint — orchestrates tabs, report generation, ZIP download
header_tab.py           Tab 1: Basic Information, pallet config, application selection, inline validation
secondary_tab.py        Tab 2: Material Flow sequence builder
data_flow_tab.py        Tab 3: Data Flow & Integration block builder
site_conditions_tab.py  Tab 4: Site Conditions & Safety
product_validators.py   XPL / XQE / XNA validation rules
translations.py         EN / DE / FR / NL / ES / IT / PL translations
products.py             Product spec catalogue
template.docx           Word report template (Jinja2 via docxtpl)
```

---

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## Deployment

The app is deployed on **Streamlit Community Cloud** (free tier).  
Every push to `main` triggers an automatic redeploy within ~30 seconds.

---

## Requirements

```
streamlit>=1.32.0
docxtpl>=0.16.0
python-docx>=1.1.0
```

---

## Contact

EP Equipment EU — [ep-equipment.eu](https://ep-equipment.eu)
