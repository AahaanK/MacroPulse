"""Data ingestion pipeline with idempotent upserts, validation, and structured audit logs."""

import datetime
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse.config import settings
from macropulse.db.session import SessionLocal
from macropulse.models.asset import Asset, MarketPrice
from macropulse.models.data_source import DataSource
from macropulse.models.event import EconomicEvent
from macropulse.models.indicator import Indicator, IndicatorObservation, IndicatorVintage
from macropulse.models.log import IngestionLog
from macropulse.providers.demo import DemoDataProvider
from macropulse.providers.fred import FREDProvider
from macropulse.providers.yfinance_provider import YFinanceProvider


class IngestionPipeline:
    """Manages idempotent data ingestion into the database."""

    def __init__(self, db: Session | None = None):
        self._external_db = db is not None
        self.db = db if db is not None else SessionLocal()
        self.demo_provider = DemoDataProvider()
        self.fred_provider = FREDProvider()
        self.yf_provider = YFinanceProvider()

    def close(self):
        if not self._external_db:
            self.db.close()

    def _log_run(
        self,
        source_id: int,
        target: str,
        started_at: datetime.datetime,
        status: str,
        rows_inserted: int,
        rows_skipped: int,
        error: str | None = None,
    ):
        log = IngestionLog(
            source_id=source_id,
            target=target,
            started_at=started_at,
            finished_at=datetime.datetime.now(datetime.timezone.utc),
            status=status,
            rows_inserted=rows_inserted,
            rows_skipped=rows_skipped,
            error=error,
        )
        self.db.add(log)
        self.db.commit()

    def ingest_data_sources(self) -> int:
        """Seed data_sources catalog."""
        sources = self.demo_provider.get_data_sources()
        inserted = 0
        for s in sources:
            existing = self.db.execute(select(DataSource).where(DataSource.id == s["id"])).scalar_one_or_none()
            if not existing:
                ds = DataSource(
                    id=s["id"],
                    name=s["name"],
                    kind=s["kind"],
                    base_url=s["base_url"],
                    license_note=s["license_note"],
                    is_demo=s["is_demo"],
                )
                self.db.add(ds)
                inserted += 1
        self.db.commit()
        return inserted

    def ingest_indicators(self) -> int:
        """Seed indicators metadata catalog."""
        self.ingest_data_sources()
        indicators = self.demo_provider.get_indicators()
        inserted = 0
        for ind in indicators:
            existing = self.db.execute(select(Indicator).where(Indicator.code == ind["code"])).scalar_one_or_none()
            if not existing:
                indicator = Indicator(
                    id=ind["id"],
                    code=ind["code"],
                    fred_series_id=ind["fred_series_id"],
                    name=ind["name"],
                    units=ind["units"],
                    frequency=ind["frequency"],
                    transform=ind.get("transform"),
                    release_time_et=ind["release_time_et"],
                    source_id=ind["source_id"],
                )
                self.db.add(indicator)
                inserted += 1
        self.db.commit()
        return inserted

    def ingest_assets(self) -> int:
        """Seed assets catalog."""
        self.ingest_data_sources()
        assets = self.demo_provider.get_assets()
        inserted = 0
        for a in assets:
            existing = self.db.execute(select(Asset).where(Asset.symbol == a["symbol"])).scalar_one_or_none()
            if not existing:
                asset = Asset(
                    id=a["id"],
                    symbol=a["symbol"],
                    name=a["name"],
                    asset_class=a["asset_class"],
                    metric_type=a["metric_type"],
                    unit=a["unit"],
                    provider=a["provider"],
                    proxy_note=a.get("proxy_note"),
                )
                self.db.add(asset)
                inserted += 1
        self.db.commit()
        return inserted

    def ingest_prices(self, since: datetime.date | None = None) -> tuple[int, int]:
        """Ingest historical daily price bars idempotently."""
        started_at = datetime.datetime.now(datetime.timezone.utc)
        self.ingest_assets()

        demo_prices_file = self.demo_provider.demo_dir / "market_prices.csv"
        if not demo_prices_file.exists():
            return 0, 0

        import pandas as pd
        df = pd.read_csv(demo_prices_file)
        inserted = 0
        skipped = 0

        # Cache existing dates per asset to ensure fast idempotent batch inserts
        existing_records = set(
            self.db.execute(select(MarketPrice.asset_id, MarketPrice.trade_date)).all()
        )

        objects_to_add = []
        for _, row in df.iterrows():
            a_id = int(row["asset_id"])
            t_date = datetime.date.fromisoformat(row["trade_date"])
            if since and t_date < since:
                skipped += 1
                continue

            if (a_id, t_date) in existing_records:
                skipped += 1
                continue

            close_val = float(row["close"])
            adj_val = float(row["adj_close"])
            vol_val = int(row["volume"]) if not pd.isna(row["volume"]) else 0

            # Data integrity validation: non-negative prices
            if close_val < 0 or adj_val < 0:
                continue

            mp = MarketPrice(
                asset_id=a_id,
                trade_date=t_date,
                close=close_val,
                adj_close=adj_val,
                volume=vol_val,
                source_id=int(row["source_id"]),
            )
            objects_to_add.append(mp)
            existing_records.add((a_id, t_date))
            inserted += 1

        if objects_to_add:
            self.db.bulk_save_objects(objects_to_add)
            self.db.commit()

        self._log_run(
            source_id=2,
            target="prices",
            started_at=started_at,
            status="SUCCESS",
            rows_inserted=inserted,
            rows_skipped=skipped,
        )
        return inserted, skipped

    def ingest_indicator_observations(self) -> tuple[int, int]:
        """Ingest indicator observations idempotently."""
        started_at = datetime.datetime.now(datetime.timezone.utc)
        self.ingest_indicators()

        obs_file = self.demo_provider.demo_dir / "indicator_observations.csv"
        if not obs_file.exists():
            return 0, 0

        import pandas as pd
        df = pd.read_csv(obs_file)
        inserted = 0
        skipped = 0

        existing_obs = set(
            self.db.execute(select(IndicatorObservation.indicator_id, IndicatorObservation.period_date)).all()
        )

        objects_to_add = []
        for _, row in df.iterrows():
            ind_id = int(row["indicator_id"])
            p_date = datetime.date.fromisoformat(row["period_date"])

            if (ind_id, p_date) in existing_obs:
                skipped += 1
                continue

            obs = IndicatorObservation(
                indicator_id=ind_id,
                period_date=p_date,
                value=float(row["value"]),
                is_latest=bool(row["is_latest"]),
            )
            objects_to_add.append(obs)
            existing_obs.add((ind_id, p_date))
            inserted += 1

        if objects_to_add:
            self.db.bulk_save_objects(objects_to_add)
            self.db.commit()

        self._log_run(
            source_id=1,
            target="indicators",
            started_at=started_at,
            status="SUCCESS",
            rows_inserted=inserted,
            rows_skipped=skipped,
        )
        return inserted, skipped

    def ingest_vintages(self) -> tuple[int, int]:
        """Ingest ALFRED indicator vintages idempotently."""
        started_at = datetime.datetime.now(datetime.timezone.utc)
        self.ingest_indicators()

        v_file = self.demo_provider.demo_dir / "indicator_vintages.csv"
        if not v_file.exists():
            return 0, 0

        import pandas as pd
        df = pd.read_csv(v_file)
        inserted = 0
        skipped = 0

        existing_vintages = set(
            self.db.execute(
                select(IndicatorVintage.indicator_id, IndicatorVintage.period_date, IndicatorVintage.realtime_start)
            ).all()
        )

        objects_to_add = []
        for _, row in df.iterrows():
            ind_id = int(row["indicator_id"])
            p_date = datetime.date.fromisoformat(row["period_date"])
            rt_start = datetime.date.fromisoformat(row["realtime_start"])
            rt_end_str = str(row["realtime_end"])
            rt_end = datetime.date(9999, 12, 31) if rt_end_str.startswith("9999") else datetime.date.fromisoformat(rt_end_str)

            if (ind_id, p_date, rt_start) in existing_vintages:
                skipped += 1
                continue

            v = IndicatorVintage(
                indicator_id=ind_id,
                period_date=p_date,
                value=float(row["value"]),
                realtime_start=rt_start,
                realtime_end=rt_end,
            )
            objects_to_add.append(v)
            existing_vintages.add((ind_id, p_date, rt_start))
            inserted += 1

        if objects_to_add:
            self.db.bulk_save_objects(objects_to_add)
            self.db.commit()

        self._log_run(
            source_id=1,
            target="vintages",
            started_at=started_at,
            status="SUCCESS",
            rows_inserted=inserted,
            rows_skipped=skipped,
        )
        return inserted, skipped

    def ingest_events(self) -> tuple[int, int]:
        """Ingest derived economic events idempotently."""
        started_at = datetime.datetime.now(datetime.timezone.utc)
        self.ingest_indicators()

        events_file = self.demo_provider.demo_dir / "economic_events.csv"
        if not events_file.exists():
            return 0, 0

        import pandas as pd
        df = pd.read_csv(events_file)
        inserted = 0
        skipped = 0

        existing_events = set(
            self.db.execute(select(EconomicEvent.event_type, EconomicEvent.period_date)).all()
        )

        for _, row in df.iterrows():
            ev_type = str(row["event_type"])
            p_date = datetime.date.fromisoformat(row["period_date"])

            if (ev_type, p_date) in existing_events:
                skipped += 1
                continue

            rel_ts = datetime.datetime.fromisoformat(row["release_ts"])
            ind_id = int(row["indicator_id"]) if not pd.isna(row["indicator_id"]) else None
            prev_first = float(row["previous_first_release"]) if not pd.isna(row["previous_first_release"]) else None
            act_latest = float(row["actual_latest"]) if not pd.isna(row["actual_latest"]) else None
            chg_val = float(row["change_value"]) if not pd.isna(row["change_value"]) else None
            chg_std = float(row["change_std"]) if not pd.isna(row["change_std"]) else None

            ev = EconomicEvent(
                event_type=ev_type,
                indicator_id=ind_id,
                country=str(row.get("country", "US")),
                period_date=p_date,
                release_ts=rel_ts,
                timestamp_source=str(row["timestamp_source"]),
                actual_first_release=float(row["actual_first_release"]),
                previous_first_release=prev_first,
                actual_latest=act_latest,
                change_value=chg_val,
                change_std=chg_std,
                data_quality=str(row.get("data_quality", "DEMO")),
                source_id=int(row.get("source_id", 1)),
            )
            self.db.add(ev)
            existing_events.add((ev_type, p_date))
            inserted += 1

        self.db.commit()
        self._log_run(
            source_id=1,
            target="events",
            started_at=started_at,
            status="SUCCESS",
            rows_inserted=inserted,
            rows_skipped=skipped,
        )
        return inserted, skipped

    def ingest_all(self, since: datetime.date | None = None) -> dict:
        """Run complete idempotent ingestion of all data targets."""
        ds_cnt = self.ingest_data_sources()
        ind_cnt = self.ingest_indicators()
        ast_cnt = self.ingest_assets()
        p_ins, p_skip = self.ingest_prices(since=since)
        o_ins, o_skip = self.ingest_indicator_observations()
        v_ins, v_skip = self.ingest_vintages()
        e_ins, e_skip = self.ingest_events()

        return {
            "data_sources": ds_cnt,
            "indicators": ind_cnt,
            "assets": ast_cnt,
            "prices": {"inserted": p_ins, "skipped": p_skip},
            "observations": {"inserted": o_ins, "skipped": o_skip},
            "vintages": {"inserted": v_ins, "skipped": v_skip},
            "events": {"inserted": e_ins, "skipped": e_skip},
        }
