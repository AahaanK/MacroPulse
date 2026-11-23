"""Service layer for querying indicators, assets, prices, and events."""

import datetime
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from macropulse.config import settings
from macropulse.models.asset import Asset, MarketPrice
from macropulse.models.data_source import DataSource
from macropulse.models.event import ConsensusForecast, EconomicEvent
from macropulse.models.indicator import Indicator, IndicatorObservation, IndicatorVintage
from macropulse.models.log import IngestionLog
from macropulse.schemas.data import AssetSchema, DataStatusSummary, EconomicEventSchema, IndicatorSchema


class DataService:
    def __init__(self, db: Session):
        self.db = db

    def get_assets(self) -> list[AssetSchema]:
        assets = self.db.execute(select(Asset).order_by(Asset.id)).scalars().all()
        return [
            AssetSchema(
                id=a.id,
                symbol=a.symbol,
                name=a.name,
                asset_class=a.asset_class,
                metric_type=a.metric_type,
                unit=a.unit,
                provider=a.provider,
                proxy_note=a.proxy_note,
            )
            for a in assets
        ]

    def get_indicators(self) -> list[IndicatorSchema]:
        indicators = self.db.execute(select(Indicator).order_by(Indicator.id)).scalars().all()
        res = []
        today = datetime.date.today()

        for ind in indicators:
            obs = (
                self.db.execute(
                    select(IndicatorObservation)
                    .where(IndicatorObservation.indicator_id == ind.id)
                    .order_by(desc(IndicatorObservation.period_date))
                    .limit(12)
                )
                .scalars()
                .all()
            )

            latest_val = obs[0].value if obs else None
            latest_period = obs[0].period_date.isoformat() if obs else None
            prev_val = obs[1].value if len(obs) > 1 else None

            abs_chg = round(latest_val - prev_val, 4) if latest_val is not None and prev_val is not None else None
            pct_chg = (
                round(((latest_val / prev_val) - 1.0) * 100.0, 2)
                if latest_val is not None and prev_val is not None and prev_val != 0
                else None
            )

            freshness = (today - obs[0].period_date).days if obs else None
            sparkline = [float(o.value) for o in reversed(obs)] if obs else []

            res.append(
                IndicatorSchema(
                    id=ind.id,
                    code=ind.code,
                    fred_series_id=ind.fred_series_id,
                    name=ind.name,
                    units=ind.units,
                    frequency=ind.frequency,
                    transform=ind.transform,
                    release_time_et=ind.release_time_et,
                    source_id=ind.source_id,
                    latest_value=latest_val,
                    latest_period=latest_period,
                    previous_value=prev_val,
                    abs_change=abs_chg,
                    pct_change=pct_chg,
                    freshness_days=freshness,
                    sparkline=sparkline,
                )
            )
        return res

    def get_indicator_series(
        self,
        code: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[dict]:
        ind = self.db.execute(select(Indicator).where(Indicator.code == code)).scalar_one_or_none()
        if not ind:
            return []

        query = select(IndicatorObservation).where(IndicatorObservation.indicator_id == ind.id)
        if start:
            query = query.where(IndicatorObservation.period_date >= start)
        if end:
            query = query.where(IndicatorObservation.period_date <= end)
        query = query.order_by(IndicatorObservation.period_date)

        rows = self.db.execute(query).scalars().all()
        return [{"date": r.period_date.isoformat(), "value": r.value} for r in rows]

    def get_events(
        self,
        event_type: str | None = None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        data_quality: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[EconomicEventSchema], int]:
        query = select(EconomicEvent)
        if event_type:
            query = query.where(EconomicEvent.event_type == event_type)
        if start_date:
            query = query.where(EconomicEvent.period_date >= start_date)
        if end_date:
            query = query.where(EconomicEvent.period_date <= end_date)
        if data_quality:
            query = query.where(EconomicEvent.data_quality == data_quality)

        total = self.db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        offset = (page - 1) * page_size
        events = self.db.execute(query.order_by(desc(EconomicEvent.release_ts)).offset(offset).limit(page_size)).scalars().all()

        items = []
        for ev in events:
            # Check for consensus
            consensus = self.db.execute(
                select(ConsensusForecast).where(ConsensusForecast.event_id == ev.id)
            ).scalar_one_or_none()

            items.append(
                EconomicEventSchema(
                    id=ev.id,
                    event_type=ev.event_type,
                    indicator_id=ev.indicator_id,
                    country=ev.country,
                    period_date=ev.period_date.isoformat(),
                    release_ts=ev.release_ts.isoformat(),
                    timestamp_source=ev.timestamp_source,
                    actual_first_release=ev.actual_first_release,
                    previous_first_release=ev.previous_first_release,
                    actual_latest=ev.actual_latest,
                    change_value=ev.change_value,
                    change_std=ev.change_std,
                    data_quality=ev.data_quality,
                    source_id=ev.source_id,
                    has_consensus=consensus is not None,
                    consensus_value=consensus.consensus_value if consensus else None,
                )
            )
        return items, total

    def get_data_status(self) -> DataStatusSummary:
        is_live = bool(settings.FRED_API_KEY)
        data_mode = "LIVE" if is_live else "DEMO"
        banner = None if is_live else "Demonstration data — not for research conclusions"

        total_assets = self.db.execute(select(func.count(Asset.id))).scalar() or 0
        total_indicators = self.db.execute(select(func.count(Indicator.id))).scalar() or 0
        total_events = self.db.execute(select(func.count(EconomicEvent.id))).scalar() or 0
        total_prices = self.db.execute(select(func.count(MarketPrice.id))).scalar() or 0

        last_log = self.db.execute(
            select(IngestionLog).order_by(desc(IngestionLog.started_at)).limit(1)
        ).scalar_one_or_none()

        # Series coverage table
        assets = self.db.execute(select(Asset).order_by(Asset.id)).scalars().all()
        series_coverage = []
        for a in assets:
            min_date, max_date, count = self.db.execute(
                select(
                    func.min(MarketPrice.trade_date),
                    func.max(MarketPrice.trade_date),
                    func.count(MarketPrice.id),
                ).where(MarketPrice.asset_id == a.id)
            ).one()
            series_coverage.append({
                "symbol": a.symbol,
                "name": a.name,
                "class": a.asset_class,
                "count": count or 0,
                "start": min_date.isoformat() if min_date else None,
                "end": max_date.isoformat() if max_date else None,
            })

        disabled_modes = []
        # Check consensus coverage
        consensus_count = self.db.execute(select(func.count(ConsensusForecast.id))).scalar() or 0
        if consensus_count == 0:
            disabled_modes.append({
                "mode": "Consensus Surprise Mode",
                "status": "Disabled",
                "reason": "No consensus forecasts imported. Operating in Indicator Change Mode (actual − previous first release).",
            })

        if not is_live:
            disabled_modes.append({
                "mode": "Live ALFRED Real-Time Queries",
                "status": "Operating in Demo Mode",
                "reason": "FRED_API_KEY environment variable not set. Operating on bundled verified demo fixtures.",
            })

        return DataStatusSummary(
            is_live_mode=is_live,
            data_mode=data_mode,
            banner_message=banner,
            total_assets=total_assets,
            total_indicators=total_indicators,
            total_events=total_events,
            total_prices=total_prices,
            last_ingestion_time=last_log.finished_at.isoformat() if last_log and last_log.finished_at else None,
            last_ingestion_status=last_log.status if last_log else None,
            series_coverage=series_coverage,
            disabled_modes=disabled_modes,
        )
