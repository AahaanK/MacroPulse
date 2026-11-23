"""Unit tests for statistical tests, BMP test, bootstrap CI, and plain-English verdict."""

import numpy as np
import pytest
import scipy.stats as stats

from macropulse.analytics.stats import (
    compute_bmp_test,
    compute_bootstrap_ci,
    compute_effect_size,
    compute_window_statistics,
)


def test_cross_sectional_t_test():
    """Verify t-statistic and p-value against hand calculation and SciPy.

    Data (n = 5): [1.0, 2.0, 3.0, 4.0, 5.0]
    mean = 3.0
    sum_sq_diff = 4 + 1 + 0 + 1 + 4 = 10.0
    s^2 = 10.0 / 4 = 2.5 -> s = sqrt(2.5) = 1.5811388
    se = s / sqrt(5) = sqrt(0.5) = 0.70710678
    t_stat = 3.0 / 0.70710678 = 4.24264
    df = 4
    two-sided p-value: 2 * stats.t.sf(4.24264, 4) = 0.0132
    """
    cars = [1.0, 2.0, 3.0, 4.0, 5.0]
    res = compute_window_statistics(cars, window=(0, 1), unit="%")

    assert res.n_events == 5
    assert pytest.approx(res.mean_car, abs=1e-3) == 3.0
    assert pytest.approx(res.std_car, abs=1e-3) == np.sqrt(2.5)
    assert pytest.approx(res.t_stat, abs=1e-2) == 4.24
    assert pytest.approx(res.p_value_t, abs=1e-3) == 0.0132
    # Verify plain-English verdict states distinguishable from zero
    assert "statistically distinguishable from zero" in res.verdict


def test_bmp_standardized_test():
    """Verify BMP test statistic.

    If standardized CARs are all equal to 2.0:
    mean = 2.0, variance of mean = 0 -> degenerate case handled.
    If standardized CARs are [1.0, 2.0, 3.0]:
    mean = 2.0
    var = sum((x - 2)^2) / (3 * 2) = (1 + 0 + 1) / 6 = 2/6 = 1/3
    se = sqrt(1/3) = 0.57735
    Z_BMP = 2.0 / 0.57735 = 3.4641
    df = 2 -> p = 2 * stats.t.sf(3.4641, 2) = 0.0742
    """
    scars = np.array([1.0, 2.0, 3.0])
    bmp_stat, p_val = compute_bmp_test(scars)

    assert bmp_stat is not None and p_val is not None
    assert pytest.approx(bmp_stat, abs=1e-2) == 3.46
    assert pytest.approx(p_val, abs=1e-3) == 0.0742


def test_bootstrap_reproducibility_with_seed():
    """Verify that bootstrap CI is 100% deterministic given fixed seed."""
    vals = np.array([0.5, -0.2, 0.8, 1.2, -0.4, 0.6, 0.1, -0.3, 0.9, 0.4])

    low_1, high_1 = compute_bootstrap_ci(vals, n_resamples=1000, seed=123)
    low_2, high_2 = compute_bootstrap_ci(vals, n_resamples=1000, seed=123)

    assert low_1 == low_2
    assert high_1 == high_2
    assert low_1 < high_1


def test_effect_size_bands():
    """Verify Cohen's d qualitative bands."""
    # d = 0.1 / 1.0 = 0.1 (< 0.2) -> Negligible
    d1, band1 = compute_effect_size(0.1, 1.0)
    assert band1 == "Negligible"

    # d = 0.35 / 1.0 = 0.35 (0.2 <= d < 0.5) -> Small
    d2, band2 = compute_effect_size(0.35, 1.0)
    assert band2 == "Small"

    # d = -0.65 / 1.0 = -0.65 (0.5 <= |d| < 0.8) -> Moderate
    d3, band3 = compute_effect_size(-0.65, 1.0)
    assert band3 == "Moderate"

    # d = 1.2 / 1.0 = 1.2 (|d| >= 0.8) -> Large
    d4, band4 = compute_effect_size(1.2, 1.0)
    assert band4 == "Large"
