export interface DataSource {
  id: number;
  name: string;
  kind: string;
  base_url: string | null;
  license_note: string | null;
  is_demo: boolean;
}

export interface Indicator {
  id: number;
  code: string;
  fred_series_id: string;
  name: string;
  units: string;
  frequency: string;
  transform: string | null;
  release_time_et: string;
  source_id: number;
  latest_value: number | null;
  latest_period: string | null;
  previous_value: number | null;
  abs_change: number | null;
  pct_change: number | null;
  freshness_days: number | null;
  sparkline: number[];
}

export interface Asset {
  id: number;
  symbol: string;
  name: string;
  asset_class: string;
  metric_type: "return" | "level_change";
  unit: string;
  provider: string;
  proxy_note: string | null;
}

export interface EconomicEvent {
  id: number;
  event_type: string;
  indicator_id: number | null;
  country: string;
  period_date: string;
  release_ts: string;
  timestamp_source: string;
  actual_first_release: number;
  previous_first_release: number | null;
  actual_latest: number | null;
  change_value: number | null;
  change_std: number | null;
  data_quality: string;
  source_id: number;
  has_consensus: boolean;
  consensus_value: number | null;
}

export interface AARPoint {
  tau: number;
  aar: number;
  aar_std: number;
  aar_se: number;
  ci_lower: number;
  ci_upper: number;
  caar: number;
  caar_bootstrap_lower: number;
  caar_bootstrap_upper: number;
}

export interface EventAbnormalReturn {
  event_id: number | string;
  event_type: string;
  period_date: string;
  release_ts: string;
  day_0_date: string;
  is_intraday_release: boolean;
  is_overlapping: boolean;
  tau_returns: Record<number, number>;
  tau_expected: Record<number, number>;
  tau_ar: Record<number, number>;
  tau_car: Record<number, number>;
  window_cars: Record<string, number>;
  window_scars: Record<string, number>;
  model_alpha: number;
  model_beta: number;
  model_r2: number;
}

export interface WindowStats {
  window: [number, number];
  n_events: number;
  mean_car: number;
  median_car: number;
  std_car: number;
  min_car: number;
  max_car: number;
  t_stat: number;
  df: number;
  p_value_t: number;
  ci_lower_t: number;
  ci_upper_t: number;
  bmp_stat: number | null;
  p_value_bmp: number | null;
  sign_stat_positive: number;
  sign_stat_negative: number;
  p_value_sign: number;
  wilcoxon_stat: number | null;
  p_value_wilcoxon: number | null;
  bootstrap_ci_lower: number;
  bootstrap_ci_upper: number;
  effect_size_d: number;
  effect_size_band: string;
  verdict: string;
  caveats: string[];
}

export interface ExcludedEvent {
  event_id: number | string;
  event_type: string;
  period_date: string;
  release_ts: string;
  reason: string;
}

export interface EventStudyResult {
  study_id: number | null;
  config_hash: string;
  input_fingerprint: string;
  app_version: string;
  is_demo: boolean;
  config: {
    event_type: string;
    asset_symbol: string;
    benchmark_symbol: string | null;
    start_date?: string | null;
    end_date?: string | null;
    event_window: [number, number];
    estimation_window: [number, number];
    return_method: "simple" | "log";
    model_type: "mean_adjusted" | "market_adjusted" | "market_model";
    use_first_release: boolean;
    exclude_overlapping: boolean;
    seed: number;
  };
  n_included: number;
  n_excluded: number;
  event_type: string;
  asset_symbol: string;
  benchmark_symbol: string | null;
  metric_type: string;
  unit: string;
  aar_series: AARPoint[];
  per_event: EventAbnormalReturn[];
  window_stats: Record<string, WindowStats>;
  excluded_events: ExcludedEvent[];
  primary_window: string;
  primary_verdict: string;
  created_at: string;
}

export interface DataStatusSummary {
  is_live_mode: boolean;
  data_mode: "LIVE" | "DEMO";
  banner_message: string | null;
  total_assets: number;
  total_indicators: number;
  total_events: number;
  total_prices: number;
  last_ingestion_time: string | null;
  last_ingestion_status: string | null;
  series_coverage: Array<{
    symbol: string;
    name: string;
    class: string;
    count: number;
    start: string | null;
    end: string | null;
  }>;
  disabled_modes: Array<{
    mode: string;
    status: string;
    reason: string;
  }>;
}
