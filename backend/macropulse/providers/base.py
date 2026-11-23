import datetime
from typing import Protocol, runtime_checkable
import pandas as pd


@runtime_checkable
class MacroDataProvider(Protocol):
    """Protocol for fetching macroeconomic series observations and historical vintages."""

    def get_series(
        self,
        series_id: str,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        """Fetch macroeconomic series observations.

        Returns DataFrame with columns:
            ['date', 'value']
        """
        ...

    def get_vintages(
        self,
        series_id: str,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        """Fetch ALFRED vintage publication revision data.

        Returns DataFrame with columns:
            ['date', 'realtime_start', 'realtime_end', 'value']
        """
        ...


@runtime_checkable
class MarketDataProvider(Protocol):
    """Protocol for fetching market daily bars and rate series."""

    def get_daily_bars(
        self,
        symbol: str,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        """Fetch daily historical price bars or rate levels.

        Returns DataFrame with columns:
            ['date', 'close', 'adj_close', 'volume']
        """
        ...
