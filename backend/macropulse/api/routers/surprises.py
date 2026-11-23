from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse.analytics.surprises import analyze_surprises
from macropulse.db.session import get_db
from macropulse.models.asset import Asset
from macropulse.models.event import ConsensusForecast, EconomicEvent
from macropulse.schemas.study import EventStudyRequest
from macropulse.services.study_service import StudyService

router = APIRouter(prefix="/surprises", tags=["Surprise Analyzer"])


class SurpriseRequest(BaseModel):
    event_type: str = "CPI"
    asset_symbol: str = "SPY"
    window_key: str = "[+0,+1]"


@router.post("/analyze")
def analyze_surprises_endpoint(
    req: SurpriseRequest,
    db: Session = Depends(get_db),
):
    """Run regression and asymmetry testing on indicator surprises vs asset reactions."""
    asset = db.execute(select(Asset).where(Asset.symbol == req.asset_symbol)).scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Run event study to get constituent event CARs
    study_svc = StudyService(db)
    study_res = study_svc.run_study(
        EventStudyRequest(
            event_type=req.event_type,
            asset_symbol=req.asset_symbol,
            benchmark_symbol="SPY" if req.asset_symbol != "SPY" else None,
            model_type="market_adjusted" if req.asset_symbol != "SPY" else "mean_adjusted",
        )
    )

    event_cars = {
        ev.event_id: ev.window_cars.get(req.window_key, 0.0)
        for ev in study_res.per_event
    }

    # Fetch event records with consensus if any
    events = (
        db.execute(
            select(EconomicEvent).where(EconomicEvent.event_type == req.event_type)
        )
        .scalars()
        .all()
    )

    ev_dicts = []
    for ev in events:
        cons = db.execute(select(ConsensusForecast).where(ConsensusForecast.event_id == ev.id)).scalar_one_or_none()
        ev_dicts.append({
            "id": ev.id,
            "event_type": ev.event_type,
            "period_date": ev.period_date,
            "actual_first_release": ev.actual_first_release,
            "previous_first_release": ev.previous_first_release,
            "change_value": ev.change_value,
            "change_std": ev.change_std,
            "consensus_value": cons.consensus_value if cons else None,
        })

    try:
        res = analyze_surprises(
            events=ev_dicts,
            event_cars=event_cars,
            asset_symbol=req.asset_symbol,
            unit=asset.unit,
        )
        return {
            "mode": res.mode,
            "asset_symbol": res.asset_symbol,
            "event_type": res.event_type,
            "window_key": req.window_key,
            "unit": asset.unit,
            "data_points": res.data_points,
            "regression": res.regression.__dict__,
            "quintile_buckets": res.quintile_buckets,
            "asymmetry": res.asymmetry.__dict__,
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
