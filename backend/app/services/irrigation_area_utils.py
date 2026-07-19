"""
Area conversion and irrigation volume scaling utilities.

Key insight: 1 liter of water spread evenly over 1 square meter is exactly
1mm of irrigation depth (1 L/m^2 = 1mm). This means a water recommendation
expressed as "liters per square meter" is numerically identical to
"millimeters of irrigation depth" — a standard, realistic unit real
irrigation engineers actually use (typical single irrigation events apply
roughly 10-40mm depending on crop and soil type).
"""

SQUARE_METERS_PER_UNIT = {
    "acre": 4046.8564224,
    "hectare": 10000.0,
    "square_meter": 1.0,
    "square_feet": 0.09290304,
}


def area_to_square_meters(area_value: float, area_unit: str) -> float:
    factor = SQUARE_METERS_PER_UNIT.get(area_unit)
    if factor is None:
        raise ValueError(f"Unknown area unit: {area_unit}")
    return area_value * factor


def compute_total_water_needed(
    water_depth_liters_per_sqm: float,
    area_value: float,
    area_unit: str,
    flow_rate_lph: float | None = None,
) -> dict:
    """
    Scales a per-square-meter irrigation depth recommendation up to a real
    field size, and — if the farmer's irrigation system flow rate is known —
    converts that into a practical run-time duration.
    """
    area_sqm = area_to_square_meters(area_value, area_unit)
    total_liters = water_depth_liters_per_sqm * area_sqm

    result = {
        "area_value": area_value,
        "area_unit": area_unit,
        "area_square_meters": round(area_sqm, 1),
        "total_liters_needed": round(total_liters, 1),
        "recommended_duration_hours": None,
    }

    if flow_rate_lph and flow_rate_lph > 0:
        result["recommended_duration_hours"] = round(total_liters / flow_rate_lph, 2)

    return result
