"""Pure event-study engine for computing AR, CAR, AAR, CAAR and full statistical summaries.

No database or HTTP dependencies. Fully testable with deterministic fixtures.
"""

from dataclasses import asdict, dataclass
import datetime
import hashlib
import json
import numpy as np
import pandas as pd

from macropulse.analytics.alignment import AlignedEventWindow, ExcludedEvent, NYSECalendarAligner
from macropulse.analytics.models import (
    ModelFit,
    ModelType,
    calculate_forecast_std_error,
    fit_expected_return_model,
    predict_expected_return,
)
from macropulse.analytics.returns import MetricType, ReturnMethod, calculate_returns
from macropulse.analytics.stats import WindowStats, compute_bootstrap_ci, compute_window_statistics


@dataclass
class EventAbnormalReturn:
    """Individual event reaction series across the event window."""

    event_id: int | str
    event_type: str
    period_date: str
    release_ts: str
    day_0_date: str
    is_intraday_release: bool
    is_overlapping: bool
    tau_returns: dict[int, float]  # tau -> raw return
    tau_expected: dict[int, float]  # tau -> expected return
    tau_ar: dict[int, float]  # tau -> AR
    tau_car: dict[int, float]  # tau -> CAR from tau_start to tau
    window_cars: dict[str, float]  # "[t1,t2]" -> CAR
    window_scars: dict[str, float]  # "[t1,t2]" -> standardized CAR (BMP)
    model_alpha: float
    model_beta: float
    model_r2: float


@dataclass
class AARPoint:
    """Cross-sectional average abnormal return for a specific event-window offset tau."""

    tau: int
    aar: float
    aar_std: float
    aar_se: float
    ci_lower: float
    ci_upper: float
    caar: float
    caar_bootstrap_lower: float
    caar_bootstrap_upper: float


@dataclass
class EventStudyResult:
    """Complete output of an event study run."""

    config: dict
    input_fingerprint: str
    n_included: int
    n_excluded: int
    event_type: str
    asset_symbol: str
    benchmark_symbol: str | None
    metric_type: str
    unit: str
    aar_series: list[AARPoint]
    per_event: list[EventAbnormalReturn]
    window_stats: dict[str, WindowStats]
    excluded_events: list[dict]
    primary_window: str
    primary_verdict: str


def run_event_study(
    events: list[dict],
    asset_prices: pd.Series,  # indexed by datetime.date
    benchmark_prices: pd.Series | None = None,  # indexed by datetime.date
    metric_type: MetricType = "return",
    return_method: ReturnMethod = "simple",
    unit: str = "%",
    model_type: ModelType = "market_adjusted",
    event_window: tuple[int, int] = (-1, 3),
    estimation_window: tuple[int, int] = (-260, -11),
    min_estimation_obs: int = 120,
    exclude_overlapping: bool = False,
    seed: int = 42,
    asset_symbol: str = "SPY",
    benchmark_symbol: str | None = "SPY",
) -> EventStudyResult:
    """Run full daily event study on historical event and price data."""
    # 1. Compute returns or level changes
    asset_returns = calculate_returns(asset_prices, metric_type=metric_type, method=return_method, unit=unit).dropna()
    # calculate_returns yields decimal fractions (0.012 = 1.2%). Results for return-type
    # assets are reported with unit "%", so express them in percentage points here.
    # Without this, a 1.2% move was displayed as "0.01%" across the UI and reports.
    pct_scale = 100.0 if (metric_type == "return" and unit == "%") else 1.0
    asset_returns = asset_returns * pct_scale
    benchmark_returns = None
    if benchmark_prices is not None and not benchmark_prices.empty:
        benchmark_returns = (
            calculate_returns(benchmark_prices, metric_type="return", method=return_method, unit="%").dropna()
            * pct_scale
        )

    available_dates = set(asset_returns.index)
    if benchmark_returns is not None:
        available_dates = available_dates.intersection(set(benchmark_returns.index))

    # 2. Align events using NYSE calendar
    aligner = NYSECalendarAligner()
    included_windows, excluded_records = aligner.build_event_windows(
        events=events,
        available_price_dates=available_dates,
        event_window=event_window,
        estimation_window=estimation_window,
        min_estimation_obs=min_estimation_obs,
        exclude_overlapping=exclude_overlapping,
    )

    tau_start, tau_end = event_window
    per_event_results: list[EventAbnormalReturn] = []

    # Windows to compute statistics for
    stat_windows = [
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
        (-1, 1),
        (-1, 3),
        (tau_start, tau_end),
    ]
    # Deduplicate windows while preserving order
    unique_windows = []
    for w in stat_windows:
        if w[0] >= tau_start and w[1] <= tau_end and w not in unique_windows:
            unique_windows.append(w)

    has_any_overlap = any(w.is_overlapping for w in included_windows)

    # 3. Process each event
    for w in included_windows:
        est_asset = asset_returns.loc[w.estimation_dates]
        est_bm = benchmark_returns.loc[w.estimation_dates] if benchmark_returns is not None else None

        try:
            fit = fit_expected_return_model(est_asset, est_bm, model_type=model_type)
        except Exception as e:
            excluded_records.append(
                ExcludedEvent(w.event_id, w.event_type, w.period_date, w.release_ts, f"model_fit_failure: {e}")
            )
            continue

        tau_ret: dict[int, float] = {}
        tau_exp: dict[int, float] = {}
        tau_ar: dict[int, float] = {}
        tau_car: dict[int, float] = {}
        tau_sar: dict[int, float] = {}

        cum_ar = 0.0
        for tau in range(tau_start, tau_end + 1):
            t_date = w.event_window_tau_dates[tau]
            r_val = float(asset_returns.loc[t_date])
            bm_val = float(benchmark_returns.loc[t_date]) if benchmark_returns is not None else 0.0

            exp_val = predict_expected_return(fit, bm_val)
            ar_val = r_val - exp_val
            cum_ar += ar_val

            se_forecast = calculate_forecast_std_error(fit, bm_val)
            sar_val = ar_val / se_forecast if se_forecast > 0 else 0.0

            tau_ret[tau] = round(r_val, 4)
            tau_exp[tau] = round(exp_val, 4)
            tau_ar[tau] = round(ar_val, 4)
            tau_car[tau] = round(cum_ar, 4)
            tau_sar[tau] = sar_val

        window_cars = {}
        window_scars = {}
        for w_span in unique_windows:
            w_key = f"[{w_span[0]:+d},{w_span[1]:+d}]"
            w_car = sum(tau_ar[t] for t in range(w_span[0], w_span[1] + 1))
            window_cars[w_key] = round(w_car, 4)

            # SCAR for BMP test
            L = w_span[1] - w_span[0] + 1
            w_scar = sum(tau_sar[t] for t in range(w_span[0], w_span[1] + 1)) / np.sqrt(L)
            window_scars[w_key] = round(float(w_scar), 4)

        per_event_results.append(
            EventAbnormalReturn(
                event_id=w.event_id,
                event_type=w.event_type,
                period_date=w.period_date.isoformat(),
                release_ts=w.release_ts.isoformat(),
                day_0_date=w.day_0_date.isoformat(),
                is_intraday_release=w.is_intraday_release,
                is_overlapping=w.is_overlapping,
                tau_returns=tau_ret,
                tau_expected=tau_exp,
                tau_ar=tau_ar,
                tau_car=tau_car,
                window_cars=window_cars,
                window_scars=window_scars,
                model_alpha=round(fit.alpha, 6),
                model_beta=round(fit.beta, 4),
                model_r2=round(fit.r_squared, 4),
            )
        )

    # 4. Compute AAR and CAAR across events
    aar_series: list[AARPoint] = []
    n_inc = len(per_event_results)

    running_caar = 0.0
    for tau in range(tau_start, tau_end + 1):
        if n_inc > 0:
            tau_ars = np.array([ev.tau_ar[tau] for ev in per_event_results], dtype=float)
            tau_cars = np.array([ev.tau_car[tau] for ev in per_event_results], dtype=float)
            aar_val = float(np.mean(tau_ars))
            std_val = float(np.std(tau_ars, ddof=1)) if n_inc > 1 else 0.0
            se_val = std_val / np.sqrt(n_inc) if n_inc > 0 else 0.0
            ci_low = aar_val - 1.96 * se_val
            ci_high = aar_val + 1.96 * se_val
            running_caar += aar_val

            # Bootstrap band for CAAR
            b_low, b_high = compute_bootstrap_ci(tau_cars, n_resamples=5000, seed=seed + tau)
        else:
            aar_val, std_val, se_val, ci_low, ci_high = 0.0, 0.0, 0.0, 0.0, 0.0
            b_low, b_high = 0.0, 0.0

        aar_series.append(
            AARPoint(
                tau=tau,
                aar=round(aar_val, 4),
                aar_std=round(std_val, 4),
                aar_se=round(se_val, 4),
                ci_lower=round(ci_low, 4),
                ci_upper=round(ci_high, 4),
                caar=round(running_caar, 4),
                caar_bootstrap_lower=round(b_low, 4),
                caar_bootstrap_upper=round(b_high, 4),
            )
        )

    # 5. Compute Window Statistics
    window_stats_map: dict[str, WindowStats] = {}
    test_count = len(unique_windows)
    for w_span in unique_windows:
        w_key = f"[{w_span[0]:+d},{w_span[1]:+d}]"
        car_vals = [ev.window_cars[w_key] for ev in per_event_results]
        scar_vals = [ev.window_scars[w_key] for ev in per_event_results] if model_type == "market_model" else None

        w_stat = compute_window_statistics(
            car_values=car_vals,
            standardized_cars=scar_vals,
            window=w_span,
            event_type=events[0]["event_type"] if events else "MACRO",
            asset_symbol=asset_symbol,
            unit=unit,
            seed=seed,
            has_overlaps=has_any_overlap,
            test_count=test_count,
        )
        window_stats_map[w_key] = w_stat

    primary_key = f"[{0:+d},{1:+d}]" if f"[{0:+d},{1:+d}]" in window_stats_map else f"[{tau_start:+d},{tau_end:+d}]"
    primary_verdict = window_stats_map[primary_key].verdict if primary_key in window_stats_map else "No results."

    # Compute config fingerprint
    config_dict = {
        "event_type": events[0]["event_type"] if events else "UNKNOWN",
        "asset_symbol": asset_symbol,
        "benchmark_symbol": benchmark_symbol,
        "metric_type": metric_type,
        "return_method": return_method,
        "model_type": model_type,
        "event_window": list(event_window),
        "estimation_window": list(estimation_window),
        "min_estimation_obs": min_estimation_obs,
        "exclude_overlapping": exclude_overlapping,
        "seed": seed,
    }
    input_fp = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    excluded_list = [
        {
            "event_id": ex.event_id,
            "event_type": ex.event_type,
            "period_date": ex.period_date.isoformat(),
            "release_ts": ex.release_ts.isoformat(),
            "reason": ex.reason,
        }
        for ex in excluded_records
    ]

    return EventStudyResult(
        config=config_dict,
        input_fingerprint=input_fp,
        n_included=len(per_event_results),
        n_excluded=len(excluded_records),
        event_type=events[0]["event_type"] if events else "UNKNOWN",
        asset_symbol=asset_symbol,
        benchmark_symbol=benchmark_symbol,
        metric_type=metric_type,
        unit=unit,
        aar_series=aar_series,
        per_event=per_event_results,
        window_stats=window_stats_map,
        excluded_events=excluded_list,
        primary_window=primary_key,
        primary_verdict=primary_verdict,
    )
