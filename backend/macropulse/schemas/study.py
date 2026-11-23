import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class EventStudyRequest(BaseModel):
    """Specification for running an event study."""

    event_type: str = Field(default="CPI", description="Economic announcement type, e.g. CPI, FOMC, NFP")
    asset_symbol: str = Field(default="SPY", description="Target financial instrument proxy symbol")
    benchmark_symbol: str | None = Field(default="SPY", description="Market benchmark symbol (e.g. SPY)")
    start_date: datetime.date | None = Field(default=None, description="Event filter start date")
    end_date: datetime.date | None = Field(default=None, description="Event filter end date")
    event_window: list[int] = Field(default=[-1, 3], description="Event window offsets [tau_start, tau_end]")
    estimation_window: list[int] = Field(default=[-260, -11], description="Estimation window offsets [est_start, est_end]")
    return_method: Literal["simple", "log"] = Field(default="simple", description="Return calculation method")
    model_type: Literal["mean_adjusted", "market_adjusted", "market_model"] = Field(
        default="market_adjusted", description="Expected return model"
    )
    use_first_release: bool = Field(
        default=True, description="Use first-release vintage values to avoid look-ahead bias"
    )
    exclude_overlapping: bool = Field(default=False, description="Exclude adjacent overlapping event windows")
    seed: int = Field(default=42, description="Random seed for bootstrap reproducibility")

    @model_validator(mode="after")
    def validate_windows(self):
        if len(self.event_window) != 2:
            raise ValueError("event_window must have exactly 2 integers [tau_start, tau_end].")
        if self.event_window[0] > self.event_window[1]:
            raise ValueError("event_window tau_start must be <= tau_end.")
        if len(self.estimation_window) != 2:
            raise ValueError("estimation_window must have exactly 2 integers [est_start, est_end].")
        if self.estimation_window[0] >= self.estimation_window[1]:
            raise ValueError("estimation_window est_start must be < est_end.")
        if self.estimation_window[1] >= self.event_window[0]:
            raise ValueError("estimation_window must end before event_window begins (gap required to avoid contamination).")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date.")
        return self


class AARPointSchema(BaseModel):
    tau: int
    aar: float
    aar_std: float
    aar_se: float
    ci_lower: float
    ci_upper: float
    caar: float
    caar_bootstrap_lower: float
    caar_bootstrap_upper: float


class EventAbnormalReturnSchema(BaseModel):
    event_id: int | str
    event_type: str
    period_date: str
    release_ts: str
    day_0_date: str
    is_intraday_release: bool
    is_overlapping: bool
    tau_returns: dict[int, float]
    tau_expected: dict[int, float]
    tau_ar: dict[int, float]
    tau_car: dict[int, float]
    window_cars: dict[str, float]
    window_scars: dict[str, float]
    model_alpha: float
    model_beta: float
    model_r2: float


class WindowStatsSchema(BaseModel):
    window: list[int]
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
    bmp_stat: float | None
    p_value_bmp: float | None
    sign_stat_positive: int
    sign_stat_negative: int
    p_value_sign: float
    wilcoxon_stat: float | None
    p_value_wilcoxon: float | None
    bootstrap_ci_lower: float
    bootstrap_ci_upper: float
    effect_size_d: float
    effect_size_band: str
    verdict: str
    caveats: list[str]


class ExcludedEventSchema(BaseModel):
    event_id: int | str
    event_type: str
    period_date: str
    release_ts: str
    reason: str


class EventStudyResponse(BaseModel):
    """Full serialized event study result."""

    study_id: int | None = None
    config_hash: str
    input_fingerprint: str
    app_version: str
    is_demo: bool
    config: dict
    n_included: int
    n_excluded: int
    event_type: str
    asset_symbol: str
    benchmark_symbol: str | None
    metric_type: str
    unit: str
    aar_series: list[AARPointSchema]
    per_event: list[EventAbnormalReturnSchema]
    window_stats: dict[str, WindowStatsSchema]
    excluded_events: list[ExcludedEventSchema]
    primary_window: str
    primary_verdict: str
    created_at: str
