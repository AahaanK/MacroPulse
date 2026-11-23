"""Unit tests for return calculations with hand-computed expected outputs."""

import numpy as np
import pandas as pd
import pytest

from macropulse.analytics.returns import calculate_returns


def test_simple_returns():
    """Verify simple return: R_t = P_t / P_{t-1} - 1.

    Hand-computed toy prices:
        t0: 100.0
        t1: 105.0 -> (105 / 100) - 1 = +0.05 (+5%)
        t2: 94.5  -> (94.5 / 105) - 1 = -0.10 (-10%)
        t3: 94.5  -> (94.5 / 94.5) - 1 = 0.00 (0%)
    """
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.Series([100.0, 105.0, 94.5, 94.5], index=dates)

    rets = calculate_returns(prices, metric_type="return", method="simple")

    assert np.isnan(rets.iloc[0])
    assert pytest.approx(rets.iloc[1], abs=1e-6) == 0.05
    assert pytest.approx(rets.iloc[2], abs=1e-6) == -0.10
    assert pytest.approx(rets.iloc[3], abs=1e-6) == 0.00


def test_log_returns():
    """Verify log return: r_t = ln(P_t / P_{t-1}).

    Hand-computed toy prices:
        t0: 100.0
        t1: 110.0 -> ln(1.10) = 0.09531018
        t2: 99.0  -> ln(99 / 110) = ln(0.9) = -0.1053605
    """
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.Series([100.0, 110.0, 99.0], index=dates)

    log_rets = calculate_returns(prices, metric_type="return", method="log")

    assert np.isnan(log_rets.iloc[0])
    assert pytest.approx(log_rets.iloc[1], abs=1e-6) == np.log(1.10)
    assert pytest.approx(log_rets.iloc[2], abs=1e-6) == np.log(0.90)


def test_yield_level_changes_in_basis_points():
    """Verify yield level differences in basis points: diff * 100.

    Hand-computed toy yields (%):
        t0: 4.50%
        t1: 4.58% -> (4.58 - 4.50) = +0.08% -> +8.0 bp
        t2: 4.52% -> (4.52 - 4.58) = -0.06% -> -6.0 bp
    """
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    yields = pd.Series([4.50, 4.58, 4.52], index=dates)

    bp_diff = calculate_returns(yields, metric_type="level_change", unit="bp")

    assert np.isnan(bp_diff.iloc[0])
    assert pytest.approx(bp_diff.iloc[1], abs=1e-6) == 8.0
    assert pytest.approx(bp_diff.iloc[2], abs=1e-6) == -6.0
