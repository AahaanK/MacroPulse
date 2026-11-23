"""Cross-asset correlation matrix and risk-on / risk-off regime interpretation rules."""

import numpy as np
import pandas as pd


def compute_cross_asset_correlations(
    returns_df: pd.DataFrame,  # columns: [symbol1, symbol2, ...]
    event_dates: set,  # set of datetime.date
) -> dict:
    """Compute correlation matrices separately for normal days vs event announcement days."""
    dates = [d.date() if hasattr(d, "date") else d for d in returns_df.index]
    is_event = np.array([d in event_dates for d in dates])

    event_subset = returns_df.iloc[is_event]
    normal_subset = returns_df.iloc[~is_event]

    normal_corr = normal_subset.corr().round(3).fillna(0.0)
    event_corr = event_subset.corr().round(3).fillna(0.0)

    # Pre/Post volatility ratio around events (5 days post vs 5 days pre)
    symbols = returns_df.columns.tolist()

    return {
        "symbols": symbols,
        "normal_correlation": normal_corr.to_dict(),
        "event_correlation": event_corr.to_dict(),
        "n_normal_days": len(normal_subset),
        "n_event_days": len(event_subset),
    }


def interpret_risk_regime(
    mean_cars: dict[str, float],  # symbol -> mean CAR
) -> dict:
    """Apply deterministic quantitative rule to interpret event market sentiment.

    Rule: 'Asset Class Divergence Rule (Equities vs. Safe Havens)'
    """
    spy_car = mean_cars.get("SPY", 0.0)
    qqq_car = mean_cars.get("QQQ", 0.0)
    tlt_car = mean_cars.get("TLT", 0.0)
    vix_car = mean_cars.get("^VIX", 0.0)
    gld_car = mean_cars.get("GLD", 0.0)

    equity_avg = (spy_car + qqq_car) / 2.0

    if equity_avg > 0.25 and vix_car <= 0.0 and tlt_car <= 0.2:
        regime = "Risk-On (Equities Rally, Volatility Subdued)"
        explanation = (
            f"Equities reacted positively (mean {equity_avg:+.2f}%) while safe-haven volatility "
            f"and long bonds remained contained (^VIX: {vix_car:+.2f} pts, TLT: {tlt_car:+.2f}%). "
            f"Quant Rule: Equity CAR > +0.25% with non-positive VIX delta."
        )
    elif equity_avg < -0.25 and (vix_car > 0.0 or gld_car > 0.1 or tlt_car > 0.1):
        regime = "Risk-Off (Flight to Safe Havens)"
        explanation = (
            f"Equities contracted (mean {equity_avg:+.2f}%) accompanied by flight-to-safety flows "
            f"(^VIX: {vix_car:+.2f} pts, Gold: {gld_car:+.2f}%, TLT: {tlt_car:+.2f}%). "
            f"Quant Rule: Equity CAR < -0.25% with safe-haven appreciation."
        )
    else:
        regime = "Mixed / Sector-Divergent"
        explanation = (
            f"Asset classes showed mixed responses without unanimous risk-on or risk-off alignment "
            f"(SPY: {spy_car:+.2f}%, TLT: {tlt_car:+.2f}%, ^VIX: {vix_car:+.2f} pts). "
            f"Quant Rule: Conflicting signals between equities and hedge assets."
        )

    return {
        "rule_name": "Asset Class Divergence Rule (Equities vs Safe Havens)",
        "regime": regime,
        "explanation": explanation,
    }
