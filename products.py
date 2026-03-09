# products.py

PRODUCT_SPECS = {
    "XPL201": {
        "model": "XPL201",
        "application": "Transport / Cross Docking",
        "max_load_kg": 2000,
        "notes": [
            "Floor-level pallet transport",
            "Suitable for cross docking and horizontal transport",
            "Aisle requirement depends on movement type and layout"
        ]
    },
    "XQE122": {
        "model": "XQE122",
        "application": "Stacking / Conveyor",
        "max_load_kg": 1500,
        "max_height_m_at_1200kg": 5.5,
        "max_height_m_at_1500kg": 3.5,
        "notes": [
            "Stacking and conveyor pickup application",
            "Minimum reference fork entry width used in validation: 320 mm"
        ]
    },
    "XNA121": {
        "model": "XNA121",
        "application": "Narrow Aisle",
        "max_load_kg": 1200,
        "max_height_m": 8.5,
        "recommended_aisle_m": "1.78–2.0"
    },
    "XNA151": {
        "model": "XNA151",
        "application": "Narrow Aisle",
        "max_load_kg": 1500,
        "max_height_m": 13.0,
        "recommended_aisle_m": "1.78–2.0"
    }
}