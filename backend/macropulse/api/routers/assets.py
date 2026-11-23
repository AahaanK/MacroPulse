from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from macropulse.db.session import get_db
from macropulse.schemas.data import AssetSchema
from macropulse.services.data_service import DataService

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=list[AssetSchema])
def list_assets(db: Session = Depends(get_db)):
    """List all asset proxies in the research universe."""
    svc = DataService(db)
    return svc.get_assets()
