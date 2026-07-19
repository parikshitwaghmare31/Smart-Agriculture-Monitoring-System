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

# Rough reference discharge ranges for common agricultural centrifugal pumps,
# used ONLY as a fallback estimate when a farmer doesn't know their pump's
# actual rated discharge. Actual discharge depends heavily on total dynamic
# head (suction + delivery lift) and pipe sizing, so these are deliberately
# conservative midpoints — always prefer a farmer-provided rated value.
PUMP_HP_TO_LPH_ESTIMATE = {
    1: 4500,
    2: 9000,
    3: 13500,
    5: 20000,
    7.5: 28000,
    10: 37000,
}


def estimate_pump_discharge_lph(pump_hp: float) -> float:
    """Rough fallback estimate — interpolates/extrapolates from the reference table."""
    known_hp = sorted(PUMP_HP_TO_LPH_ESTIMATE.keys())
    if pump_hp <= known_hp[0]:
        return PUMP_HP_TO_LPH_ESTIMATE[known_hp[0]] * (pump_hp / known_hp[0])
    if pump_hp >= known_hp[-1]:
        return PUMP_HP_TO_LPH_ESTIMATE[known_hp[-1]] * (pump_hp / known_hp[-1])

    for lower, upper in zip(known_hp, known_hp[1:]):
        if lower <= pump_hp <= upper:
            lph_lower, lph_upper = PUMP_HP_TO_LPH_ESTIMATE[lower], PUMP_HP_TO_LPH_ESTIMATE[upper]
            fraction = (pump_hp - lower) / (upper - lower)
            return lph_lower + fraction * (lph_upper - lph_lower)

    return PUMP_HP_TO_LPH_ESTIMATE[5]  # unreachable fallback


def compute_irrigation_system_flow_rate(
    area_value: float,
    area_unit: str,
    row_spacing_cm: float,
    emitter_spacing_cm: float,
    emitter_discharge_lph: float,
    pump_rated_discharge_lph: float | None = None,
    pump_hp: float | None = None,
) -> dict:
    """
    Computes what a drip irrigation system can actually deliver, from its
    real physical parameters, instead of relying on a guessed flow rate.

    Returns the system's theoretical simultaneous demand (if every emitter
    ran at once), the pump's supply capacity, which one is the bottleneck,
    and how many irrigation zones the field needs to be split into if the
    pump can't cover everything simultaneously.
    """
    area_sqm = area_to_square_meters(area_value, area_unit)

    area_per_emitter_sqm = (row_spacing_cm / 100) * (emitter_spacing_cm / 100)
    num_emitters = area_sqm / area_per_emitter_sqm
    system_demand_lph = num_emitters * emitter_discharge_lph

    pump_supply_is_estimated = pump_rated_discharge_lph is None
    if pump_rated_discharge_lph is not None:
        pump_supply_lph = pump_rated_discharge_lph
    elif pump_hp is not None:
        pump_supply_lph = estimate_pump_discharge_lph(pump_hp)
    else:
        raise ValueError("Either pump_rated_discharge_lph or pump_hp must be provided")

    effective_flow_rate_lph = min(system_demand_lph, pump_supply_lph)
    zones_needed = 1
    if system_demand_lph > pump_supply_lph:
        import math
        zones_needed = math.ceil(system_demand_lph / pump_supply_lph)

    return {
        "num_emitters": round(num_emitters),
        "system_demand_lph": round(system_demand_lph, 1),
        "pump_supply_lph": round(pump_supply_lph, 1),
        "pump_supply_is_estimated": pump_supply_is_estimated,
        "effective_flow_rate_lph": round(effective_flow_rate_lph, 1),
        "zones_needed": zones_needed,
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
