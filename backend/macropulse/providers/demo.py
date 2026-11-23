import datetime
import json
from pathlib import Path
import pandas as pd

from macropulse.providers.base import MacroDataProvider, MarketDataProvider


class DemoDataProvider:
    """Demo data provider reading from bundled authentic historical fixtures.

    All data returned is marked with is_demo = True.
    """

    def __init__(self, demo_dir: Path | None = None):
        if demo_dir is None:
            self.demo_dir = Path(__file__).resolve().parent.parent.parent / "data" / "demo"
        else:
            self.demo_dir = demo_dir
        self.is_demo = True

    def get_data_sources(self) -> list[dict]:
        with open(self.demo_dir / "data_sources.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def get_indicators(self) -> list[dict]:
        with open(self.demo_dir / "indicators.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def get_assets(self) -> list[dict]:
        with open(self.demo_dir / "assets.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def get_series(
        self,
        series_id: str,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        """Fetch macroeconomic series observations from demo fixture.

        Matches either series_id as code (e.g. 'CPI') or fred_series_id (e.g. 'CPIAUCSL').
        """
        indicators = self.get_indicators()
        matched_ind = next(
            (i for i in indicators if i["code"].upper() == series_id.upper() or i["fred_series_id"].upper() == series_id.upper()),
            None,
        )
        if not matched_ind:
            return pd.DataFrame(columns=["date", "value"])

        ind_id = matched_ind["id"]
        obs_df = pd.read_csv(self.demo_dir / "indicator_observations.csv")
        subset = obs_df[obs_df["indicator_id"] == ind_id].copy()
        subset.rename(columns={"period_date": "date"}, inplace=True)
        subset["date"] = pd.to_datetime(subset["date"]).dt.date

        if start is not None:
            s_date = pd.to_datetime(start).date()
            subset = subset[subset["date"] >= s_date]
        if end is not None:
            e_date = pd.to_datetime(end).date()
            subset = subset[subset["date"] <= e_date]

        return subset[["date", "value"]].sort_values("date").reset_index(drop=True)

    def get_vintages(
        self,
        series_id: str,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        """Fetch ALFRED historical vintages from demo fixture."""
        indicators = self.get_indicators()
        matched_ind = next(
            (i for i in indicators if i["code"].upper() == series_id.upper() or i["fred_series_id"].upper() == series_id.upper()),
            None,
        )
        if not matched_ind:
            return pd.DataFrame(columns=["date", "realtime_start", "realtime_end", "value"])

        ind_id = matched_ind["id"]
        v_df = pd.read_csv(self.demo_dir / "indicator_vintages.csv")
        subset = v_df[v_df["indicator_id"] == ind_id].copy()
        subset.rename(columns={"period_date": "date"}, inplace=True)
        subset["date"] = pd.to_datetime(subset["date"]).dt.date
        subset["realtime_start"] = pd.to_datetime(subset["realtime_start"]).dt.date

        if start is not None:
            s_date = pd.to_datetime(start).date()
            subset = subset[subset["date"] >= s_date]
        if end is not None:
            e_date = pd.to_datetime(end).date()
            subset = subset[subset["date"] <= e_date]

        return subset[["date", "realtime_start", "realtime_end", "value"]].sort_values("date").reset_index(drop=True)

    def get_daily_bars(
        self,
        symbol: str,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        """Fetch daily historical price bars from demo fixture."""
        assets = self.get_assets()
        matched_asset = next((a for a in assets if a["symbol"].upper() == symbol.upper()), None)
        if not matched_asset:
            return pd.DataFrame(columns=["date", "close", "adj_close", "volume"])

        asset_id = matched_asset["id"]
        prices_df = pd.read_csv(self.demo_dir / "market_prices.csv")
        subset = prices_df[prices_df["asset_id"] == asset_id].copy()
        subset.rename(columns={"trade_date": "date"}, inplace=True)
        subset["date"] = pd.to_datetime(subset["date"]).dt.date

        if start is not None:
            s_date = pd.to_datetime(start).date()
            subset = subset[subset["date"] >= s_date]
        if end is not None:
            e_date = pd.to_datetime(end).date()
            subset = subset[subset["date"] <= e_date]

        return subset[["date", "close", "adj_close", "volume"]].sort_values("date").reset_index(drop=True)

    def get_economic_events(
        self,
        event_type: str | None = None,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        """Fetch economic events from demo fixture."""
        events_df = pd.read_csv(self.demo_dir / "economic_events.csv")
        if event_type:
            events_df = events_df[events_df["event_type"].str.upper() == event_type.upper()].copy()

        events_df["period_date"] = pd.to_datetime(events_df["period_date"]).dt.date
        if start is not None:
            s_date = pd.to_datetime(start).date()
            events_df = events_df[events_df["period_date"] >= s_date]
        if end is not None:
            e_date = pd.to_datetime(end).date()
            events_df = events_df[events_df["period_date"] <= e_date]

        return events_df.sort_values("release_ts").reset_index(drop=True)
