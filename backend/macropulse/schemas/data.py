import datetime
from pydantic import BaseModel


class DataSourceSchema(BaseModel):
    id: int
    name: str
    kind: str
    base_url: str | None
    license_note: str | None
    is_demo: bool


class IndicatorSchema(BaseModel):
    id: int
    code: str
    fred_series_id: str
    name: str
    units: str
    frequency: str
    transform: str | None
    release_time_et: str
    source_id: int
    latest_value: float | None = None
    latest_period: str | None = None
    previous_value: float | None = None
    abs_change: float | None = None
    pct_change: float | None = None
    freshness_days: int | None = None
    sparkline: list[float] = []


class AssetSchema(BaseModel):
    id: int
    symbol: str
    name: str
    asset_class: str
    metric_type: str
    unit: str
    provider: str
    proxy_note: str | None


class EconomicEventSchema(BaseModel):
    id: int
    event_type: str
    indicator_id: int | None
    country: str
    period_date: str
    release_ts: str
    timestamp_source: str
    actual_first_release: float
    previous_first_release: float | None
    actual_latest: float | None
    change_value: float | None
    change_std: float | None
    data_quality: str
    source_id: int
    has_consensus: bool = False
    consensus_value: float | None = None


class DataStatusSummary(BaseModel):
    is_live_mode: bool
    data_mode: str  # "LIVE" or "DEMO"
    banner_message: str | None
    total_assets: int
    total_indicators: int
    total_events: int
    total_prices: int
    last_ingestion_time: str | None
    last_ingestion_status: str | None
    series_coverage: list[dict]
    disabled_modes: list[dict]
