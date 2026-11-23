from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from macropulse.db.session import get_db
from macropulse.ingest.pipeline import IngestionPipeline
from macropulse.schemas.data import DataStatusSummary
from macropulse.services.data_service import DataService

router = APIRouter(prefix="/data-status", tags=["Data Status"])


@router.get("", response_model=DataStatusSummary)
def get_data_status(db: Session = Depends(get_db)):
    """Summary of data coverage, integrity, provider status, and active limitations."""
    svc = DataService(db)
    return svc.get_data_status()


def _run_ingest_task():
    pipeline = IngestionPipeline()
    try:
        pipeline.ingest_all()
    finally:
        pipeline.close()


@router.post("/refresh")
def refresh_data(background_tasks: BackgroundTasks):
    """Trigger an incremental data refresh in the background."""
    background_tasks.add_task(_run_ingest_task)
    return {"status": "scheduled", "message": "Incremental data ingestion triggered."}
