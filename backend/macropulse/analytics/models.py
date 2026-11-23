"""Expected-return models for event-study abnormal return estimation.

Models implemented:
1. Mean-adjusted model: E[R_i,t] = mean(R_i,est)
2. Market-adjusted model: E[R_i,t] = R_m,t
3. Market model (OLS): R_i,t = alpha + beta * R_m,t + epsilon
"""

from dataclasses import dataclass
from typing import Literal
import numpy as np
import pandas as pd

ModelType = Literal["mean_adjusted", "market_adjusted", "market_model"]


@dataclass(frozen=True)
class ModelFit:
    """Estimated parameters and diagnostics from the estimation window."""

    model_type: ModelType
    n_obs: int
    alpha: float
    beta: float
    sigma_epsilon: float  # Residual standard error
    r_squared: float
    mean_benchmark: float = 0.0
    var_benchmark: float = 0.0
    sum_sq_diff_benchmark: float = 0.0


def fit_expected_return_model(
    asset_returns: pd.Series,
    benchmark_returns: pd.Series | None = None,
    model_type: ModelType = "market_adjusted",
) -> ModelFit:
    """Fit the expected return model on the estimation window.

    Args:
        asset_returns: Series of asset returns/changes over estimation window.
        benchmark_returns: Series of benchmark returns over estimation window (required for market and market_adjusted).
        model_type: 'mean_adjusted', 'market_adjusted', or 'market_model'.

    Returns:
        ModelFit with parameters, residual standard error, and diagnostics.
    """
    if asset_returns.empty:
        raise ValueError("Asset returns for estimation window cannot be empty.")

    n = len(asset_returns)

    if model_type == "mean_adjusted":
        mean_r = float(asset_returns.mean())
        residuals = asset_returns - mean_r
        dof = max(n - 1, 1)
        sigma_eps = float(np.sqrt(np.sum(residuals**2) / dof))
        return ModelFit(
            model_type=model_type,
            n_obs=n,
            alpha=mean_r,
            beta=0.0,
            sigma_epsilon=sigma_eps,
            r_squared=0.0,
        )

    if benchmark_returns is None or benchmark_returns.empty:
        raise ValueError(f"Benchmark returns are required for model_type '{model_type}'.")

    # Align on common dates
    common_idx = asset_returns.index.intersection(benchmark_returns.index)
    if len(common_idx) < 10:
        raise ValueError(f"Insufficient overlapping estimation observations: {len(common_idx)} < 10")

    y = asset_returns.loc[common_idx].to_numpy(dtype=float)
    x = benchmark_returns.loc[common_idx].to_numpy(dtype=float)
    n = len(y)

    mean_x = float(np.mean(x))
    mean_y = float(np.mean(y))
    sum_sq_diff_x = float(np.sum((x - mean_x) ** 2))
    var_x = sum_sq_diff_x / max(n - 1, 1)

    if model_type == "market_adjusted":
        # Assumes alpha = 0, beta = 1
        residuals = y - x
        dof = max(n - 1, 1)
        sigma_eps = float(np.sqrt(np.sum(residuals**2) / dof))
        ss_tot = float(np.sum((y - mean_y) ** 2))
        ss_res = float(np.sum(residuals**2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        return ModelFit(
            model_type=model_type,
            n_obs=n,
            alpha=0.0,
            beta=1.0,
            sigma_epsilon=sigma_eps,
            r_squared=max(0.0, r2),
            mean_benchmark=mean_x,
            var_benchmark=var_x,
            sum_sq_diff_benchmark=sum_sq_diff_x,
        )

    if model_type == "market_model":
        # OLS estimation: y = alpha + beta * x + eps
        if sum_sq_diff_x == 0:
            beta = 0.0
            alpha = mean_y
        else:
            covariance_xy = float(np.sum((x - mean_x) * (y - mean_y)))
            beta = covariance_xy / sum_sq_diff_x
            alpha = mean_y - beta * mean_x

        y_pred = alpha + beta * x
        residuals = y - y_pred
        dof = max(n - 2, 1)
        sigma_eps = float(np.sqrt(np.sum(residuals**2) / dof))

        ss_tot = float(np.sum((y - mean_y) ** 2))
        ss_res = float(np.sum(residuals**2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return ModelFit(
            model_type=model_type,
            n_obs=n,
            alpha=alpha,
            beta=beta,
            sigma_epsilon=sigma_eps,
            r_squared=max(0.0, r2),
            mean_benchmark=mean_x,
            var_benchmark=var_x,
            sum_sq_diff_benchmark=sum_sq_diff_x,
        )

    raise ValueError(f"Unknown model_type: {model_type}")


def predict_expected_return(
    fit: ModelFit,
    benchmark_value: float | None = None,
) -> float:
    """Predict expected normal return given model fit and benchmark value on event day."""
    if fit.model_type == "mean_adjusted":
        return fit.alpha
    if benchmark_value is None:
        raise ValueError(f"benchmark_value is required for {fit.model_type}")
    if fit.model_type == "market_adjusted":
        return benchmark_value
    # market_model
    return fit.alpha + fit.beta * benchmark_value


def calculate_forecast_std_error(
    fit: ModelFit,
    benchmark_value: float | None = None,
) -> float:
    """Compute the standard error of the forecast for BMP test standardization."""
    s_eps = fit.sigma_epsilon
    n = fit.n_obs
    if fit.model_type == "mean_adjusted":
        return float(s_eps * np.sqrt(1.0 + 1.0 / n))

    if benchmark_value is None or fit.sum_sq_diff_benchmark == 0:
        return float(s_eps * np.sqrt(1.0 + 1.0 / n))

    # Market model forecast variance adjustment
    diff_sq = (benchmark_value - fit.mean_benchmark) ** 2
    factor = 1.0 + (1.0 / n) + (diff_sq / fit.sum_sq_diff_benchmark)
    return float(s_eps * np.sqrt(max(1.0, factor)))
