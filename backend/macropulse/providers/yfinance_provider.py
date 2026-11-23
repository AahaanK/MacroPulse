import datetime
import pandas as pd
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
import yfinance as yf

from macropulse.providers.base import MarketDataProvider


class YFinanceProvider(MarketDataProvider):
    """Market data provider fetching daily bars via yfinance.

    Labelled as 'research-grade, unofficial' in UI and documentation.
    """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    def get_daily_bars(
        self,
        symbol: str,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        s_str = pd.to_datetime(start).strftime("%Y-%m-%d") if start else "2015-01-01"
        e_str = pd.to_datetime(end).strftime("%Y-%m-%d") if end else datetime.date.today().strftime("%Y-%m-%d")

        df = yf.download(symbol, start=s_str, end=e_str, progress=False, auto_adjust=False)
        if df.empty:
            return pd.DataFrame(columns=["date", "close", "adj_close", "volume"])

        # Handle potential multi-index columns from yfinance v0.2+
        if isinstance(df.columns, pd.MultiIndex):
            df = df.droplevel(1, axis=1)

        records = []
        for dt, row in df.iterrows():
            close_val = float(row.get("Close", 0.0))
            adj_val = float(row.get("Adj Close", close_val))
            vol_val = int(row.get("Volume", 0))
            records.append({
                "date": pd.to_datetime(dt).date(),
                "close": round(close_val, 4),
                "adj_close": round(adj_val, 4),
                "volume": vol_val,
            })

        res_df = pd.DataFrame(records)
        return res_df.sort_values("date").reset_index(drop=True)
