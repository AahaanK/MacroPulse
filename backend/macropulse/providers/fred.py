import datetime
import io
import time
import httpx
import pandas as pd
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from macropulse.config import settings
from macropulse.providers.base import MacroDataProvider


class FREDProvider(MacroDataProvider):
    """FRED and ALFRED macroeconomic data provider with exponential backoff and rate limiting."""

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.FRED_API_KEY
        self.last_request_time = 0.0

    def _rate_limit(self):
        """Respect FRED's rate limits (at least 0.5s between requests)."""
        elapsed = time.time() - self.last_request_time
        if elapsed < settings.FRED_RATE_LIMIT_DELAY:
            time.sleep(settings.FRED_RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(settings.FRED_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    def _fetch_json(self, endpoint: str, params: dict) -> dict:
        self._rate_limit()
        params["api_key"] = self.api_key
        params["file_type"] = "json"
        with httpx.Client(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
            resp = client.get(f"{self.BASE_URL}/{endpoint}", params=params)
            resp.raise_for_status()
            return resp.json()

    def get_series(
        self,
        series_id: str,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        """Fetch series observations from FRED API or public fallback endpoint."""
        if self.api_key:
            params = {"series_id": series_id}
            if start:
                params["observation_start"] = pd.to_datetime(start).strftime("%Y-%m-%d")
            if end:
                params["observation_end"] = pd.to_datetime(end).strftime("%Y-%m-%d")

            data = self._fetch_json("series/observations", params)
            obs = data.get("observations", [])
            rows = []
            for item in obs:
                val = item.get("value")
                if val is not None and val != ".":
                    rows.append({
                        "date": pd.to_datetime(item["date"]).date(),
                        "value": float(val),
                    })
            return pd.DataFrame(rows)

        # Fallback to direct public FRED CSV download if no API key is provided
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        with httpx.Client(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
            resp = client.get(url)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
            df.columns = ["date", "value"]
            df = df[df["value"] != "."].dropna()
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["value"] = df["value"].astype(float)
            if start:
                s_dt = pd.to_datetime(start).date()
                df = df[df["date"] >= s_dt]
            if end:
                e_dt = pd.to_datetime(end).date()
                df = df[df["date"] <= e_dt]
            return df.sort_values("date").reset_index(drop=True)

    def get_vintages(
        self,
        series_id: str,
        start: datetime.date | str | None = None,
        end: datetime.date | str | None = None,
    ) -> pd.DataFrame:
        """Fetch ALFRED historical vintages for a series. Requires valid FRED_API_KEY."""
        if not self.api_key:
            raise ValueError("FRED_API_KEY is required to query live ALFRED vintages. Use demo mode or provide an API key.")

        params = {"series_id": series_id, "output_type": 2}  # 2: observations by real-time period
        if start:
            params["observation_start"] = pd.to_datetime(start).strftime("%Y-%m-%d")
        if end:
            params["observation_end"] = pd.to_datetime(end).strftime("%Y-%m-%d")

        data = self._fetch_json("series/observations", params)
        obs = data.get("observations", [])
        rows = []
        for item in obs:
            val = item.get("value")
            if val is not None and val != ".":
                rows.append({
                    "date": pd.to_datetime(item["date"]).date(),
                    "realtime_start": pd.to_datetime(item["realtime_start"]).date(),
                    "realtime_end": pd.to_datetime(item["realtime_end"]).date(),
                    "value": float(val),
                })
        return pd.DataFrame(rows)
