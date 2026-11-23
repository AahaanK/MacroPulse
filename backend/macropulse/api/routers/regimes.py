from fastapi import APIRouter, Depends
import pandas as pd
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse.analytics.regimes import classify_market_regimes
from macropulse.db.session import get_db
from macropulse.models.asset import Asset, MarketPrice
from macropulse.models.event import EconomicEvent
from macropulse.schemas.study import EventStudyRequest
from macropulse.services.study_service import StudyService

router = APIRouter(prefix="/regimes", tags=["Regime Analysis"])


class ConditionedStudyRequest(BaseModel):
    event_type: str = "CPI"
    asset_symbol: str = "SPY"


@router.get("/history")
def get_regime_history(db: Session = Depends(get_db)):
    """Get historical daily market regime classifications."""
    spy = db.execute(select(Asset).where(Asset.symbol == "SPY")).scalar_one_or_none()
    vix = db.execute(select(Asset).where(Asset.symbol == "^VIX")).scalar_one_or_none()

    spy_rows = db.execute(
        select(MarketPrice.trade_date, MarketPrice.close, MarketPrice.adj_close)
        .where(MarketPrice.asset_id == spy.id)
        .order_by(MarketPrice.trade_date)
    ).all()

    vix_rows = db.execute(
        select(MarketPrice.trade_date, MarketPrice.close)
        .where(MarketPrice.asset_id == vix.id)
        .order_by(MarketPrice.trade_date)
    ).all() if vix else []

    df_spy = pd.DataFrame([{"trade_date": r.trade_date, "close": r.close, "adj_close": r.adj_close} for r in spy_rows])
    df_vix = pd.DataFrame([{"trade_date": r.trade_date, "close": r.close} for r in vix_rows])

    regime_df = classify_market_regimes(df_spy, df_vix)

    # Calculate distribution
    counts = regime_df["label"].value_counts().to_dict()

    return {
        "distribution": counts,
        "history": [
            {
                "date": row["trade_date"].isoformat(),
                "label": row["label"],
                "vol_21d": row["feature_json"]["vol_21d"],
                "vol_percentile": row["feature_json"]["vol_percentile"],
                "vix": row["feature_json"]["vix"],
            }
            for _, row in regime_df.tail(250).iterrows()
        ],
    }


@router.post("/conditioned-study")
def run_conditioned_study(
    req: ConditionedStudyRequest,
    db: Session = Depends(get_db),
):
    """Run an event study conditioned on market volatility regimes."""
    # Classify regimes first
    spy = db.execute(select(Asset).where(Asset.symbol == "SPY")).scalar_one_or_none()
    vix = db.execute(select(Asset).where(Asset.symbol == "^VIX")).scalar_one_or_none()

    spy_rows = db.execute(
        select(MarketPrice.trade_date, MarketPrice.close, MarketPrice.adj_close)
        .where(MarketPrice.asset_id == spy.id)
        .order_by(MarketPrice.trade_date)
    ).all()
    vix_rows = db.execute(
        select(MarketPrice.trade_date, MarketPrice.close)
        .where(MarketPrice.asset_id == vix.id)
        .order_by(MarketPrice.trade_date)
    ).all() if vix else []

    df_spy = pd.DataFrame([{"trade_date": r.trade_date, "close": r.close, "adj_close": r.adj_close} for r in spy_rows])
    df_vix = pd.DataFrame([{"trade_date": r.trade_date, "close": r.close} for r in vix_rows])
    regime_df = classify_market_regimes(df_spy, df_vix)
    regime_map = {row["trade_date"]: row["label"] for _, row in regime_df.iterrows()}

    # Run overall event study
    study_svc = StudyService(db)
    res = study_svc.run_study(
        EventStudyRequest(
            event_type=req.event_type,
            asset_symbol=req.asset_symbol,
            benchmark_symbol="SPY" if req.asset_symbol != "SPY" else None,
            model_type="market_adjusted" if req.asset_symbol != "SPY" else "mean_adjusted",
        )
    )

    # Group event CARs by regime at release date
    regime_buckets: dict[str, list[float]] = {
        "High Vol / Risk-Off": [],
        "Low Vol / Risk-On": [],
        "Transitional / unclassified": [],
    }

    for ev in res.per_event:
        d_val = pd.to_datetime(ev.day_0_date).date()
        regime = regime_map.get(d_val, "Transitional / unclassified")
        car_val = ev.window_cars.get("[+0,+1]", 0.0)
        regime_buckets[regime].append(car_val)

    comparison = []
    import numpy as np
    for reg, cars in regime_buckets.items():
        arr = np.array(cars, dtype=float)
        mean_c = float(np.mean(arr)) if len(arr) > 0 else 0.0
        median_c = float(np.median(arr)) if len(arr) > 0 else 0.0
        std_c = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        comparison.append({
            "regime": reg,
            "count": len(arr),
            "mean_car": round(mean_c, 4),
            "median_car": round(median_c, 4),
            "std_car": round(std_c, 4),
        })

    return {
        "event_type": req.event_type,
        "asset_symbol": req.asset_symbol,
        "unit": res.unit,
        "regime_comparison": comparison,
    }
