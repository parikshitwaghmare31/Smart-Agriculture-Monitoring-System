"""
Unit tests for area unit conversion and total irrigation water scaling.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.irrigation_area_utils import area_to_square_meters, compute_total_water_needed


def test_acre_to_square_meters():
    assert abs(area_to_square_meters(1, "acre") - 4046.8564224) < 0.01


def test_hectare_to_square_meters():
    assert area_to_square_meters(1, "hectare") == 10000.0


def test_square_feet_to_square_meters():
    assert abs(area_to_square_meters(1, "square_feet") - 0.09290304) < 0.0001


def test_unknown_unit_raises():
    try:
        area_to_square_meters(1, "furlong")
        assert False, "Expected ValueError for unknown unit"
    except ValueError:
        pass


def test_total_water_for_one_acre_matches_known_hydrology_conversion():
    """
    1mm of irrigation depth over 1 acre is a well-established hydrology
    figure: ~4046.86 liters. This confirms our math matches real-world
    convention, not just internal consistency.
    """
    result = compute_total_water_needed(
        water_depth_liters_per_sqm=1.0, area_value=1, area_unit="acre"
    )
    assert abs(result["total_liters_needed"] - 4046.9) < 1.0


def test_total_water_scales_linearly_with_depth():
    result_10mm = compute_total_water_needed(10.0, area_value=1, area_unit="acre")
    result_20mm = compute_total_water_needed(20.0, area_value=1, area_unit="acre")
    assert abs(result_20mm["total_liters_needed"] - 2 * result_10mm["total_liters_needed"]) < 1.0


def test_duration_computed_when_flow_rate_given():
    result = compute_total_water_needed(
        water_depth_liters_per_sqm=22.66, area_value=1, area_unit="acre", flow_rate_lph=4000
    )
    expected_total = 22.66 * 4046.8564224
    expected_hours = expected_total / 4000
    assert abs(result["total_liters_needed"] - expected_total) < 1.0
    assert abs(result["recommended_duration_hours"] - expected_hours) < 0.01


def test_duration_is_none_when_no_flow_rate_given():
    result = compute_total_water_needed(22.66, area_value=1, area_unit="acre")
    assert result["recommended_duration_hours"] is None
