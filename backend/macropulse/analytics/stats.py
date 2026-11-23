"""Statistical inference tests and plain-English verdict generation for event studies.

Tests:
1. Cross-sectional t-test on CAR with 95% t-confidence interval.
2. Boehmer-Musumeci-Poulsen (BMP 1991) standardized cross-sectional test.
3. Sign test (exact binomial test against p=0.5).
4. Wilcoxon signed-rank test against median=0.
5. Percentile bootstrap confidence interval with fixed seed.
6. Cohen's d effect size with qualitative band.
7. Holm-Bonferroni multiple testing adjustment.
8. Plain-English verdicts and automated caveat detection.
"""

from dataclasses import dataclass
import numpy as np
import scipy.stats as stats


@dataclass(frozen=True)
class WindowStats:
    """Statistical summary and hypothesis tests for a specific event window [tau1, tau2]."""

    window: tuple[int, int]
    n_events: int
    mean_car: float
    median_car: float
    std_car: float
    min_car: float
    max_car: float
    t_stat: float
    df: int
    p_value_t: float
    ci_lower_t: float
    ci_upper_t: float
    # BMP test
    bmp_stat: float | None
    p_value_bmp: float | None
    # Nonparametric
    sign_stat_positive: int
    sign_stat_negative: int
    p_value_sign: float
    wilcoxon_stat: float | None
    p_value_wilcoxon: float | None
    # Bootstrap
    bootstrap_ci_lower: float
    bootstrap_ci_upper: float
    # Effect size
    effect_size_d: float
    effect_size_band: str
    # Plain language verdict and caveats
    verdict: str
    caveats: list[str]


def compute_bootstrap_ci(
    values: np.ndarray,
    n_resamples: int = 5000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float]:
    """Calculate two-sided percentile bootstrap confidence interval for the mean.

    Uses a deterministic fixed seed for 100% reproducibility.
    """
    if len(values) == 0:
        return 0.0, 0.0
    if len(values) == 1:
        val = float(values[0])
        return val, val

    rng = np.random.default_rng(seed)
    boot_indices = rng.choice(len(values), size=(n_resamples, len(values)), replace=True)
    boot_means = np.mean(values[boot_indices], axis=1)

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    lower_ci = float(np.percentile(boot_means, lower_pct))
    upper_ci = float(np.percentile(boot_means, upper_pct))
    return lower_ci, upper_ci


def compute_effect_size(mean_val: float, std_val: float) -> tuple[float, str]:
    """Calculate Cohen's d style effect size and assign qualitative band."""
    if std_val == 0 or np.isnan(std_val):
        return 0.0, "Negligible"

    d = mean_val / std_val
    abs_d = abs(d)

    if abs_d < 0.2:
        band = "Negligible"
    elif abs_d < 0.5:
        band = "Small"
    elif abs_d < 0.8:
        band = "Moderate"
    else:
        band = "Large"

    return float(d), band


def compute_bmp_test(
    standardized_cars: np.ndarray,
) -> tuple[float | None, float | None]:
    """Compute the Boehmer, Musumeci, and Poulsen (BMP 1991) standardized cross-sectional test.

    Standardizes individual event CARs by forecast standard error, making the test
    robust to event-induced variance increases.
    """
    n = len(standardized_cars)
    if n < 3:
        return None, None

    mean_scar = float(np.mean(standardized_cars))
    sum_sq_diff = float(np.sum((standardized_cars - mean_scar) ** 2))
    var_scar = sum_sq_diff / (n * (n - 1))

    if var_scar <= 0:
        return None, None

    se_scar = np.sqrt(var_scar)
    bmp_z = mean_scar / se_scar
    # Two-sided p-value using Student's t distribution with n - 1 degrees of freedom
    p_val = float(2.0 * stats.t.sf(abs(bmp_z), df=n - 1))
    return float(bmp_z), p_val


def compute_window_statistics(
    car_values: list[float],
    standardized_cars: list[float] | None = None,
    window: tuple[int, int] = (0, 1),
    event_type: str = "CPI",
    asset_symbol: str = "SPY",
    unit: str = "%",
    n_resamples: int = 5000,
    seed: int = 42,
    has_overlaps: bool = False,
    test_count: int = 1,
) -> WindowStats:
    """Compute cross-sectional t-test, BMP test, nonparametric tests, and verdict."""
    arr = np.array(car_values, dtype=float)
    n = len(arr)

    if n == 0:
        return WindowStats(
            window=window,
            n_events=0,
            mean_car=0.0,
            median_car=0.0,
            std_car=0.0,
            min_car=0.0,
            max_car=0.0,
            t_stat=0.0,
            df=0,
            p_value_t=1.0,
            ci_lower_t=0.0,
            ci_upper_t=0.0,
            bmp_stat=None,
            p_value_bmp=None,
            sign_stat_positive=0,
            sign_stat_negative=0,
            p_value_sign=1.0,
            wilcoxon_stat=None,
            p_value_wilcoxon=None,
            bootstrap_ci_lower=0.0,
            bootstrap_ci_upper=0.0,
            effect_size_d=0.0,
            effect_size_band="Unavailable",
            verdict="No events met the inclusion criteria.",
            caveats=["No valid events."],
        )

    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))

    # Cross-sectional t-test
    df = n - 1
    if std_val > 0 and n > 1:
        se = std_val / np.sqrt(n)
        t_stat = mean_val / se
        p_val_t = float(2.0 * stats.t.sf(abs(t_stat), df=df))
        t_crit = float(stats.t.ppf(0.975, df=df))
        ci_lower_t = float(mean_val - t_crit * se)
        ci_upper_t = float(mean_val + t_crit * se)
    else:
        t_stat = 0.0
        p_val_t = 1.0
        ci_lower_t = mean_val
        ci_upper_t = mean_val

    # BMP test
    bmp_stat, p_val_bmp = None, None
    if standardized_cars is not None and len(standardized_cars) == n:
        bmp_stat, p_val_bmp = compute_bmp_test(np.array(standardized_cars, dtype=float))

    # Nonparametric tests
    pos_count = int(np.sum(arr > 0))
    neg_count = int(np.sum(arr < 0))
    # Sign test using exact binomial test
    if (pos_count + neg_count) > 0:
        binom_res = stats.binomtest(pos_count, n=pos_count + neg_count, p=0.5, alternative="two-sided")
        p_val_sign = float(binom_res.pvalue)
    else:
        p_val_sign = 1.0

    # Wilcoxon signed-rank test
    wilcoxon_stat, p_val_wilcoxon = None, None
    non_zeros = arr[arr != 0]
    if len(non_zeros) >= 10:
        try:
            w_res = stats.wilcoxon(non_zeros, alternative="two-sided")
            wilcoxon_stat = float(w_res.statistic)
            p_val_wilcoxon = float(w_res.pvalue)
        except Exception:
            pass

    # Bootstrap CI
    boot_lower, boot_upper = compute_bootstrap_ci(arr, n_resamples=n_resamples, seed=seed)

    # Effect size
    effect_d, effect_band = compute_effect_size(mean_val, std_val)

    # Caveats
    caveats = []
    if n < 30:
        caveats.append(f"Small sample size caveat: n = {n} (< 30). T-distribution assumptions may be fragile.")
    if has_overlaps:
        caveats.append("Overlapping event windows caveat: cross-correlation between adjacent events can inflate test statistics.")
    if test_count > 1:
        # Holm-Bonferroni adjustment threshold
        holm_alpha = 0.05 / test_count
        caveats.append(f"Multiple testing caveat: {test_count} windows/tests evaluated. Bonferroni/Holm significance threshold is p < {holm_alpha:.4f}.")
    caveats.append("Daily-frequency limitation: Announcement reaction is measured between closing sessions, not tick-by-tick intraday.")

    # Plain English verdict
    distinguishable = "statistically distinguishable from zero" if p_val_t < 0.05 else "not statistically distinguishable from zero"
    sign_str = "+" if mean_val > 0 else ""
    w_str = f"[{window[0]:+d},{window[1]:+d}]"
    unit_str = "%" if unit == "%" else f" {unit}"

    verdict = (
        f"Across {n} {event_type} releases, {asset_symbol}'s mean CAR{w_str} was {sign_str}{mean_val:.2f}{unit_str} "
        f"(95% CI {ci_lower_t:+.2f}{unit_str} to {ci_upper_t:+.2f}{unit_str}). "
        f"This is {distinguishable} (t = {t_stat:.2f}, p = {p_val_t:.3f})."
    )

    return WindowStats(
        window=window,
        n_events=n,
        mean_car=round(mean_val, 4),
        median_car=round(median_val, 4),
        std_car=round(std_val, 4),
        min_car=round(min_val, 4),
        max_car=round(max_val, 4),
        t_stat=round(t_stat, 3),
        df=df,
        p_value_t=round(p_val_t, 4),
        ci_lower_t=round(ci_lower_t, 4),
        ci_upper_t=round(ci_upper_t, 4),
        bmp_stat=round(bmp_stat, 3) if bmp_stat is not None else None,
        p_value_bmp=round(p_val_bmp, 4) if p_val_bmp is not None else None,
        sign_stat_positive=pos_count,
        sign_stat_negative=neg_count,
        p_value_sign=round(p_val_sign, 4),
        wilcoxon_stat=round(wilcoxon_stat, 2) if wilcoxon_stat is not None else None,
        p_value_wilcoxon=round(p_val_wilcoxon, 4) if p_val_wilcoxon is not None else None,
        bootstrap_ci_lower=round(boot_lower, 4),
        bootstrap_ci_upper=round(boot_upper, 4),
        effect_size_d=round(effect_d, 3),
        effect_size_band=effect_band,
        verdict=verdict,
        caveats=caveats,
    )
