from fastapi import APIRouter, Depends
import pandas as pd
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse.analytics.correlations import compute_cross_asset_correlations, interpret_risk_regime
from macropulse.db.session import get_db
from macropulse.models.asset import Asset, MarketPrice
from macropulse.models.event import EconomicEvent
from macropulse.schemas.study import EventStudyRequest
from macropulse.services.study_service import StudyService

router = APIRouter(prefix="/correlations", tags=["Correlations & Matrix"])


class MatrixRequest(BaseModel):
    event_type: str = "CPI"
    symbols: list[str] = ["SPY", "QQQ", "TLT", "UUP", "GLD", "^VIX", "DGS10"]


@router.post("/matrix")
def get_cross_asset_matrix(
    req: MatrixRequest,
    db: Session = Depends(get_db),
):
    """Compute mean CAR across multiple assets for the specified event type."""
    study_svc = StudyService(db)
    rows = []
    mean_cars = {}

    for sym in req.symbols:
        asset = db.execute(select(Asset).where(Asset.symbol == sym)).scalar_one_or_none()
        if not asset:
            continue

        try:
            res = study_svc.run_study(
                EventStudyRequest(
                    event_type=req.event_type,
                    asset_symbol=sym,
                    benchmark_symbol="SPY" if sym != "SPY" else None,
                    model_type="market_adjusted" if sym != "SPY" else "mean_adjusted",
                )
            )
            w_stat = res.window_stats.get("[+0,+1]")
            if w_stat:
                mean_cars[sym] = w_stat.mean_car
                rows.append({
                    "symbol": sym,
                    "name": asset.name,
                    "asset_class": asset.asset_class,
                    "metric_type": asset.metric_type,
                    "unit": asset.unit,
                    "n_events": w_stat.n_events,
                    "mean_car": w_stat.mean_car,
                    "median_car": w_stat.median_car,
                    "t_stat": w_stat.t_stat,
                    "p_value": w_stat.p_value_t,
                    "is_significant": w_stat.p_value_t < 0.05,
                })
        except Exception:
            continue

    sentiment = interpret_risk_regime(mean_cars)

    return {
        "event_type": req.event_type,
        "assets": rows,
        "sentiment_interpretation": sentiment,
    }


@router.post("/event-vs-normal")
def get_event_vs_normal_correlations(
    req: MatrixRequest,
    db: Session = Depends(get_db),
):
    """Compute correlation matrices comparing normal days vs macroeconomic announcement days."""
    # Fetch returns for symbols
    price_dfs = {}
    for sym in req.symbols:
        asset = db.execute(select(Asset).where(Asset.symbol == sym)).scalar_one_or_none()
        if not asset:
            continue
        p_rows = db.execute(
            select(MarketPrice.trade_date, MarketPrice.adj_close)
            .where(MarketPrice.asset_id == asset.id)
            .order_by(MarketPrice.trade_date)
        ).all()
        if p_rows:
            s = pd.Series([r.adj_close for r in p_rows], index=[r.trade_date for r in p_rows])
            price_dfs[sym] = s.pct_change()

    returns_df = pd.DataFrame(price_dfs).dropna()

    # Event dates
    ev_dates = set(
        db.execute(
            select(EconomicEvent.period_date).where(EconomicEvent.event_type == req.event_type)
        ).scalars().all()
    )

    corr_data = compute_cross_asset_correlations(returns_df, ev_dates)
    return corr_data
