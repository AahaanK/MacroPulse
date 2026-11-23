import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse.db.session import get_db
from macropulse.models.event import ConsensusForecast, EconomicEvent
from macropulse.schemas.common import PaginatedResponse
from macropulse.schemas.data import EconomicEventSchema
from macropulse.services.data_service import DataService

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=PaginatedResponse[EconomicEventSchema])
def list_events(
    event_type: str | None = Query(None, description="Filter by event type, e.g. CPI, FOMC, NFP"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    data_quality: str | None = Query(None, description="VERIFIED_TIMESTAMP, DERIVED_TIMESTAMP, DEMO"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db),
):
    """List historical macroeconomic events with pagination and filters."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_DATE_RANGE", "message": "start_date must be <= end_date."}},
        )

    svc = DataService(db)
    items, total = svc.get_events(
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        data_quality=data_quality,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse[EconomicEventSchema](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}")
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    """Get single event detail including release timestamp provenance and consensus."""
    ev = db.execute(select(EconomicEvent).where(EconomicEvent.id == event_id)).scalar_one_or_none()
    if not ev:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Event id {event_id} not found."}},
        )

    consensus = db.execute(
        select(ConsensusForecast).where(ConsensusForecast.event_id == ev.id)
    ).scalar_one_or_none()

    return {
        "id": ev.id,
        "event_type": ev.event_type,
        "country": ev.country,
        "period_date": ev.period_date.isoformat(),
        "release_ts": ev.release_ts.isoformat(),
        "timestamp_source": ev.timestamp_source,
        "actual_first_release": ev.actual_first_release,
        "previous_first_release": ev.previous_first_release,
        "actual_latest": ev.actual_latest,
        "change_value": ev.change_value,
        "change_std": ev.change_std,
        "data_quality": ev.data_quality,
        "source_id": ev.source_id,
        "consensus": (
            {
                "value": consensus.consensus_value,
                "source": consensus.source,
                "license_note": consensus.license_note,
                "imported_at": consensus.imported_at.isoformat(),
            }
            if consensus
            else None
        ),
    }
