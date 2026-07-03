# Smart AGV Site Survey Tool

A multilingual, web-based presales and site survey tool for AGV/AMR automation projects.  
Built to help sales engineers collect customer requirements on-site, validate product configurations live, and generate a structured Word report packaged as a downloadable ZIP.

🌐 **Live demo:** [ep-intelligent-survey-tool.streamlit.app](https://ep-intelligent-survey-tool.streamlit.app)

---

## What it does

- **4-tab survey form** — Basic Information, Material Flow, Data Flow & Integration, Site Conditions
- **Live product validation** — real-time ✅/❌ checks for XPL201, XQE122, XNA121/XNA151 against aisle width, load weight, stacking height, and pallet type
- **Smart defaults** — pre-fills typical values when an application type is selected
- **Fleet size estimation** — auto-calculates recommended number of vehicles from throughput and cycle time
- **Word report generation** — renders a structured `.docx` report via `template.docx` and packages it with uploaded photos, CAD files, and layouts into a ZIP
- **Save / Resume session** — export form state as JSON and reload in a future visit
- **8 languages** — English, Deutsch, Français, Nederlands, Español, Italiano, Română, Polski
- **Guided mode** — step-by-step view for non-technical users, or Expert tab view for engineers
- **Resource library** — downloadable layout specs, technical references, and system requirements

---

## Products covered

| Application | Max Weight | Max Height | Min Aisle |
|---|---|---|---|
| Transport / Cross Docking | 2000 kg | Floor level | 1.5 m |
| Stacking / Conveyor | 1500 kg | 5.5 m | 2900 mm |
| Narrow Aisle | 1200 kg | 8.5 m | 1.78 m |
| Narrow Aisle | 1500 kg | 13.0 m | 1.78 m |

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit (Python) |
| Report generation | docxtpl (Jinja2 + python-docx) |
| Multilanguage | Custom translation module (8 languages) |
| Deployment | Streamlit Community Cloud |

---

## Project structure

```
app.py                  Main entrypoint — orchestrates tabs, report generation, ZIP download
header_tab.py           Tab 1: Basic Information, pallet config, application selection, inline validation
secondary_tab.py        Tab 2: Material Flow sequence builder
data_flow_tab.py        Tab 3: Data Flow & Integration block builder
site_conditions_tab.py  Tab 4: Site Conditions & Safety
product_validators.py   XPL / XQE / XNA validation rules
translations.py         EN / DE / FR / NL / ES / IT / RO / PL translations
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

Deployed on **Streamlit Community Cloud** (free tier).  
Every push to `main` triggers an automatic redeploy within ~30 seconds.

---

## Requirements

```
streamlit>=1.32.0
docxtpl>=0.16.0
python-docx>=1.1.0
```
