# product_validators.py

def validate_xpl201(aisle_width_m, load_weight_kg):
    """
    Validation for XPL201 (Transport / Cross Docking).
    """
    issues = []

    if aisle_width_m < 1.5:
        issues.append(
            f"Minimum aisle width for XPL201 is 1.5 m. Current: {aisle_width_m} m."
        )
    elif aisle_width_m < 1.8:
        issues.append(
            f"Aisle width {aisle_width_m} m is technically possible in some layouts, "
            "but 1.8 m or more is recommended for better safety and performance."
        )

    if load_weight_kg > 2000:
        issues.append(
            f"XPL201 maximum load capacity is 2000 kg. Current: {load_weight_kg} kg."
        )

    if issues:
        is_critical = any("maximum load capacity" in issue.lower() for issue in issues)
        color = "red" if is_critical else "orange"
        return False, "\n".join(issues), color

    return True, "Acceptable for XPL201 (Transport / Cross Docking)", "green"


def validate_xqe122(load_weight_kg, max_stacking_height_m, reference_fork_entry_width=320):
    """
    Validation for XQE122 (Stacking / Conveyor).
    The third parameter is kept for compatibility with app.py,
    but it is treated as a fixed reference value.
    """
    issues = []

    if reference_fork_entry_width < 320:
        issues.append(
            f"Minimum reference fork entry width for XQE122 is 320 mm. Current: {reference_fork_entry_width} mm."
        )

    if load_weight_kg > 1500:
        issues.append(
            f"XQE122 maximum load capacity is 1500 kg. Current: {load_weight_kg} kg."
        )
    elif load_weight_kg > 1200 and max_stacking_height_m > 3.5:
        issues.append(
            f"For loads above 1200 kg, maximum stacking height is 3.5 m. Current: {max_stacking_height_m} m."
        )
    elif max_stacking_height_m > 5.5:
        issues.append(
            f"XQE122 maximum stacking height is 5.5 m. Current: {max_stacking_height_m} m."
        )

    if issues:
        is_critical = any("maximum" in issue.lower() or "load capacity" in issue.lower() for issue in issues)
        color = "red" if is_critical else "orange"
        return False, "\n".join(issues), color

    return True, "Acceptable for XQE122 (Stacking / Conveyor)", "green"


def validate_xna121_151(aisle_width_m, load_weight_kg, max_stacking_height_m, model):
    """
    Validation for XNA121 / XNA151 (Narrow Aisle).
    """
    issues = []

    if aisle_width_m < 1.78:
        issues.append(f"Minimum aisle width for XNA is 1.78 m. Current: {aisle_width_m} m.")
    if aisle_width_m > 2.0:
        issues.append(
            f"Recommended maximum aisle width for XNA is 2.0 m. Current: {aisle_width_m} m."
        )

    if model == "XNA121 (up to 8.5m)":
        if max_stacking_height_m > 8.5:
            issues.append(f"XNA121 maximum lift height is 8.5 m. Current: {max_stacking_height_m} m.")
        if load_weight_kg > 1200:
            issues.append(f"XNA121 maximum load is 1200 kg. Current: {load_weight_kg} kg.")
    else:
        if max_stacking_height_m > 13.0:
            issues.append(f"XNA151 maximum lift height is 13.0 m. Current: {max_stacking_height_m} m.")
        if load_weight_kg > 1500:
            issues.append(f"XNA151 maximum load is 1500 kg. Current: {load_weight_kg} kg.")

    if issues:
        color = "red" if any("maximum" in msg.lower() or "minimum" in msg.lower() for msg in issues) else "orange"
        return False, "\n".join(issues), color

    return True, f"Acceptable for {model} (Narrow Aisle)", "green"