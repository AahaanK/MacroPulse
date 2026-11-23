from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from macropulse.db.session import get_db
from macropulse.schemas.study import EventStudyRequest, EventStudyResponse
from macropulse.services.study_service import StudyService

router = APIRouter(prefix="/event-studies", tags=["Event Studies"])


@router.get("/defaults")
def get_study_defaults():
    """Default parameters for the flagship Event Study Lab."""
    return {
        "event_type": "CPI",
        "asset_symbol": "SPY",
        "benchmark_symbol": "SPY",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "event_window": [-1, 3],
        "estimation_window": [-260, -11],
        "return_method": "simple",
        "model_type": "market_adjusted",
        "use_first_release": True,
        "exclude_overlapping": False,
        "seed": 42,
    }


@router.post("/run", response_model=EventStudyResponse)
def run_event_study_endpoint(
    req: EventStudyRequest,
    db: Session = Depends(get_db),
):
    """Run an event study and persist results and configuration."""
    svc = StudyService(db)
    try:
        return svc.run_study(req)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "STUDY_EXECUTION_ERROR", "message": str(e)}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": f"Event study failed: {str(e)}"}},
        )


@router.get("/{result_id}", response_model=EventStudyResponse)
def get_study_result_endpoint(
    result_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a previously executed study result by ID."""
    svc = StudyService(db)
    res = svc.get_result(result_id)
    if not res:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Study result id {result_id} not found."}},
        )
    return res
