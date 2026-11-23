"""Market regime classification models with strict no look-ahead enforcement."""

import datetime
from typing import Literal
import numpy as np
import pandas as pd

RegimeLabel = Literal["High Vol / Risk-Off", "Low Vol / Risk-On", "Transitional / unclassified"]


def classify_market_regimes(
    prices_df: pd.DataFrame,  # columns: ['trade_date', 'close', 'adj_close']
    vix_df: pd.DataFrame | None = None,  # columns: ['trade_date', 'close']
    vol_percentile_cutoff: float = 70.0,
    vix_high_cutoff: float = 22.0,
    vix_low_cutoff: float = 16.0,
) -> pd.DataFrame:
    """Classify daily market regimes strictly using data available up to t - 1.

    Zero look-ahead guarantee:
    All features (21-day realized vol, 50-day SMA, 200-day SMA, VIX level) are shifted by 1 day
    so that the regime at day t is known before market open on day t.

    Rules:
    - High Vol / Risk-Off: 21d realized vol percentile >= 70% AND (VIX >= 22 OR 50d SMA < 200d SMA)
    - Low Vol / Risk-On: 21d realized vol percentile <= 40% AND VIX <= 16 AND 50d SMA > 200d SMA
    - Otherwise: 'Transitional / unclassified' (when signals conflict or sit in intermediate zones)
    """
    df = prices_df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df.sort_values("trade_date", inplace=True)
    df.set_index("trade_date", inplace=True)

    # 1. Compute daily returns
    daily_returns = df["adj_close"].pct_change()

    # 2. Compute 21-day annualized realized volatility: std * sqrt(252)
    # CRITICAL: Shift by 1 trading day so day t's feature uses only observations <= t - 1!
    hist_returns_lagged = daily_returns.shift(1)
    rolling_21d_vol = hist_returns_lagged.rolling(window=21, min_periods=15).std() * np.sqrt(252) * 100.0

    # Rolling expanding percentile of realized volatility
    rolling_vol_rank = rolling_21d_vol.expanding(min_periods=60).apply(
        lambda s: float(stats_percentile_rank(s)), raw=True
    )

    # 3. Moving average trend (50-day vs 200-day SMA, shifted by 1 day)
    lagged_price = df["adj_close"].shift(1)
    sma_50 = lagged_price.rolling(window=50, min_periods=40).mean()
    sma_200 = lagged_price.rolling(window=200, min_periods=150).mean()
    bullish_trend = sma_50 > sma_200

    # 4. VIX level (lagged by 1 day)
    vix_series = None
    if vix_df is not None and not vix_df.empty:
        v_df = vix_df.copy()
        v_df["trade_date"] = pd.to_datetime(v_df["trade_date"])
        v_df.sort_values("trade_date", inplace=True)
        v_df.set_index("trade_date", inplace=True)
        vix_series = v_df["close"].shift(1).reindex(df.index).ffill()

    labels = []
    features = []

    for dt in df.index:
        pct_rank = rolling_vol_rank.loc[dt] if dt in rolling_vol_rank else np.nan
        trend_ok = bullish_trend.loc[dt] if dt in bullish_trend else None
        vix_val = vix_series.loc[dt] if vix_series is not None and dt in vix_series else 18.0

        if pd.isna(pct_rank):
            label = "Transitional / unclassified"
            conf = 0.5
        elif pct_rank >= vol_percentile_cutoff and (vix_val >= vix_high_cutoff or trend_ok is False):
            label = "High Vol / Risk-Off"
            conf = min(1.0, 0.5 + (pct_rank - vol_percentile_cutoff) / 60.0)
        elif pct_rank <= (vol_percentile_cutoff - 30.0) and vix_val <= vix_low_cutoff and trend_ok is True:
            label = "Low Vol / Risk-On"
            conf = min(1.0, 0.5 + (40.0 - pct_rank) / 60.0)
        else:
            label = "Transitional / unclassified"
            conf = 0.6

        labels.append(label)
        features.append({
            "vol_21d": round(float(rolling_21d_vol.get(dt, 0.0) or 0.0), 2),
            "vol_percentile": round(float(pct_rank or 50.0), 1),
            "vix": round(float(vix_val or 18.0), 2),
            "bullish_trend": bool(trend_ok) if trend_ok is not None else False,
        })

    result_df = pd.DataFrame(
        {
            "trade_date": [d.date() for d in df.index],
            "label": labels,
            "feature_json": features,
        }
    )
    return result_df


def stats_percentile_rank(arr: np.ndarray) -> float:
    """Calculate percentile rank of the last element within historical window."""
    last_val = arr[-1]
    valid = arr[~np.isnan(arr)]
    if len(valid) == 0 or np.isnan(last_val):
        return 50.0
    return float(np.sum(valid <= last_val) / len(valid) * 100.0)
