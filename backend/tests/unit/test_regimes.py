"""Unit test verifying the mathematical guarantee of NO LOOK-AHEAD bias in regimes."""

import datetime
import numpy as np
import pandas as pd
import pytest

from macropulse.analytics.regimes import classify_market_regimes


def test_regimes_no_look_ahead_by_perturbation():
    """Verify that perturbing future data at t >= k has ZERO effect on labels at t < k.

    Per Rule 12:
    'No look-ahead: regime features at t use only data <= t-1 (test by perturbing
     future data and asserting labels don't change).'
    """
    dates = pd.date_range("2023-01-01", periods=120, freq="B")
    rng = np.random.default_rng(42)
    # Generate prices with steady upward drift
    base_prices = 100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, size=120)))

    df_original = pd.DataFrame({
        "trade_date": [d.date() for d in dates],
        "close": base_prices,
        "adj_close": base_prices,
    })

    regimes_original = classify_market_regimes(df_original)

    # Now create perturbed copy where days 80..119 have extreme artificial crashes/spikes
    perturbed_prices = base_prices.copy()
    perturbed_prices[80:] = perturbed_prices[80:] * 3.5  # extreme future shock

    df_perturbed = pd.DataFrame({
        "trade_date": [d.date() for d in dates],
        "close": perturbed_prices,
        "adj_close": perturbed_prices,
    })

    regimes_perturbed = classify_market_regimes(df_perturbed)

    # Assert that all classifications for t < 80 are EXACTLY IDENTICAL
    for t in range(80):
        orig_label = regimes_original.iloc[t]["label"]
        pert_label = regimes_perturbed.iloc[t]["label"]
        orig_vol = regimes_original.iloc[t]["feature_json"]["vol_21d"]
        pert_vol = regimes_perturbed.iloc[t]["feature_json"]["vol_21d"]

        assert orig_label == pert_label, f"Look-ahead detected at index {t}!"
        if np.isnan(orig_vol):
            assert np.isnan(pert_vol)
        else:
            assert pytest.approx(orig_vol, abs=1e-5) == pert_vol, f"Vol feature changed at index {t} due to future data!"
