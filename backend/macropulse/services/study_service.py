"""Service layer orchestrating event study execution, caching, and persistence."""

from dataclasses import asdict
import datetime
import hashlib
import json
import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from macropulse.analytics.event_study import run_event_study
from macropulse.config import settings
from macropulse.models.asset import Asset, MarketPrice
from macropulse.models.event import EconomicEvent
from macropulse.models.study import StudyConfig, StudyResult
from macropulse.schemas.study import (
    AARPointSchema,
    EventAbnormalReturnSchema,
    EventStudyRequest,
    EventStudyResponse,
    ExcludedEventSchema,
    WindowStatsSchema,
)


class StudyService:
    def __init__(self, db: Session):
        self.db = db

    def run_study(self, req: EventStudyRequest) -> EventStudyResponse:
        # 1. Fetch Target Asset
        asset = self.db.execute(select(Asset).where(Asset.symbol == req.asset_symbol)).scalar_one_or_none()
        if not asset:
            raise ValueError(f"Asset symbol '{req.asset_symbol}' not found in asset universe.")

        asset_prices_query = (
            select(MarketPrice.trade_date, MarketPrice.adj_close)
            .where(MarketPrice.asset_id == asset.id)
            .order_by(MarketPrice.trade_date)
        )
        asset_price_rows = self.db.execute(asset_prices_query).all()
        if not asset_price_rows:
            raise ValueError(f"No historical price data found for asset '{req.asset_symbol}'.")

        s_asset = pd.Series(
            data=[r.adj_close for r in asset_price_rows],
            index=[r.trade_date for r in asset_price_rows],
        )

        # 2. Fetch Benchmark Asset (if needed)
        s_benchmark = None
        if req.benchmark_symbol:
            benchmark = self.db.execute(
                select(Asset).where(Asset.symbol == req.benchmark_symbol)
            ).scalar_one_or_none()
            if not benchmark:
                raise ValueError(f"Benchmark symbol '{req.benchmark_symbol}' not found in asset universe.")

            bm_price_rows = self.db.execute(
                select(MarketPrice.trade_date, MarketPrice.adj_close)
                .where(MarketPrice.asset_id == benchmark.id)
                .order_by(MarketPrice.trade_date)
            ).all()

            s_benchmark = pd.Series(
                data=[r.adj_close for r in bm_price_rows],
                index=[r.trade_date for r in bm_price_rows],
            )

        # 3. Fetch Events
        events_query = select(EconomicEvent).where(EconomicEvent.event_type == req.event_type)
        if req.start_date:
            events_query = events_query.where(EconomicEvent.period_date >= req.start_date)
        if req.end_date:
            events_query = events_query.where(EconomicEvent.period_date <= req.end_date)
        events_query = events_query.order_by(EconomicEvent.period_date)

        event_rows = self.db.execute(events_query).scalars().all()
        if not event_rows:
            raise ValueError(f"No events found for event_type '{req.event_type}' within the specified date range.")

        event_dicts = [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "period_date": ev.period_date,
                "release_ts": ev.release_ts,
                "actual_first_release": ev.actual_first_release,
                "actual_latest": ev.actual_latest if not req.use_first_release and ev.actual_latest else ev.actual_first_release,
            }
            for ev in event_rows
        ]

        # 4. Execute Pure Analytics Engine
        study_output = run_event_study(
            events=event_dicts,
            asset_prices=s_asset,
            benchmark_prices=s_benchmark,
            metric_type=asset.metric_type,
            return_method=req.return_method,
            unit=asset.unit,
            model_type=req.model_type,
            event_window=(req.event_window[0], req.event_window[1]),
            estimation_window=(req.estimation_window[0], req.estimation_window[1]),
            exclude_overlapping=req.exclude_overlapping,
            seed=req.seed,
            asset_symbol=asset.symbol,
            benchmark_symbol=req.benchmark_symbol,
        )

        # 5. Compute Config Hash and Check DB Cache / Save
        config_dict = req.model_dump(mode="json")
        config_hash = hashlib.sha256(json.dumps(config_dict, default=str, sort_keys=True).encode("utf-8")).hexdigest()

        # Check existing config
        db_config = self.db.execute(
            select(StudyConfig).where(StudyConfig.config_hash == config_hash)
        ).scalar_one_or_none()

        if not db_config:
            db_config = StudyConfig(
                name=f"{req.event_type} on {req.asset_symbol} ({req.model_type})",
                config_json=config_dict,
                config_hash=config_hash,
            )
            self.db.add(db_config)
            self.db.flush()

        # Serialize results
        summary_data = {
            "n_included": study_output.n_included,
            "n_excluded": study_output.n_excluded,
            "primary_window": study_output.primary_window,
            "primary_verdict": study_output.primary_verdict,
            "metric_type": study_output.metric_type,
            "unit": study_output.unit,
        }

        per_event_data = [asdict(ev) for ev in study_output.per_event]
        aar_data = [asdict(pt) for pt in study_output.aar_series]
        stats_data = {k: asdict(v) for k, v in study_output.window_stats.items()}
        excluded_data = study_output.excluded_events

        is_demo = any(ev.data_quality == "DEMO" for ev in event_rows)

        db_result = StudyResult(
            config_id=db_config.id,
            summary_json=summary_data,
            per_event_json=per_event_data,
            aar_json=aar_data,
            stats_json=stats_data,
            excluded_json=excluded_data,
            input_fingerprint=study_output.input_fingerprint,
            app_version=settings.APP_VERSION,
            seed=req.seed,
            is_demo=is_demo,
        )
        self.db.add(db_result)
        self.db.commit()
        self.db.refresh(db_result)

        # 6. Format Response
        return EventStudyResponse(
            study_id=db_result.id,
            config_hash=config_hash,
            input_fingerprint=study_output.input_fingerprint,
            app_version=settings.APP_VERSION,
            is_demo=is_demo,
            config=config_dict,
            n_included=study_output.n_included,
            n_excluded=study_output.n_excluded,
            event_type=req.event_type,
            asset_symbol=req.asset_symbol,
            benchmark_symbol=req.benchmark_symbol,
            metric_type=study_output.metric_type,
            unit=study_output.unit,
            aar_series=[AARPointSchema(**asdict(p)) for p in study_output.aar_series],
            per_event=[EventAbnormalReturnSchema(**asdict(ev)) for ev in study_output.per_event],
            window_stats={k: WindowStatsSchema(**asdict(v)) for k, v in study_output.window_stats.items()},
            excluded_events=[ExcludedEventSchema(**ex) for ex in excluded_data],
            primary_window=study_output.primary_window,
            primary_verdict=study_output.primary_verdict,
            created_at=db_result.created_at.isoformat(),
        )

    def get_result(self, result_id: int) -> EventStudyResponse | None:
        db_result = self.db.execute(
            select(StudyResult).where(StudyResult.id == result_id)
        ).scalar_one_or_none()
        if not db_result:
            return None

        cfg = db_result.config
        summary = db_result.summary_json
        return EventStudyResponse(
            study_id=db_result.id,
            config_hash=cfg.config_hash,
            input_fingerprint=db_result.input_fingerprint,
            app_version=db_result.app_version,
            is_demo=db_result.is_demo,
            config=cfg.config_json,
            n_included=summary["n_included"],
            n_excluded=summary["n_excluded"],
            event_type=cfg.config_json.get("event_type", "CPI"),
            asset_symbol=cfg.config_json.get("asset_symbol", "SPY"),
            benchmark_symbol=cfg.config_json.get("benchmark_symbol", "SPY"),
            metric_type=summary["metric_type"],
            unit=summary["unit"],
            aar_series=[AARPointSchema(**p) for p in db_result.aar_json],
            per_event=[EventAbnormalReturnSchema(**ev) for ev in db_result.per_event_json],
            window_stats={k: WindowStatsSchema(**v) for k, v in db_result.stats_json.items()},
            excluded_events=[ExcludedEventSchema(**ex) for ex in db_result.excluded_json],
            primary_window=summary["primary_window"],
            primary_verdict=summary["primary_verdict"],
            created_at=db_result.created_at.isoformat(),
        )
