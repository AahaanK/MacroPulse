import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse.db.session import get_db
from macropulse.models.indicator import Indicator, IndicatorVintage
from macropulse.schemas.data import IndicatorSchema
from macropulse.services.data_service import DataService

router = APIRouter(prefix="/indicators", tags=["Indicators"])


@router.get("", response_model=list[IndicatorSchema])
def list_indicators(db: Session = Depends(get_db)):
    """List macroeconomic indicators with latest values, changes, and sparklines."""
    svc = DataService(db)
    return svc.get_indicators()


@router.get("/{code}")
def get_indicator_detail(code: str, db: Session = Depends(get_db)):
    """Get single indicator details, latest release, and freshness."""
    svc = DataService(db)
    indicators = svc.get_indicators()
    matched = next((i for i in indicators if i.code.upper() == code.upper()), None)
    if not matched:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Indicator '{code}' not found."}},
        )
    return matched


@router.get("/{code}/series")
def get_indicator_series(
    code: str,
    start: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Get historical time series observations for an indicator."""
    if start and end and start > end:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_DATE_RANGE", "message": "start date must be <= end date."}},
        )
    svc = DataService(db)
    series = svc.get_indicator_series(code.upper(), start=start, end=end)
    return {"code": code.upper(), "data": series}


@router.get("/{code}/vintages")
def get_indicator_vintages(code: str, db: Session = Depends(get_db)):
    """Get ALFRED vintage revisions for an indicator."""
    ind = db.execute(select(Indicator).where(Indicator.code == code.upper())).scalar_one_or_none()
    if not ind:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Indicator '{code}' not found."}},
        )

    vintages = (
        db.execute(
            select(IndicatorVintage)
            .where(IndicatorVintage.indicator_id == ind.id)
            .order_by(IndicatorVintage.period_date, IndicatorVintage.realtime_start)
        )
        .scalars()
        .all()
    )

    return {
        "code": code.upper(),
        "vintages": [
            {
                "period_date": v.period_date.isoformat(),
                "realtime_start": v.realtime_start.isoformat(),
                "realtime_end": v.realtime_end.isoformat(),
                "value": v.value,
            }
            for v in vintages
        ],
    }
