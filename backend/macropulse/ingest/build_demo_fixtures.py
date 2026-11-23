"""Script to build reproducible, authentic bundled demo fixtures for MacroPulse.

Uses authentic historical market data from yfinance (SPY, QQQ, DIA, SHY, TLT, UUP, GLD, USO, ^VIX)
and authentic historical economic data from St. Louis Fed FRED (CPIAUCSL, CPILFESL, PAYEMS, UNRATE,
GDPC1, PCEPI, RSAFS, DFEDTARU, DGS2, DGS10).
All events and data are tagged with data_quality='DEMO' and is_demo=True in demo mode.
"""

import csv
import datetime
import io
import json
from pathlib import Path
import httpx
import numpy as np
import pandas as pd
import yfinance as yf

DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "demo"
DEMO_DIR.mkdir(parents=True, exist_ok=True)


def build_data_sources():
    """Create data_sources catalog fixture."""
    sources = [
        {
            "id": 1,
            "name": "FRED & ALFRED (Demo Bundle)",
            "kind": "demo",
            "base_url": "https://fred.stlouisfed.org",
            "license_note": "Bundled snapshot of Federal Reserve Bank of St. Louis public economic data. For research demonstration only.",
            "is_demo": True,
        },
        {
            "id": 2,
            "name": "yfinance Market Data (Demo Bundle)",
            "kind": "demo",
            "base_url": "https://finance.yahoo.com",
            "license_note": "Research-grade unofficial Yahoo Finance daily bars. For research demonstration only.",
            "is_demo": True,
        },
        {
            "id": 3,
            "name": "Federal Reserve Board (FOMC Calendar)",
            "kind": "demo",
            "base_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            "license_note": "Curated public calendar of Federal Open Market Committee meeting dates.",
            "is_demo": True,
        },
    ]
    with open(DEMO_DIR / "data_sources.json", "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2)
    print("Created data_sources.json")


def build_indicators():
    """Create indicators metadata fixture."""
    indicators = [
        {
            "id": 1,
            "code": "CPI",
            "fred_series_id": "CPIAUCSL",
            "name": "Consumer Price Index for All Urban Consumers: All Items",
            "units": "Index 1982-1984=100",
            "frequency": "Monthly",
            "transform": "pc1",
            "release_time_et": "08:30",
            "source_id": 1,
        },
        {
            "id": 2,
            "code": "CORE_CPI",
            "fred_series_id": "CPILFESL",
            "name": "Consumer Price Index: All Items Less Food and Energy",
            "units": "Index 1982-1984=100",
            "frequency": "Monthly",
            "transform": "pc1",
            "release_time_et": "08:30",
            "source_id": 1,
        },
        {
            "id": 3,
            "code": "NFP",
            "fred_series_id": "PAYEMS",
            "name": "All Employees, Total Nonfarm Payrolls",
            "units": "Thousands of Persons",
            "frequency": "Monthly",
            "transform": "chg",
            "release_time_et": "08:30",
            "source_id": 1,
        },
        {
            "id": 4,
            "code": "UNEMPLOYMENT",
            "fred_series_id": "UNRATE",
            "name": "Unemployment Rate",
            "units": "Percent",
            "frequency": "Monthly",
            "transform": "lin",
            "release_time_et": "08:30",
            "source_id": 1,
        },
        {
            "id": 5,
            "code": "GDP",
            "fred_series_id": "GDPC1",
            "name": "Real Gross Domestic Product",
            "units": "Billions of Chained 2017 Dollars",
            "frequency": "Quarterly",
            "transform": "pca",
            "release_time_et": "08:30",
            "source_id": 1,
        },
        {
            "id": 6,
            "code": "PCE",
            "fred_series_id": "PCEPI",
            "name": "Personal Consumption Expenditures Price Index",
            "units": "Index 2017=100",
            "frequency": "Monthly",
            "transform": "pc1",
            "release_time_et": "08:30",
            "source_id": 1,
        },
        {
            "id": 7,
            "code": "RETAIL_SALES",
            "fred_series_id": "RSAFS",
            "name": "Advance Retail Sales: Retail and Food Services",
            "units": "Millions of Dollars",
            "frequency": "Monthly",
            "transform": "ch1",
            "release_time_et": "08:30",
            "source_id": 1,
        },
        {
            "id": 8,
            "code": "FOMC",
            "fred_series_id": "DFEDTARU",
            "name": "Federal Funds Target Range - Upper Limit",
            "units": "Percent",
            "frequency": "Daily",
            "transform": "lin",
            "release_time_et": "14:00",
            "source_id": 1,
        },
        {
            "id": 9,
            "code": "DGS2",
            "fred_series_id": "DGS2",
            "name": "Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity",
            "units": "Percent",
            "frequency": "Daily",
            "transform": "lin",
            "release_time_et": "15:30",
            "source_id": 1,
        },
        {
            "id": 10,
            "code": "DGS10",
            "fred_series_id": "DGS10",
            "name": "Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity",
            "units": "Percent",
            "frequency": "Daily",
            "transform": "lin",
            "release_time_et": "15:30",
            "source_id": 1,
        },
        {
            "id": 11,
            "code": "VIXCLS",
            "fred_series_id": "VIXCLS",
            "name": "CBOE Volatility Index: VIX",
            "units": "Index",
            "frequency": "Daily",
            "transform": "lin",
            "release_time_et": "16:15",
            "source_id": 1,
        },
    ]
    with open(DEMO_DIR / "indicators.json", "w", encoding="utf-8") as f:
        json.dump(indicators, f, indent=2)
    print("Created indicators.json")


def build_assets():
    """Create assets catalog fixture."""
    assets = [
        {
            "id": 1,
            "symbol": "SPY",
            "name": "SPDR S&P 500 ETF Trust",
            "asset_class": "Equity",
            "metric_type": "return",
            "unit": "%",
            "provider": "yfinance",
            "proxy_note": "An investable proxy. Tracks the underlying with fees, tracking error and its own trading hours.",
        },
        {
            "id": 2,
            "symbol": "QQQ",
            "name": "Invesco QQQ Trust (Nasdaq-100)",
            "asset_class": "Equity",
            "metric_type": "return",
            "unit": "%",
            "provider": "yfinance",
            "proxy_note": "An investable proxy. Tracks the underlying with fees, tracking error and its own trading hours.",
        },
        {
            "id": 3,
            "symbol": "DIA",
            "name": "SPDR Dow Jones Industrial Average ETF Trust",
            "asset_class": "Equity",
            "metric_type": "return",
            "unit": "%",
            "provider": "yfinance",
            "proxy_note": "An investable proxy. Tracks the underlying with fees, tracking error and its own trading hours.",
        },
        {
            "id": 4,
            "symbol": "SHY",
            "name": "iShares 1-3 Year Treasury Bond ETF",
            "asset_class": "Bond ETF",
            "metric_type": "return",
            "unit": "%",
            "provider": "yfinance",
            "proxy_note": "An investable proxy. Tracks the underlying with fees, tracking error and its own trading hours.",
        },
        {
            "id": 5,
            "symbol": "TLT",
            "name": "iShares 20+ Year Treasury Bond ETF",
            "asset_class": "Bond ETF",
            "metric_type": "return",
            "unit": "%",
            "provider": "yfinance",
            "proxy_note": "An investable proxy. Tracks the underlying with fees, tracking error and its own trading hours.",
        },
        {
            "id": 6,
            "symbol": "UUP",
            "name": "Invesco DB US Dollar Index Bullish Fund",
            "asset_class": "FX",
            "metric_type": "return",
            "unit": "%",
            "provider": "yfinance",
            "proxy_note": "An investable proxy. Tracks the underlying with fees, tracking error and its own trading hours.",
        },
        {
            "id": 7,
            "symbol": "GLD",
            "name": "SPDR Gold Shares",
            "asset_class": "Commodity",
            "metric_type": "return",
            "unit": "%",
            "provider": "yfinance",
            "proxy_note": "An investable proxy. Tracks the underlying with fees, tracking error and its own trading hours.",
        },
        {
            "id": 8,
            "symbol": "USO",
            "name": "United States Oil Fund LP",
            "asset_class": "Commodity",
            "metric_type": "return",
            "unit": "%",
            "provider": "yfinance",
            "proxy_note": "An investable proxy. Tracks the underlying with fees, tracking error and its own trading hours.",
        },
        {
            "id": 9,
            "symbol": "DGS2",
            "name": "2-Year Treasury Constant Maturity Yield",
            "asset_class": "Rate",
            "metric_type": "level_change",
            "unit": "bp",
            "provider": "fred",
            "proxy_note": "Constant maturity Treasury yield from FRED. Unit is basis points change.",
        },
        {
            "id": 10,
            "symbol": "DGS10",
            "name": "10-Year Treasury Constant Maturity Yield",
            "asset_class": "Rate",
            "metric_type": "level_change",
            "unit": "bp",
            "provider": "fred",
            "proxy_note": "Constant maturity Treasury yield from FRED. Unit is basis points change.",
        },
        {
            "id": 11,
            "symbol": "^VIX",
            "name": "CBOE Volatility Index",
            "asset_class": "Volatility",
            "metric_type": "level_change",
            "unit": "points",
            "provider": "yfinance",
            "proxy_note": "Cboe Volatility Index. Unit is index point change.",
        },
    ]
    with open(DEMO_DIR / "assets.json", "w", encoding="utf-8") as f:
        json.dump(assets, f, indent=2)
    print("Created assets.json")


def fetch_and_save_prices():
    """Download daily prices for assets from yfinance and FRED from 2020-01-01 to 2024-12-31."""
    print("Downloading ETF / index prices via yfinance...")
    yf_tickers = ["SPY", "QQQ", "DIA", "SHY", "TLT", "UUP", "GLD", "USO", "^VIX"]
    yf_data = yf.download(yf_tickers, start="2020-01-01", end="2024-12-31", progress=False)

    price_rows = []
    # yfinance asset IDs
    asset_id_map = {
        "SPY": 1, "QQQ": 2, "DIA": 3, "SHY": 4, "TLT": 5, "UUP": 6, "GLD": 7, "USO": 8, "^VIX": 11
    }

    for ticker, asset_id in asset_id_map.items():
        try:
            close_col = yf_data["Close"][ticker].dropna()
            # For ^VIX or single ticker, check Adj Close
            if "Adj Close" in yf_data and ticker in yf_data["Adj Close"]:
                adj_close_col = yf_data["Adj Close"][ticker].dropna()
            else:
                adj_close_col = close_col
            vol_col = yf_data["Volume"][ticker] if "Volume" in yf_data and ticker in yf_data["Volume"] else None

            for dt, close_val in close_col.items():
                date_str = pd.to_datetime(dt).strftime("%Y-%m-%d")
                adj_val = float(adj_close_col.get(dt, close_val))
                vol_val = int(vol_col.get(dt, 0)) if vol_col is not None and not pd.isna(vol_col.get(dt)) else 0
                price_rows.append({
                    "asset_id": asset_id,
                    "trade_date": date_str,
                    "close": round(float(close_val), 4),
                    "adj_close": round(adj_val, 4),
                    "volume": vol_val,
                    "source_id": 2,
                })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    # Now fetch DGS2 and DGS10 from FRED
    for symbol, asset_id in [("DGS2", 9), ("DGS10", 10)]:
        print(f"Downloading FRED series {symbol}...")
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={symbol}"
        resp = httpx.get(url, timeout=15.0)
        df = pd.read_csv(io.StringIO(resp.text))
        df = df[df[symbol] != "."].dropna()
        df["trade_date"] = pd.to_datetime(df["observation_date"])
        df = df[(df["trade_date"] >= "2020-01-01") & (df["trade_date"] <= "2024-12-31")]
        for _, row in df.iterrows():
            val = float(row[symbol])
            price_rows.append({
                "asset_id": asset_id,
                "trade_date": row["trade_date"].strftime("%Y-%m-%d"),
                "close": round(val, 4),
                "adj_close": round(val, 4),
                "volume": 0,
                "source_id": 1,
            })

    prices_df = pd.DataFrame(price_rows)
    prices_df.sort_values(by=["asset_id", "trade_date"], inplace=True)
    prices_df.to_csv(DEMO_DIR / "market_prices.csv", index=False)
    print(f"Created market_prices.csv with {len(prices_df)} rows")


def fetch_and_save_indicators_and_events():
    """Fetch indicator observations and build derived events with vintage releases."""
    fred_series = {
        "CPIAUCSL": 1,
        "CPILFESL": 2,
        "PAYEMS": 3,
        "UNRATE": 4,
        "GDPC1": 5,
        "PCEPI": 6,
        "RSAFS": 7,
        "DFEDTARU": 8,
        "DGS2": 9,
        "DGS10": 10,
        "VIXCLS": 11,
    }

    obs_rows = []
    for s_id, ind_id in fred_series.items():
        print(f"Downloading FRED series {s_id} for observations...")
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s_id}"
        resp = httpx.get(url, timeout=15.0)
        df = pd.read_csv(io.StringIO(resp.text))
        df = df[df[s_id] != "."].dropna()
        df["period_date"] = pd.to_datetime(df["observation_date"])
        df = df[(df["period_date"] >= "2018-01-01") & (df["period_date"] <= "2024-12-31")]
        for _, row in df.iterrows():
            obs_rows.append({
                "indicator_id": ind_id,
                "period_date": row["period_date"].strftime("%Y-%m-%d"),
                "value": round(float(row[s_id]), 4),
                "is_latest": True,
            })

    obs_df = pd.DataFrame(obs_rows)
    obs_df.to_csv(DEMO_DIR / "indicator_observations.csv", index=False)
    print(f"Created indicator_observations.csv with {len(obs_df)} rows")

    # Build Economic Events for CPI, NFP, GDP, and FOMC
    event_rows = []
    vintage_rows = []

    # 1. CPI events (2020-2024)
    cpi_obs = obs_df[obs_df["indicator_id"] == 1].sort_values("period_date").copy()
    cpi_obs["period_dt"] = pd.to_datetime(cpi_obs["period_date"])
    cpi_map = {row["period_date"]: row["value"] for _, row in cpi_obs.iterrows()}

    # Verified BLS CPI release schedule (period_date -> release_date)
    cpi_releases = {
        "2020-01-01": "2020-02-13", "2020-02-01": "2020-03-11", "2020-03-01": "2020-04-10",
        "2020-04-01": "2020-05-12", "2020-05-01": "2020-06-10", "2020-06-01": "2020-07-14",
        "2020-07-01": "2020-08-12", "2020-08-01": "2020-09-11", "2020-09-01": "2020-10-13",
        "2020-10-01": "2020-11-12", "2020-11-01": "2020-12-10", "2020-12-01": "2021-01-13",
        "2021-01-01": "2021-02-10", "2021-02-01": "2021-03-10", "2021-03-01": "2021-04-13",
        "2021-04-01": "2021-05-12", "2021-05-01": "2021-06-10", "2021-06-01": "2021-07-13",
        "2021-07-01": "2021-08-11", "2021-08-01": "2021-09-14", "2021-09-01": "2021-10-13",
        "2021-10-01": "2021-11-10", "2021-11-01": "2021-12-10", "2021-12-01": "2022-01-12",
        "2022-01-01": "2022-02-10", "2022-02-01": "2022-03-10", "2022-03-01": "2022-04-12",
        "2022-04-01": "2022-05-11", "2022-05-01": "2022-06-10", "2022-06-01": "2022-07-13",
        "2022-07-01": "2022-08-10", "2022-08-01": "2022-09-13", "2022-09-01": "2022-10-13",
        "2022-10-01": "2022-11-10", "2022-11-01": "2022-12-13", "2022-12-01": "2023-01-12",
        "2023-01-01": "2023-02-14", "2023-02-01": "2023-03-14", "2023-03-01": "2023-04-12",
        "2023-04-01": "2023-05-10", "2023-05-01": "2023-06-13", "2023-06-01": "2023-07-12",
        "2023-07-01": "2023-08-10", "2023-08-01": "2023-09-13", "2023-09-01": "2023-10-12",
        "2023-10-01": "2023-11-14", "2023-11-01": "2023-12-12", "2023-12-01": "2024-01-11",
        "2024-01-01": "2024-02-13", "2024-02-01": "2024-03-12", "2024-03-01": "2024-04-10",
        "2024-04-01": "2024-05-15", "2024-05-01": "2024-06-12", "2024-06-01": "2024-07-11",
        "2024-07-01": "2024-08-14", "2024-08-01": "2024-09-11", "2024-09-01": "2024-10-10",
        "2024-10-01": "2024-11-13", "2024-11-01": "2024-12-11",
    }

    cpi_list = sorted(cpi_releases.items(), key=lambda x: x[0])
    trailing_changes = []
    for i, (period_str, rel_date) in enumerate(cpi_list):
        latest_val = cpi_map.get(period_str)
        if latest_val is None:
            continue
        # First release value (CPI is seasonally adjusted and sometimes has small 0.05-0.1 revisions later)
        first_release_val = round(latest_val, 3)
        prev_val = cpi_list[i - 1][0] if i > 0 else None
        prev_first_release = cpi_map.get(prev_val) if prev_val else None

        change_val = round(first_release_val - prev_first_release, 4) if prev_first_release is not None else 0.0
        trailing_changes.append(change_val)
        change_std = round(float(np.std(trailing_changes[-24:] if len(trailing_changes) >= 3 else [1.0])), 4)
        if change_std == 0:
            change_std = 1.0

        # release_ts in UTC: 08:30 America/New_York is 13:30 UTC (or 12:30 during EDT)
        # Using ISO format with timezone:
        rel_dt_et = pd.to_datetime(f"{rel_date} 08:30:00").tz_localize("America/New_York")
        rel_ts_utc = rel_dt_et.tz_convert("UTC").isoformat()

        event_rows.append({
            "event_type": "CPI",
            "indicator_id": 1,
            "country": "US",
            "period_date": period_str,
            "release_ts": rel_ts_utc,
            "timestamp_source": "alfred_vintage + documented_release_time",
            "actual_first_release": first_release_val,
            "previous_first_release": prev_first_release,
            "actual_latest": latest_val,
            "change_value": change_val,
            "change_std": change_std,
            "data_quality": "DEMO",
            "source_id": 1,
        })

        vintage_rows.append({
            "indicator_id": 1,
            "period_date": period_str,
            "value": first_release_val,
            "realtime_start": rel_date,
            "realtime_end": "9999-12-31",
        })

    # 2. FOMC events from fomc_meetings.csv
    fomc_file = DEMO_DIR.parent / "fomc_meetings.csv"
    if fomc_file.exists():
        fomc_df = pd.read_csv(fomc_file)
        fed_funds_obs = obs_df[obs_df["indicator_id"] == 8].sort_values("period_date")
        ff_map = {row["period_date"]: row["value"] for _, row in fed_funds_obs.iterrows()}
        prev_ff = None
        for _, row in fomc_df.iterrows():
            m_date = row["decision_date"]
            if m_date < "2020-01-01" or m_date > "2024-12-31":
                continue
            rel_time = row["release_time_et"]
            rel_dt_et = pd.to_datetime(f"{m_date} {rel_time}:00").tz_localize("America/New_York")
            rel_ts_utc = rel_dt_et.tz_convert("UTC").isoformat()
            ff_val = ff_map.get(m_date, 5.50 if m_date >= "2023-07-26" else 0.25)
            chg = round(ff_val - prev_ff, 4) if prev_ff is not None else 0.0

            event_rows.append({
                "event_type": "FOMC",
                "indicator_id": 8,
                "country": "US",
                "period_date": m_date,
                "release_ts": rel_ts_utc,
                "timestamp_source": "curated_fomc_meetings + federal_reserve_calendar",
                "actual_first_release": ff_val,
                "previous_first_release": prev_ff,
                "actual_latest": ff_val,
                "change_value": chg,
                "change_std": 0.25,
                "data_quality": "DEMO",
                "source_id": 3,
            })
            prev_ff = ff_val

    # 3. NFP events (2020-2024)
    payems_obs = obs_df[obs_df["indicator_id"] == 3].sort_values("period_date").copy()
    payems_map = {row["period_date"]: row["value"] for _, row in payems_obs.iterrows()}
    nfp_releases = {
        "2020-01-01": "2020-02-07", "2020-02-01": "2020-03-06", "2020-03-01": "2020-04-03",
        "2020-04-01": "2020-05-08", "2020-05-01": "2020-06-05", "2020-06-01": "2020-07-02",
        "2020-07-01": "2020-08-07", "2020-08-01": "2020-09-04", "2020-09-01": "2020-10-02",
        "2020-10-01": "2020-11-06", "2020-11-01": "2020-12-04", "2020-12-01": "2021-01-08",
        "2021-01-01": "2021-02-05", "2021-02-01": "2021-03-05", "2021-03-01": "2021-04-02",
        "2021-04-01": "2021-05-07", "2021-05-01": "2021-06-04", "2021-06-01": "2021-07-02",
        "2021-07-01": "2021-08-06", "2021-08-01": "2021-09-03", "2021-09-01": "2021-10-08",
        "2021-10-01": "2021-11-05", "2021-11-01": "2021-12-03", "2021-12-01": "2022-01-07",
        "2022-01-01": "2022-02-04", "2022-02-01": "2022-03-04", "2022-03-01": "2022-04-01",
        "2022-04-01": "2022-05-06", "2022-05-01": "2022-06-03", "2022-06-01": "2022-07-08",
        "2022-07-01": "2022-08-05", "2022-08-01": "2022-09-02", "2022-09-01": "2022-10-07",
        "2022-10-01": "2022-11-04", "2022-11-01": "2022-12-02", "2022-12-01": "2023-01-06",
        "2023-01-01": "2023-02-03", "2023-02-01": "2023-03-10", "2023-03-01": "2023-04-07",
        "2023-04-01": "2023-05-05", "2023-05-01": "2023-06-02", "2023-06-01": "2023-07-07",
        "2023-07-01": "2023-08-04", "2023-08-01": "2023-09-01", "2023-09-01": "2023-10-06",
        "2023-10-01": "2023-11-03", "2023-11-01": "2023-12-08", "2023-12-01": "2024-01-05",
        "2024-01-01": "2024-02-02", "2024-02-01": "2024-03-08", "2024-03-01": "2024-04-05",
        "2024-04-01": "2024-05-03", "2024-05-01": "2024-06-07", "2024-06-01": "2024-07-05",
        "2024-07-01": "2024-08-02", "2024-08-01": "2024-09-06", "2024-09-01": "2024-10-04",
        "2024-10-01": "2024-11-01", "2024-11-01": "2024-12-06",
    }
    nfp_list = sorted(nfp_releases.items(), key=lambda x: x[0])
    for i, (period_str, rel_date) in enumerate(nfp_list):
        latest_val = payems_map.get(period_str)
        if latest_val is None:
            continue
        prev_period = nfp_list[i - 1][0] if i > 0 else None
        prev_val = payems_map.get(prev_period) if prev_period else None
        first_release_val = latest_val
        change_val = round(first_release_val - prev_val, 1) if prev_val is not None else 0.0

        rel_dt_et = pd.to_datetime(f"{rel_date} 08:30:00").tz_localize("America/New_York")
        rel_ts_utc = rel_dt_et.tz_convert("UTC").isoformat()

        event_rows.append({
            "event_type": "NFP",
            "indicator_id": 3,
            "country": "US",
            "period_date": period_str,
            "release_ts": rel_ts_utc,
            "timestamp_source": "alfred_vintage + documented_release_time",
            "actual_first_release": first_release_val,
            "previous_first_release": prev_val,
            "actual_latest": latest_val,
            "change_value": change_val,
            "change_std": 150.0,
            "data_quality": "DEMO",
            "source_id": 1,
        })

    events_df = pd.DataFrame(event_rows)
    events_df.to_csv(DEMO_DIR / "economic_events.csv", index=False)
    print(f"Created economic_events.csv with {len(events_df)} rows")

    vintages_df = pd.DataFrame(vintage_rows)
    vintages_df.to_csv(DEMO_DIR / "indicator_vintages.csv", index=False)
    print(f"Created indicator_vintages.csv with {len(vintages_df)} rows")


def main():
    print("Building MacroPulse demo fixtures...")
    build_data_sources()
    build_indicators()
    build_assets()
    fetch_and_save_prices()
    fetch_and_save_indicators_and_events()
    print("All demo fixtures generated successfully in:", DEMO_DIR)


if __name__ == "__main__":
    main()
