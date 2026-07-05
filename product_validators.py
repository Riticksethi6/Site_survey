# product_validators.py – Generic AMR/AGV validation rules

def validate_xpl201(aisle_width_m, load_weight_kg, pallet_type=""):
    """
    Horizontal Transport AMR (Transport / Cross Docking).
    Vehicle capacity: 2000 kg.
    Euro pallet structural limit: ~1500 kg (dynamic load).
    Minimum aisle: 1.5 m one-way driving.
    """
    issues = []
    color = "green"

    if pallet_type == "Euro" and load_weight_kg > 1500:
        issues.append(
            f"Note: Horizontal Transport AMR can carry up to 2000 kg, but a standard Euro pallet is only structurally rated for ~1500 kg under dynamic load. "
            f"Current load: {load_weight_kg} kg on a Euro pallet. "
            "Consider using an Industrial or custom pallet for loads above 1500 kg."
        )
        color = "orange"

    if load_weight_kg > 2000:
        issues.append(f"Horizontal Transport AMR maximum vehicle load capacity is 2000 kg. Current: {load_weight_kg} kg.")
        color = "red"

    if aisle_width_m and aisle_width_m < 1.5:
        issues.append(
            f"Minimum aisle width for Horizontal Transport AMR (one-way driving) is 1.5 m. Current: {aisle_width_m} m.\n"
            "Reference aisle table (Euro Pallets):\n"
            "  • One-way driving: 1.5 m\n"
            "  • Two-way driving: 3.0 m\n"
            "  • One-way turning: 2.3 m\n"
            "  • Two-way turning: 3.8 m\n"
            "  • Loading/Unloading one-side: 3.0 m\n"
            "  • Loading/Unloading both-sides: 3.5–5.6 m"
        )
        color = "red"
    elif aisle_width_m and aisle_width_m < 1.8:
        issues.append(
            f"Aisle {aisle_width_m} m is technically acceptable (≥1.5 m) but 1.8 m is recommended for "
            "better safety fields, higher speed, and easier commissioning."
        )
        if color == "green":
            color = "orange"

    if issues:
        return False, "\n\n".join(issues), color

    return True, "Horizontal Transport AMR – Within specification (Transport / Cross Docking)", "green"


def validate_xqe122(load_weight_kg, max_stacking_height_m, aisle_width_mm=0):
    """
    Stacker AMR (Stacking / Conveyor).
    Vehicle capacity: 1500 kg (900 kg above 4.5 m, 1200 kg above 3.5 m).
    Minimum aisle width: 2900 mm (straight passage, one-way).
    Floor stacking channel: truck body 1240 mm + 200 mm clearance each side = 1640 mm min channel width.
    Floor stacking gap: 200 mm between pallets/boxes in ALL directions.
    Rack stacking gap: 75 mm between pallets on shelf (standard).
    """
    issues = []
    color = "green"

    if load_weight_kg > 1500:
        issues.append(f"Stacker AMR maximum load capacity is 1500 kg. Current: {load_weight_kg} kg.")
        color = "red"
    elif load_weight_kg > 1200 and max_stacking_height_m > 3.5:
        issues.append(
            f"For loads above 1200 kg, maximum stacking height is 3.5 m. "
            f"Current: {load_weight_kg} kg at {max_stacking_height_m} m."
        )
        color = "red"
    elif load_weight_kg > 900 and max_stacking_height_m > 4.5:
        issues.append(
            f"For loads above 900 kg, maximum stacking height is 4.5 m. "
            f"Current: {load_weight_kg} kg at {max_stacking_height_m} m."
        )
        color = "red"
    elif max_stacking_height_m > 5.5:
        issues.append(
            f"Stacker AMR maximum stacking height is 5.5 m (at ≤900 kg). "
            f"Current: {max_stacking_height_m} m."
        )
        color = "red"

    if aisle_width_mm and aisle_width_mm < 2900:
        issues.append(
            f"Minimum aisle width for Stacker AMR is 2900 mm (straight passage, one-way). "
            f"Current: {aisle_width_mm} mm.\n"
            "Note: Truck body width is 1240 mm. Add 200 mm clearance on each side for safe operation."
        )
        if color == "green":
            color = "orange"

    if issues:
        return False, "\n\n".join(issues), color

    return True, "Stacker AMR – Within specification (Stacking / Conveyor)", "green"


def validate_xna121_151(aisle_width_m, load_weight_kg, max_stacking_height_m, model):
    """
    VNA Standard / VNA High Reach (Very Narrow Aisle).
    Minimum aisle: 1.78 m.
    """
    issues = []
    color = "green"

    if aisle_width_m and aisle_width_m < 1.78:
        issues.append(f"Minimum aisle width for VNA robot is 1.78 m. Current: {aisle_width_m} m.")
        color = "red"
    elif aisle_width_m and aisle_width_m > 2.0:
        issues.append(
            f"VNA robot is optimised for aisles up to 2.0 m. "
            f"Current: {aisle_width_m} m — wider aisles may reduce efficiency."
        )
        if color == "green":
            color = "orange"

    if "Standard" in model:
        if max_stacking_height_m > 8.5:
            issues.append(f"VNA Standard maximum lift height is 8.5 m. Current: {max_stacking_height_m} m.")
            color = "red"
        if load_weight_kg > 1200:
            issues.append(f"VNA Standard maximum load is 1200 kg. Current: {load_weight_kg} kg.")
            color = "red"
    else:
        if max_stacking_height_m > 13.0:
            issues.append(f"VNA High Reach maximum lift height is 13.0 m. Current: {max_stacking_height_m} m.")
            color = "red"
        if load_weight_kg > 1500:
            issues.append(f"VNA High Reach maximum load is 1500 kg. Current: {load_weight_kg} kg.")
            color = "red"

    if issues:
        return False, "\n\n".join(issues), color

    return True, f"{model} – Within specification (Very Narrow Aisle)", "green"
