"""Surprise analysis module: OLS sensitivity, quintile buckets, and positive/negative asymmetry tests."""

from dataclasses import dataclass
import numpy as np
import pandas as pd
import scipy.stats as stats


@dataclass(frozen=True)
class RegressionStats:
    slope: float
    intercept: float
    r_squared: float
    t_stat: float
    p_value: float
    se_slope: float
    ci_lower: float
    ci_upper: float


@dataclass(frozen=True)
class AsymmetryTestResult:
    pos_n: int
    neg_n: int
    pos_mean_car: float
    neg_mean_car: float
    welch_t_stat: float
    welch_p_value: float
    mann_whitney_u: float
    mann_whitney_p: float
    is_asymmetric: bool
    verdict: str


@dataclass(frozen=True)
class SurpriseAnalysisResult:
    mode: str  # "consensus_surprise" or "indicator_change"
    asset_symbol: str
    event_type: str
    data_points: list[dict]  # [{date, surprise, car, event_id}]
    regression: RegressionStats
    quintile_buckets: list[dict]  # [{bucket, min_x, max_x, mean_x, mean_car, count}]
    asymmetry: AsymmetryTestResult


def analyze_surprises(
    events: list[dict],
    event_cars: dict[int | str, float],
    asset_symbol: str = "SPY",
    unit: str = "%",
) -> SurpriseAnalysisResult:
    """Run regression and asymmetry tests on indicator change or consensus surprise."""
    has_consensus = any(ev.get("consensus_value") is not None for ev in events)
    mode = "consensus_surprise" if has_consensus else "indicator_change"

    points = []
    for ev in events:
        ev_id = ev["id"]
        car = event_cars.get(ev_id)
        if car is None:
            continue

        if mode == "consensus_surprise" and ev.get("consensus_value") is not None:
            surprise_val = ev["actual_first_release"] - ev["consensus_value"]
        else:
            # Indicator Change mode: actual_first_release - previous_first_release
            # Standardized by trailing std if available
            change_val = ev.get("change_value")
            if change_val is None:
                if ev.get("previous_first_release") is not None:
                    change_val = ev["actual_first_release"] - ev["previous_first_release"]
                else:
                    change_val = 0.0

            std_val = ev.get("change_std") or 1.0
            surprise_val = change_val / std_val if std_val > 0 else change_val

        points.append({
            "event_id": ev_id,
            "period_date": str(ev["period_date"]),
            "surprise": round(float(surprise_val), 4),
            "car": round(float(car), 4),
        })

    if len(points) < 3:
        raise ValueError(f"Insufficient paired events with CARs: {len(points)} < 3")

    x = np.array([p["surprise"] for p in points], dtype=float)
    y = np.array([p["car"] for p in points], dtype=float)
    n = len(x)

    # OLS Regression
    mean_x = float(np.mean(x))
    mean_y = float(np.mean(y))
    ss_x = float(np.sum((x - mean_x) ** 2))

    if ss_x == 0:
        slope = 0.0
        intercept = mean_y
        se_slope = 0.0
        t_stat = 0.0
        p_val = 1.0
        r2 = 0.0
        ci_lower = 0.0
        ci_upper = 0.0
    else:
        slope = float(np.sum((x - mean_x) * (y - mean_y)) / ss_x)
        intercept = mean_y - slope * mean_x
        y_pred = intercept + slope * x
        residuals = y - y_pred
        dof = max(n - 2, 1)
        s_eps = float(np.sqrt(np.sum(residuals ** 2) / dof))
        se_slope = float(s_eps / np.sqrt(ss_x))
        t_stat = float(slope / se_slope) if se_slope > 0 else 0.0
        p_val = float(2.0 * stats.t.sf(abs(t_stat), df=dof))

        ss_tot = float(np.sum((y - mean_y) ** 2))
        ss_res = float(np.sum(residuals ** 2))
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

        t_crit = float(stats.t.ppf(0.975, df=dof))
        ci_lower = float(slope - t_crit * se_slope)
        ci_upper = float(slope + t_crit * se_slope)

    reg_stats = RegressionStats(
        slope=round(slope, 4),
        intercept=round(intercept, 4),
        r_squared=round(max(0.0, r2), 4),
        t_stat=round(t_stat, 3),
        p_value=round(p_val, 4),
        se_slope=round(se_slope, 4),
        ci_lower=round(ci_lower, 4),
        ci_upper=round(ci_upper, 4),
    )

    # Quintile Buckets
    df_pts = pd.DataFrame(points)
    df_pts["bucket"] = pd.qcut(df_pts["surprise"], q=min(5, len(df_pts)), duplicates="drop")
    buckets = []
    for b_label, group in df_pts.groupby("bucket", observed=True):
        buckets.append({
            "bucket": str(b_label),
            "min_x": round(float(group["surprise"].min()), 3),
            "max_x": round(float(group["surprise"].max()), 3),
            "mean_x": round(float(group["surprise"].mean()), 3),
            "mean_car": round(float(group["car"].mean()), 4),
            "count": len(group),
        })

    # Asymmetry Test: Positive vs Negative Surprises
    pos_cars = y[x > 0]
    neg_cars = y[x < 0]

    pos_n = len(pos_cars)
    neg_n = len(neg_cars)
    pos_mean = float(np.mean(pos_cars)) if pos_n > 0 else 0.0
    neg_mean = float(np.mean(neg_cars)) if neg_n > 0 else 0.0

    if pos_n >= 2 and neg_n >= 2:
        # Welch's t-test (unequal variances)
        tt_res = stats.ttest_ind(pos_cars, neg_cars, equal_var=False)
        welch_t = float(tt_res.statistic)
        welch_p = float(tt_res.pvalue)

        # Mann-Whitney U test (nonparametric)
        u_res = stats.mannwhitneyu(pos_cars, neg_cars, alternative="two-sided")
        mw_u = float(u_res.statistic)
        mw_p = float(u_res.pvalue)
    else:
        welch_t, welch_p = 0.0, 1.0
        mw_u, mw_p = 0.0, 1.0

    is_asym = welch_p < 0.05
    asym_verdict = (
        f"Significant reaction asymmetry detected between positive ({pos_mean:+.2f}{unit}) and negative ({neg_mean:+.2f}{unit}) moves (Welch t = {welch_t:.2f}, p = {welch_p:.3f})."
        if is_asym
        else f"No statistically significant asymmetry detected between positive and negative indicator moves (p = {welch_p:.3f})."
    )

    asym_res = AsymmetryTestResult(
        pos_n=pos_n,
        neg_n=neg_n,
        pos_mean_car=round(pos_mean, 4),
        neg_mean_car=round(neg_mean, 4),
        welch_t_stat=round(welch_t, 3),
        welch_p_value=round(welch_p, 4),
        mann_whitney_u=round(mw_u, 2),
        mann_whitney_p=round(mw_p, 4),
        is_asymmetric=is_asym,
        verdict=asym_verdict,
    )

    return SurpriseAnalysisResult(
        mode=mode,
        asset_symbol=asset_symbol,
        event_type=events[0]["event_type"] if events else "MACRO",
        data_points=points,
        regression=reg_stats,
        quintile_buckets=buckets,
        asymmetry=asym_res,
    )
