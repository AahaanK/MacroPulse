"""Unit tests for expected-return models against hand-worked OLS solutions."""

import numpy as np
import pandas as pd
import pytest

from macropulse.analytics.models import fit_expected_return_model, predict_expected_return


def test_mean_adjusted_model():
    """Verify mean-adjusted model against hand calculation.

    Data: [0.01, 0.02, 0.03, -0.01, 0.00]
    n = 5
    Sum = 0.05
    Mean alpha = 0.01
    Residuals = [0.00, 0.01, 0.02, -0.02, -0.01]
    Sum residuals^2 = 0 + 0.0001 + 0.0004 + 0.0004 + 0.0001 = 0.0010
    dof = 4 -> s^2 = 0.0010 / 4 = 0.00025 -> s_eps = sqrt(0.00025) = 0.01581139
    """
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    r = pd.Series([0.01, 0.02, 0.03, -0.01, 0.00], index=dates)

    fit = fit_expected_return_model(r, model_type="mean_adjusted")

    assert fit.model_type == "mean_adjusted"
    assert fit.n_obs == 5
    assert pytest.approx(fit.alpha, abs=1e-6) == 0.01
    assert fit.beta == 0.0
    assert pytest.approx(fit.sigma_epsilon, abs=1e-6) == np.sqrt(0.00025)

    pred = predict_expected_return(fit)
    assert pytest.approx(pred, abs=1e-6) == 0.01


def test_market_model_ols():
    """Verify market model OLS against hand-computed slope and intercept.

    Toy data (n = 10):
        x = [0.01, 0.02, -0.01, 0.03, 0.00, 0.01, -0.02, 0.02, 0.01, -0.01]
        y = 0.005 + 1.2 * x + noise

    Let x = [-2, -1, 0, 1, 2] * 2 (repeats for n=10)
    Here, let's pick simple clean numbers:
        x: [1, 2, 3, 4, 5]
        mean(x) = 3
        (x - 3): [-2, -1, 0, 1, 2]
        sum((x - 3)^2) = 4 + 1 + 0 + 1 + 4 = 10

        y = 1.5 * x + 0.5:
        y: [2.0, 3.5, 5.0, 6.5, 8.0]
        mean(y) = 5.0
        (y - 5): [-3.0, -1.5, 0.0, 1.5, 3.0]
        sum((x - 3)*(y - 5)) = (-2)*(-3) + (-1)*(-1.5) + 0 + 1.5 + 6 = 6 + 1.5 + 1.5 + 6 = 15.0

        beta = 15.0 / 10.0 = 1.5
        alpha = mean(y) - beta * mean(x) = 5.0 - 1.5 * 3.0 = 0.5
        R^2 = 1.0 (perfect linear relation)
        residuals = 0.0 -> sigma_epsilon = 0.0
    """
    # Repeat pattern twice to satisfy minimum length checks
    x_vals = [-0.02, -0.01, 0.00, 0.01, 0.02] * 2
    # y = 0.005 + 1.5 * x
    y_vals = [0.005 + 1.5 * x for x in x_vals]

    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    r_asset = pd.Series(y_vals, index=dates)
    r_bench = pd.Series(x_vals, index=dates)

    fit = fit_expected_return_model(r_asset, r_bench, model_type="market_model")

    assert fit.model_type == "market_model"
    assert fit.n_obs == 10
    assert pytest.approx(fit.beta, abs=1e-5) == 1.50
    assert pytest.approx(fit.alpha, abs=1e-5) == 0.005
    assert pytest.approx(fit.r_squared, abs=1e-4) == 1.0
    assert pytest.approx(fit.sigma_epsilon, abs=1e-5) == 0.0

    # Prediction on event day when benchmark moves +1% (0.01)
    # Expected return = alpha + beta * 0.01 = 0.005 + 1.5 * 0.01 = 0.020 (2.0%)
    pred = predict_expected_return(fit, benchmark_value=0.01)
    assert pytest.approx(pred, abs=1e-5) == 0.020
