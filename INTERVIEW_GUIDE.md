# MacroPulse — Quant & Software Engineering Interview Guide

This guide is written for a CS student interviewing for Quantitative Trading, Quantitative Research, and Financial Software Engineering internships. Every section covers the exact financial intuition, mathematical justification, and system design tradeoffs implemented in MacroPulse.

---

## 1. Executive Walkthrough

MacroPulse is a full-stack, daily-frequency event-study platform that quantifies how multi-asset instruments (equities, rates, currencies, commodities, volatility) respond to macroeconomic announcements (CPI, FOMC, Nonfarm Payrolls, GDP).

### Component Walkthrough
1. **Data Ingestion & Historical Provenance:**
   - Ingests macroeconomic series and revision vintages from the St. Louis Fed FRED/ALFRED.
   - Ingests daily adjusted market bars from Yahoo Finance.
   - Derives verified publication release dates from ALFRED's `realtime_start` timestamp paired with documented BLS/Fed announcement times (08:30 ET for CPI/NFP, 14:00 ET for FOMC).
2. **NYSE Calendar Alignment (`analytics/alignment.py`):**
   - Maps announcement timestamps to NYSE trading sessions using `pandas_market_calendars`.
   - Pre-open releases (08:30 ET) align to the current session (close $t-1$ to close $t$). Intraday releases (14:00 FOMC) align to day 0 and are flagged. After-close releases align to the next trading day.
3. **Pure Event-Study Engine (`analytics/`):**
   - Calculates abnormal returns ($AR_{i,\tau}$) across three expected-return benchmarks: Mean-Adjusted, Market-Adjusted, and Market Model (OLS $\alpha, \beta$).
   - Aggregates abnormal returns into Cumulative Abnormal Returns ($CAR$) and Cumulative Average Abnormal Returns ($CAAR$).
4. **Statistical Inference & Diagnostics (`analytics/stats.py`):**
   - Computes cross-sectional t-test, Boehmer–Musumeci–Poulsen (BMP 1991) standardized test, Sign test, Wilcoxon signed-rank test, and percentile bootstrap confidence intervals ($B = 5,000$ resamples).
5. **Macro Regime Conditioning (`analytics/regimes.py`):**
   - Classifies market volatility regimes strictly using lagged data up to $t-1$ (21-day trailing realized volatility percentile, 50/200-day trend, VIX level) to guarantee **zero look-ahead bias**.

---

## 2. Statistical Testing Choices & Quant Assumptions

### Why not rely only on a standard cross-sectional t-test?
The cross-sectional Student's t-test assumes:
1. Abnormal returns are normally distributed.
2. Events do not induce variance changes.
3. Event dates are independent (no cross-correlation or clustering).

In financial markets, announcements systematically **induce variance spikes**. Boehmer, Musumeci, and Poulsen (BMP 1991) demonstrated that event-induced volatility causes the cross-sectional t-test to reject the null hypothesis of zero abnormal return too frequently (inflated Type I error).

### The BMP (1991) Standardized Cross-Sectional Test
To solve event-induced variance:
1. Each event's abnormal return $AR_{i,\tau}$ is normalized by its forecast standard error $\hat{\sigma}_{f,i,\tau}$ (which accounts for estimation risk and market model distance from the mean benchmark return).
2. The standardized cumulative abnormal return $SCAR_i = \frac{1}{\sqrt{L}} \sum SAR_{i,\tau}$ is formed.
3. The cross-sectional standard error of $SCAR$ is computed across events.
Because $SCAR_i$ is standardized at the firm level before taking cross-sectional standard error, the test is robust to cross-sectional variance expansion on announcement days.

### Nonparametric & Bootstrap Checks
- **Sign Test (Exact Binomial):** Tests whether the median abnormal return differs from zero without relying on symmetric or normal distributions.
- **Wilcoxon Signed-Rank Test:** Incorporates the relative ranking of magnitudes as well as signs.
- **Percentile Bootstrap CI:** Resamples observed CARs with replacement 5,000 times using a fixed seed to produce non-parametric 95% confidence intervals.

---

## 3. Look-Ahead Bias & Revision Bias

### What is look-ahead bias in macroeconomic research?
Look-ahead bias occurs when a quant model uses data that was not known or published at the time the simulated trade would have been placed.

In MacroPulse, zero look-ahead bias is enforced across two dimensions:
1. **Regime Classifications:**
   On trading day $t$, realized volatility is calculated over trading days $[t-21, t-1]$. The price on day $t$ is never included in the regime feature calculation. We unit-tested this by perturbing future prices ($t \ge 80$) and proving that regime classifications for $t < 80$ remain mathematically identical.
2. **First-Release vs. Revised Vintages:**
   Economic statistics (e.g., CPI and GDP) are frequently revised months after initial publication due to seasonal adjustments and updated source surveys. Testing an event study on latest revised data tests how the market *would have reacted if it knew future revisions*, which is invalid. MacroPulse pulls original first-release vintages from ALFRED to avoid revision look-ahead bias.

---

## 4. 10 Technical Interview Questions & Answers

#### Q1: Why did you separate percentage returns and level differences in the schema?
**Answer:** "Equities and ETFs track proportional capital gains ($R = \Delta P / P$), whereas Treasury yields are interest rates quoted in percent (e.g., 4.25%). A 10 basis point rise in yield from 4.00% to 4.10% is an arithmetic difference ($\Delta y = 0.10\% = 10\text{ bp}$), not a percentage change ($\frac{4.10 - 4.00}{4.00} = 2.5\%$). Conflating them or averaging percentage returns with basis point changes corrupts statistical aggregation. In MacroPulse, `metric_type` ('return' vs 'level_change') is enforced across models, database tables, and chart axes."

#### Q2: How does your NYSE calendar alignment handle a holiday or early close?
**Answer:** "We use `pandas_market_calendars` NYSE schedule. For any announcement timestamp, we convert to `America/New_York`. If the release is on a holiday (like July 4th), the aligner identifies that the market was closed and advances Day 0 to the next active trading session (July 5th). For early closes (e.g. 13:00 ET on Christmas Eve), the close time from the schedule is checked dynamically."

#### Q3: Why is the analytics engine built as pure functions without database imports?
**Answer:** "Separating analytics from I/O achieves two critical software engineering goals: testability and determinism. Pure functions allow us to run unit tests with hand-calculated toy panels in memory with zero database setup. It also allows the same mathematical engine to be executed asynchronously or migrated to distributed batch workers."

#### Q4: How do you handle idempotency during data ingestion?
**Answer:** "All database tables have unique composite constraints, such as `UNIQUE(asset_id, trade_date)` for market prices and `UNIQUE(event_type, period_date)` for events. During pipeline execution, existing date keys are pre-fetched into memory sets, and incoming records that already exist are safely skipped. Ingestion logs record exact rows inserted and skipped on every execution."

#### Q5: What database considerations led you to support both SQLite and PostgreSQL?
**Answer:** "PostgreSQL is the production standard with robust concurrency and connection pooling in Docker. However, forcing interviewers or contributors to configure Postgres locally creates setup friction. By utilizing SQLAlchemy 2.x with declarative models and Alembic batch mode migrations, the app runs zero-config with SQLite locally while maintaining 100% schema parity with PostgreSQL in production."

#### Q6: Why did you choose TanStack Query v5 for the frontend?
**Answer:** "TanStack Query provides declarative server-state management. It handles caching, deduplication of concurrent requests, background revalidation, and loading/error states without boilerplate Redux actions. When a user runs an event study, the result is cached by query key, preventing redundant network trips."

#### Q7: How did you implement strict color palette constraints in Tailwind?
**Answer:** "In `tailwind.config.ts`, overriding `theme.colors` directly completely removes the default Tailwind color palette. The only tokens available in the application are our six custom design tokens (`palladian`, `oatmeal`, `blue-fantastic`, `burning-flame`, `truffle`, `abyssal`) and their opacity variants, guaranteeing design consistency."

#### Q8: How is the PDF report generated without headless browser dependencies?
**Answer:** "Instead of running headless Chrome or Puppeteer (which is heavy, fragile, and memory-intensive in server environments), we use ReportLab Platypus. It builds deterministic PDF documents directly from Python flowable primitives and tables, rendering in milliseconds using our exact palette hex codes."

#### Q9: What happens if FRED rate limits are exceeded?
**Answer:** "The `FREDProvider` implements polite rate-limiting with a minimum delay between calls. Furthermore, it wraps HTTP requests with `tenacity` exponential backoff and jitter, retrying on HTTP 429 and 5xx errors up to 4 attempts before raising structured exceptions."

#### Q10: How are input fingerprints generated for study reproducibility?
**Answer:** "We serialize the canonical JSON representation of the study parameters (event type, asset, benchmark, windows, return method, model, seed), sort the keys deterministically, and compute a SHA-256 hash. This fingerprint is stored with the result, enabling audit verification."

---

## 5. 5 Quant Interview Questions & Answers

#### Q1: Why can't daily-frequency event studies definitively isolate the announcement effect?
**Answer:** "Daily closing prices reflect all news, earnings releases, geopolitics, and liquidity flows that occurred between 16:00 ET yesterday and 16:00 ET today. For an 08:30 ET CPI release, the daily bar $Close_{t-1} \to Close_t$ includes the pre-market announcement, but also 6.5 hours of regular trading. If an unrelated geopolitical event or earnings surprise occurs at 13:00 ET, it contaminates the abnormal return. Isolating the pure announcement effect requires tick or 1-minute data over a tight $[ -15\text{m}, +60\text{m} ]$ intraday window."

#### Q2: What is the difference between an Indicator Change and a Consensus Surprise?
**Answer:** "Market prices reflect existing expectations. If CPI increases by +0.4% month-over-month, but consensus expectations were already +0.4%, the announcement carries zero new information. The true surprise is:
$$\text{Surprise} = \text{Actual} - \text{Consensus}$$
When analyst consensus is unavailable, researchers fall back on $\text{Actual}_t - \text{Actual}_{t-1}$. However, this conflates trend with surprise: a market that anticipated the change has already priced it in."

#### Q3: What is event clustering, and how does it bias event-study t-statistics?
**Answer:** "Event clustering occurs when multiple assets experience an event on the exact same date (cross-sectional clustering), or when multiple events of the same type occur close in time (temporal clustering, like consecutive FOMC announcements). When event windows overlap, the error terms $\varepsilon_{i,t}$ are cross-correlated. This violates the OLS independence assumption and underestimates the standard error of CAAR, leading to artificially inflated t-statistics and false discoveries."

#### Q4: When would you use a Market Model OLS vs. a Market-Adjusted model?
**Answer:** "The Market-Adjusted model assumes $\alpha = 0$ and $\beta = 1$. It is appropriate when estimating beta is noisy (e.g., short historical series or structural breaks in the firm/asset). The Market Model OLS estimates empirical $\alpha$ and $\beta$ over a clean estimation window. It is preferred when an asset's beta differs significantly from 1 (e.g. high-beta tech equities or low-beta defensive assets), removing market-wide beta co-movement from the abnormal return."

#### Q5: What is survivorship bias in ETF event studies, and how does it affect research?
**Answer:** "Using current ETF universes (like SPY or QQQ) implies that the index composition today represents historical constituents. While index-level ETFs avoid individual stock delisting bias, thematic or sector ETFs that shuttered during bear markets are missing from historical databases. For broad market benchmarks, ETF tracking error, expense ratios, and creation/redemption frictions create minor differences relative to theoretical index returns."

---

## 6. Resume Bullet Points (Tested & Implemented)

- **MacroPulse (Quant Event-Study & Macro Sentiment Platform):**
  - Engineered a full-stack quantitative event-study research platform in Python (FastAPI, NumPy, SciPy, Statsmodels, Pandas) and TypeScript (React 18, Vite, TanStack Query, Plotly.js).
  - Implemented core event-study methodologies (Mean-Adjusted, Market-Adjusted, Market Model OLS) calculating AR, CAR, AAR, and CAAR with NYSE calendar alignment across 11 macro indicators and 11 asset proxies.
  - Built rigorous hypothesis testing suite including cross-sectional t-tests, Boehmer–Musumeci–Poulsen (BMP 1991) standardized tests for event-induced variance, Wilcoxon signed-rank tests, and 5,000-resample bootstrap confidence intervals.
  - Designed zero look-ahead market regime classification engine using lagged 21-day realized volatility percentiles and moving-average filters, backed by automated future-perturbation unit tests.
  - Developed automated PDF quant reporting system using ReportLab and built end-to-end CI pipeline covering 19 unit tests, integration tests, and strict TypeScript/lint checks.
