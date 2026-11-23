/**
 * Short, plain-English explanations for the financial and statistical terms that appear in
 * the interface. Shown through the <Term> tooltip component.
 */
export const GLOSSARY = {
  abnormal_return:
    "How much an asset moved beyond what would normally be expected that day. Also called abnormal return (AR).",
  car:
    "Cumulative abnormal return (CAR): the extra moves added up over several days around a release.",
  aar:
    "Average abnormal return (AAR): the extra move on one specific day, averaged across every release studied.",
  caar:
    "Cumulative average abnormal return (CAAR): the average extra move, added up day by day through the window.",
  event_window:
    "The trading days measured around each release. Day 0 is the first trading session that could react to the news.",
  estimation_window:
    "An earlier, quiet stretch of trading days used to learn what “normal” looks like for the asset. It must end before the event window starts.",
  model:
    "How a “normal” day is defined. Its own average uses the asset's typical return. Compared with the market subtracts the benchmark's move. Adjusted for sensitivity also accounts for how strongly the asset usually follows the market (beta).",
  benchmark:
    "The broad market fund used as the yardstick when comparing an asset with the market.",
  first_release:
    "Uses the number as it was first published, not later revisions. Revised data would include information markets didn't have at the time.",
  overlap:
    "Drops releases whose measurement windows overlap with another release, so one move isn't counted twice.",
  return_method:
    "Simple returns are ordinary percentage changes. Log returns are a variant that adds up neatly over time; for daily moves the two are nearly identical.",
  seed:
    "Fixes the random draws used for bootstrap intervals, so the same settings always produce the same result.",
  t_stat:
    "t-statistic: how large the average move is compared with its natural variation. Values beyond about ±2 suggest a real pattern.",
  p_value:
    "The chance of seeing a move this large if releases truly had no effect. Below 0.05 is the usual bar for “statistically significant”.",
  significant:
    "Statistically significant means the average move is large enough that random chance is an unlikely explanation (p below 0.05).",
  bmp:
    "Boehmer–Musumeci–Poulsen test: a version of the t-test that accounts for markets being more volatile on release days.",
  bootstrap_ci:
    "A 95% range for the true average move, built by resampling the releases thousands of times. If it includes zero, the effect is uncertain.",
  ci:
    "95% confidence range: the span where the true value most likely sits.",
  effect_size:
    "Effect size (Cohen's d): how big the average move is relative to the spread of individual moves, regardless of sample size.",
  sign_test:
    "Counts how many releases produced an up move versus a down move, and checks whether that split is unusual.",
  wilcoxon:
    "Wilcoxon signed-rank test: checks for a consistent direction while giving less weight to a few extreme moves. Needs at least 10 non-zero moves.",
  alpha:
    "Alpha: the asset's typical daily return not explained by the market, estimated from the quiet period.",
  beta:
    "Beta: how strongly the asset tends to move with the market. 1.0 means one-for-one.",
  surprise:
    "How different the released number was from the previous release, scaled by how much it usually changes. Larger values mean bigger surprises.",
  consensus:
    "The average forecast from economists before the release. MacroPulse does not include forecast data, so it measures the change from the previous release instead.",
  slope:
    "Sensitivity: how much the asset's move changes for each one-unit increase in the surprise.",
  r_squared:
    "R²: the share of the variation in moves that the surprise explains. 0% means no relationship; 100% means a perfect one.",
  std_error:
    "Standard error: the uncertainty in the estimated sensitivity.",
  quintile:
    "Releases sorted from smallest to largest surprise and split into five equal groups.",
  asymmetry:
    "Whether higher-than-previous and lower-than-previous readings produce moves of different sizes.",
  correlation:
    "How closely two assets move together, from −1 (opposite) through 0 (unrelated) to +1 (in step).",
  regime:
    "The market's mood on the day before a release, judged from recent volatility, trend and the VIX.",
  realized_vol:
    "Realized volatility: how much the market actually swung over the past 21 trading days, annualised.",
  vol_percentile:
    "Where today's volatility ranks against its own history. The 90th percentile means more volatile than 90% of past days.",
  vix:
    "The VIX: a market-implied measure of expected S&P 500 volatility over the next 30 days, often called the “fear gauge”.",
  sma:
    "Simple moving average: the average price over the last 50 or 200 days, used to tell up-trends from down-trends.",
  look_ahead:
    "Look-ahead bias: accidentally using information that wasn't available at the time. MacroPulse only uses data from the day before.",
  robustness:
    "Re-running the same question with different reasonable settings. A finding that survives these changes is more trustworthy.",
  fingerprint:
    "A short code that identifies the exact data and settings used. The same fingerprint always gives the same result.",
  demo_data:
    "Bundled sample data that lets the app run without an internet connection or API key. Good for exploring, not for drawing conclusions.",
  intraday:
    "Released during market hours, so part of the reaction happens the same day.",
  multiple_testing:
    "Testing several windows raises the odds that one looks significant by chance, so a stricter threshold applies.",
} as const;

export type GlossaryKey = keyof typeof GLOSSARY;
