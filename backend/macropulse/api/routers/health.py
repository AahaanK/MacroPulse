from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from macropulse.config import settings
from macropulse.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check for application status and database connectivity."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_connected": db_ok,
        "data_mode": "LIVE" if settings.FRED_API_KEY else "DEMO",
    }
