"""Pure functions for computing returns and level changes.

Non-negotiable quant rule: Never average or conflate percentage returns with basis point (bp)
or point level changes. Metric types are strictly separated.
"""

from typing import Literal
import numpy as np
import pandas as pd

ReturnMethod = Literal["simple", "log"]
MetricType = Literal["return", "level_change"]


def calculate_returns(
    series: pd.Series,
    metric_type: MetricType = "return",
    method: ReturnMethod = "simple",
    unit: str = "%",
) -> pd.Series:
    """Calculate asset periodic returns or level changes.

    Args:
        series: Pandas Series indexed by trade date with price or yield levels.
        metric_type: 'return' for equities, ETFs, FX, commodities.
                     'level_change' for yields and volatility indices.
        method: 'simple' (P_t / P_{t-1} - 1) or 'log' (ln(P_t / P_{t-1})).
        unit: Unit of measure ('%', 'bp', 'points').
              If metric_type == 'level_change' and unit == 'bp', yield differences
              are multiplied by 100 (e.g. 0.05% -> 5 bp).

    Returns:
        Pandas Series of periodic changes or returns.
    """
    if series.empty:
        return pd.Series(dtype=float)

    if metric_type == "level_change":
        diff = series.diff()
        if unit == "bp":
            return diff * 100.0
        return diff

    if method == "log":
        # Guard against zero or negative prices
        valid_mask = series > 0
        log_series = pd.Series(index=series.index, dtype=float)
        log_series[valid_mask] = np.log(series[valid_mask])
        return log_series.diff()

    # Default: simple return
    return series.pct_change()
