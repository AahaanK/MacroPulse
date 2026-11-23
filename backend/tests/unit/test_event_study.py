"""Unit test running the full event study engine on a hand-verified 3-event toy panel."""

import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import pytest

from macropulse.analytics.event_study import run_event_study


def test_event_study_toy_panel():
    """Verify AR, CAR, AAR, CAAR on a 3-event toy panel.

    Setup:
    - 3 events spaced across 2023.
    - Market adjusted model: E[R_i,t] = R_m,t.
    - Event window [-1, +1] (3 days: tau=-1, 0, +1).
    - Event 1:
        tau=-1: Asset = +1.0%, Bench = +0.5% -> AR = +0.5%
        tau= 0: Asset = +2.0%, Bench = +0.0% -> AR = +2.0%
        tau=+1: Asset = -1.0%, Bench = -0.5% -> AR = -0.5%
        CAR[-1,1] = 0.5 + 2.0 - 0.5 = +2.0%
        CAR[0,1]  = 2.0 - 0.5 = +1.5%

    - Event 2:
        tau=-1: Asset = +0.2%, Bench = +0.2% -> AR = 0.0%
        tau= 0: Asset = +1.0%, Bench = +0.0% -> AR = +1.0%
        tau=+1: Asset = +0.5%, Bench = +0.0% -> AR = +0.5%
        CAR[-1,1] = 0.0 + 1.0 + 0.5 = +1.5%
        CAR[0,1]  = 1.0 + 0.5 = +1.5%

    - Event 3:
        tau=-1: Asset = -0.5%, Bench = 0.0%  -> AR = -0.5%
        tau= 0: Asset = 0.0%,  Bench = 0.0%  -> AR = 0.0%
        tau=+1: Asset = +1.0%, Bench = 0.0%  -> AR = +1.0%
        CAR[-1,1] = -0.5 + 0.0 + 1.0 = +0.5%
        CAR[0,1]  = 0.0 + 1.0 = +1.0%

    Cross-sectional AAR:
        tau=-1: mean(0.5, 0.0, -0.5) = 0.0%
        tau= 0: mean(2.0, 1.0, 0.0)  = +1.0%
        tau=+1: mean(-0.5, 0.5, 1.0) = +0.3333%

    CAAR from tau=-1:
        tau=-1: 0.0%
        tau= 0: 0.0 + 1.0 = +1.0%
        tau=+1: 1.0 + 0.3333 = +1.3333%

    Window CAR[0,1] across 3 events:
        [1.5%, 1.5%, 1.0%] -> mean = 1.3333%
    """
    # Create calendar dates covering 2023
    from macropulse.analytics.alignment import NYSECalendarAligner
    aligner = NYSECalendarAligner(start_date="2023-01-01", end_date="2023-12-31")
    trading_dates = aligner.trading_days

    # Pick 3 event dates separated by at least 40 trading days
    ev_dates = [trading_dates[30], trading_dates[80], trading_dates[130]]
    events = [
        {
            "id": i + 1,
            "event_type": "CPI",
            "period_date": d,
            "release_ts": datetime.datetime(d.year, d.month, d.day, 8, 30, tzinfo=ZoneInfo("America/New_York")),
        }
        for i, d in enumerate(ev_dates)
    ]

    # Generate synthetic price series such that returns match our toy panel
    # We construct daily prices where for non-event days return is 0,
    # and on event window days it matches our specified values.
    # Start price = 100.0
    p_asset = {}
    p_bench = {}
    cur_pa = 100.0
    cur_pb = 100.0

    # Map event window indices
    ev_tau_map_a = {
        0: {-1: 0.010, 0: 0.020, 1: -0.010},
        1: {-1: 0.002, 0: 0.010, 1: 0.005},
        2: {-1: -0.005, 0: 0.000, 1: 0.010},
    }
    ev_tau_map_b = {
        0: {-1: 0.005, 0: 0.000, 1: -0.005},
        1: {-1: 0.002, 0: 0.000, 1: 0.000},
        2: {-1: 0.000, 0: 0.000, 1: 0.000},
    }

    # Set initial prices
    for i, d in enumerate(trading_dates):
        # Check if d is in any event window [-1, 1]
        ret_a = 0.0005  # tiny baseline
        ret_b = 0.0005

        for ev_idx, ev_d in enumerate(ev_dates):
            ev_cal_idx = aligner._date_to_index[ev_d]
            tau = i - ev_cal_idx
            if tau in ev_tau_map_a[ev_idx]:
                ret_a = ev_tau_map_a[ev_idx][tau]
                ret_b = ev_tau_map_b[ev_idx][tau]

        cur_pa *= (1.0 + ret_a)
        cur_pb *= (1.0 + ret_b)
        p_asset[d] = cur_pa
        p_bench[d] = cur_pb

    s_asset = pd.Series(p_asset)
    s_bench = pd.Series(p_bench)

    res = run_event_study(
        events=events,
        asset_prices=s_asset,
        benchmark_prices=s_bench,
        metric_type="return",
        return_method="simple",
        model_type="market_adjusted",
        event_window=(-1, 1),
        estimation_window=(-25, -2),  # short estimation window for toy test
        min_estimation_obs=15,
        seed=42,
    )

    assert res.n_included == 3
    assert res.n_excluded == 0

    # Results are in percentage points (unit "%"), matching the docstring above.
    # Verify AAR points
    tau_neg1 = next(p for p in res.aar_series if p.tau == -1)
    tau_0 = next(p for p in res.aar_series if p.tau == 0)
    tau_pos1 = next(p for p in res.aar_series if p.tau == 1)

    assert pytest.approx(tau_neg1.aar, abs=1e-2) == 0.0
    assert pytest.approx(tau_0.aar, abs=1e-2) == 1.0
    assert pytest.approx(tau_pos1.aar, abs=1e-2) == 0.3333

    # Verify CAAR points
    assert pytest.approx(tau_neg1.caar, abs=1e-2) == 0.0
    assert pytest.approx(tau_0.caar, abs=1e-2) == 1.0
    assert pytest.approx(tau_pos1.caar, abs=1e-2) == 1.3333

    # Check Window stats for [0, 1]
    stat_01 = res.window_stats.get("[+0,+1]")
    assert stat_01 is not None
    assert pytest.approx(stat_01.mean_car, abs=1e-2) == 1.3333
