# product_validators.py – Final version aligned with all XPL & XQE PDFs (March 2026)

def validate_xpl201(aisle_width_m, load_weight_kg):
    """
    Validation for XPL201 (Transport / Cross Docking).
    Uses the lowest minimum from your PDFs (1.5 m one-way driving), but explains full range.
    No stacking height check (floor-level only).
    """
    issues = []

    # Aisle width check – 1.5 m is the absolute minimum from one PDF version
    if aisle_width_m < 1.5:
        issues.append(
            f"Minimum aisle width for XPL201 (one-way driving) is 1.5 m according to the XPL Layout and Aisle Planning Specification. "
            f"Current: {aisle_width_m} m is too narrow. "
            "Full recommended values from specification (Euro Pallets):\n"
            "• Driving (One-way): 1.5–1.8 m\n"
            "• Driving (Two-way): 3.0–3.6 m\n"
            "• Turning (One-way): 2.3 m\n"
            "• Turning (Two-way): 3.8 m\n"
            "• Loading/Unloading (One-way, one side): 3.0 m\n"
            "• Loading/Unloading (One-way, both sides): 3.5 m\n"
            "• Loading/Unloading (Two-way, one side): 4.0 m\n"
            "• Loading/Unloading (Two-way, both sides): 4.5–5.6 m\n"
            "Note: More aisle space allows higher driving speed, larger safety detection fields, faster pallet throughput, easier commissioning and tuning."
        )
    elif aisle_width_m < 1.8:
        issues.append(
            f"Current aisle width {aisle_width_m} m is between 1.5–1.8 m. "
            "While technically acceptable in some XPL layouts (one-way driving), 1.8 m is recommended for better safety and performance. "
            "Please refer to the full XPL Layout and Aisle Planning Specification for your exact action types."
        )

    if load_weight_kg > 2000:
        issues.append(f"XPL201 maximum load capacity is 2000 kg. Current: {load_weight_kg} kg")

    if issues:
        is_critical = any("maximum" in issue.lower() or "load capacity" in issue.lower() for issue in issues)
        color = "red" if is_critical else "orange"
        return False, "\n".join(issues), color

    return True, "Acceptable for XPL201 (Transport / Cross Docking)", "green"


def validate_xqe122(load_weight_kg, max_stacking_height_m, fork_entry_width):
    """
    Validation for XQE122 (Stacking / Conveyor).
    Based on XQE Layout and Aisle Planning Specification (Euro Pallets).
    """
    issues = []

    if fork_entry_width < 320:
        issues.append(f"Minimum fork entry width for XQE122 is 320 mm. Current: {fork_entry_width} mm")

    if load_weight_kg > 1500:
        issues.append(f"XQE122 maximum load capacity is 1500 kg. Current: {load_weight_kg} kg")
    elif load_weight_kg > 1200 and max_stacking_height_m > 3.5:
        issues.append(f"For loads > 1200 kg, maximum stacking height is 3.5 m. Current: {max_stacking_height_m} m")
    elif max_stacking_height_m > 5.5:
        issues.append(f"XQE122 maximum stacking height is 5.5 m (at 1200 kg, special arrangements required). Current: {max_stacking_height_m} m")

    if issues:
        is_critical = any("maximum" in issue.lower() or "load capacity" in issue.lower() for issue in issues)
        color = "red" if is_critical else "orange"
        return False, "\n".join(issues), color

    return True, "Acceptable for XQE122 (Stacking / Conveyor)", "green"


def validate_xna121_151(aisle_width_m, load_weight_kg, max_stacking_height_m, model):
    """
    Validation for XNA121 / XNA151 (Narrow Aisle).
    Aisle width typically 1.78–2.0 m (standard narrow aisle spec).
    """
    issues = []

    if aisle_width_m < 1.78:
        issues.append(f"Minimum aisle width for XNA is 1.78 m. Current: {aisle_width_m} m")
    if aisle_width_m > 2.0:
        issues.append(f"Recommended maximum aisle width for XNA is 2.0 m (wider aisles may reduce efficiency). Current: {aisle_width_m} m")

    if model == "XNA121 (up to 8.5m)":
        if max_stacking_height_m > 8.5:
            issues.append(f"XNA121 maximum lift height is 8.5 m. Current: {max_stacking_height_m} m")
        if load_weight_kg > 1200:
            issues.append(f"XNA121 maximum load is 1200 kg. Current: {load_weight_kg} kg")
    else:  # XNA151
        if max_stacking_height_m > 13.0:
            issues.append(f"XNA151 maximum lift height is 13 m. Current: {max_stacking_height_m} m")
        if load_weight_kg > 1500:
            issues.append(f"XNA151 maximum load is 1500 kg. Current: {load_weight_kg} kg")

    if issues:
        color = "red" if any("minimum" in msg.lower() or "maximum" in msg.lower() for msg in issues) else "orange"
        return False, "\n".join(issues), color

    return True, f"Acceptable for {model} (Narrow Aisle)", "green"