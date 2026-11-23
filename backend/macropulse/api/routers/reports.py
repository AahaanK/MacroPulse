from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from macropulse.db.session import get_db
from macropulse.reports.pdf_generator import generate_study_pdf
from macropulse.services.study_service import StudyService

router = APIRouter(prefix="/reports", tags=["Reports"])


class GenerateReportRequest(BaseModel):
    study_id: int


@router.post("/generate")
def generate_report_json(req: GenerateReportRequest, db: Session = Depends(get_db)):
    svc = StudyService(db)
    res = svc.get_result(req.study_id)
    if not res:
        raise HTTPException(status_code=404, detail="Study result not found.")
    return res


@router.get("/{study_id}.pdf")
def export_report_pdf(study_id: int, db: Session = Depends(get_db)):
    """Generate and download publication-ready ReportLab PDF report."""
    svc = StudyService(db)
    res = svc.get_result(study_id)
    if not res:
        raise HTTPException(status_code=404, detail="Study result not found.")

    study_dict = res.model_dump()
    pdf_bytes = generate_study_pdf(study_dict)

    filename = f"MacroPulse_Report_{res.event_type}_{res.asset_symbol}_{res.config_hash[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{study_id}.csv")
def export_report_csv(study_id: int, db: Session = Depends(get_db)):
    """Generate and download study constituent CAR series CSV."""
    svc = StudyService(db)
    res = svc.get_result(study_id)
    if not res:
        raise HTTPException(status_code=404, detail="Study result not found.")

    headers = ["event_id", "period_date", "day_0_date", "car_0_1", "model_alpha", "model_beta", "is_intraday"]
    rows = [headers]
    for ev in res.per_event:
        car_val = ev.window_cars.get("[+0,+1]", 0.0)
        rows.append([
            str(ev.event_id),
            ev.period_date,
            ev.day_0_date,
            str(car_val),
            str(ev.model_alpha),
            str(ev.model_beta),
            str(ev.is_intraday_release),
        ])

    csv_data = "\n".join([",".join(r) for r in rows])
    filename = f"MacroPulse_Data_{res.event_type}_{res.asset_symbol}_{res.config_hash[:8]}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
