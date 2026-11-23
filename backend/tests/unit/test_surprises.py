"""Unit tests for surprise regression and asymmetry tests."""

import pytest
from macropulse.analytics.surprises import analyze_surprises


def test_surprise_regression_and_asymmetry():
    events = [
        {"id": 1, "period_date": "2023-01-01", "event_type": "CPI", "actual_first_release": 6.5, "previous_first_release": 6.0, "change_value": 0.5, "change_std": 0.5},
        {"id": 2, "period_date": "2023-02-01", "event_type": "CPI", "actual_first_release": 6.4, "previous_first_release": 6.0, "change_value": 0.4, "change_std": 0.5},
        {"id": 3, "period_date": "2023-03-01", "event_type": "CPI", "actual_first_release": 5.8, "previous_first_release": 6.0, "change_value": -0.2, "change_std": 0.5},
        {"id": 4, "period_date": "2023-04-01", "event_type": "CPI", "actual_first_release": 5.5, "previous_first_release": 6.0, "change_value": -0.5, "change_std": 0.5},
    ]

    event_cars = {
        1: -1.2,
        2: -0.9,
        3: +0.6,
        4: +1.4,
    }

    res = analyze_surprises(events, event_cars, asset_symbol="SPY", unit="%")

    assert res.mode == "indicator_change"
    assert res.regression.slope < 0  # Higher CPI surprise -> negative equity CAR
    assert len(res.data_points) == 4
    assert res.asymmetry.pos_n == 2
    assert res.asymmetry.neg_n == 2
    assert res.asymmetry.pos_mean_car < 0  # negative market move on high CPI
    assert res.asymmetry.neg_mean_car > 0  # positive market move on low CPI
