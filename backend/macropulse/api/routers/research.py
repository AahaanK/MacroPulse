import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from macropulse.db.session import get_db
from macropulse.models.research import ProjectStudy, ResearchNote, ResearchProject
from macropulse.models.study import StudyConfig, StudyResult
from macropulse.schemas.study import EventStudyRequest
from macropulse.services.study_service import StudyService

router = APIRouter(prefix="/research", tags=["Research Workspace"])


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class NoteCreate(BaseModel):
    project_id: int
    result_id: int | None = None
    body_md: str


class CompareRequest(BaseModel):
    study_ids: list[int]


class RobustnessRequest(BaseModel):
    event_type: str = "CPI"
    asset_symbol: str = "SPY"


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    projects = db.execute(select(ResearchProject).order_by(desc(ResearchProject.updated_at))).scalars().all()
    res = []
    for p in projects:
        study_count = len(p.studies)
        note_count = len(p.notes)
        res.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "study_count": study_count,
            "note_count": note_count,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        })
    return res


@router.post("/projects")
def create_project(req: ProjectCreate, db: Session = Depends(get_db)):
    p = ResearchProject(name=req.name, description=req.description)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name, "description": p.description}


@router.get("/saved-studies")
def list_saved_studies(db: Session = Depends(get_db)):
    """List executed studies with summary metrics."""
    studies = db.execute(select(StudyResult).order_by(desc(StudyResult.created_at)).limit(50)).scalars().all()
    res = []
    for s in studies:
        cfg = s.config
        summary = s.summary_json
        res.append({
            "id": s.id,
            "name": cfg.name,
            "config": cfg.config_json,
            "primary_verdict": summary.get("primary_verdict"),
            "n_included": summary.get("n_included"),
            "created_at": s.created_at.isoformat(),
        })
    return res


@router.post("/notes")
def add_note(req: NoteCreate, db: Session = Depends(get_db)):
    note = ResearchNote(
        project_id=req.project_id,
        result_id=req.result_id,
        body_md=req.body_md,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "body_md": note.body_md, "created_at": note.created_at.isoformat()}


@router.get("/notes")
def get_notes(project_id: int | None = None, db: Session = Depends(get_db)):
    query = select(ResearchNote)
    if project_id:
        query = query.where(ResearchNote.project_id == project_id)
    notes = db.execute(query.order_by(desc(ResearchNote.created_at))).scalars().all()
    return [
        {
            "id": n.id,
            "project_id": n.project_id,
            "result_id": n.result_id,
            "body_md": n.body_md,
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ]


@router.post("/compare")
def compare_studies(req: CompareRequest, db: Session = Depends(get_db)):
    """Side-by-side comparison of 2-4 studies."""
    if len(req.study_ids) < 2 or len(req.study_ids) > 4:
        raise HTTPException(status_code=422, detail="Provide between 2 and 4 study IDs to compare.")

    svc = StudyService(db)
    studies = []
    for s_id in req.study_ids:
        res = svc.get_result(s_id)
        if res:
            studies.append(res)

    return {"studies": studies}


@router.post("/robustness")
def run_robustness_lab(req: RobustnessRequest, db: Session = Depends(get_db)):
    """Re-run study across alternative estimation windows, benchmarks, and models to test hypothesis stability."""
    svc = StudyService(db)

    variations = [
        {"name": "Baseline (Market Adjusted)", "model": "market_adjusted", "est": [-260, -11], "bm": "SPY"},
        {"name": "Market Model (OLS α,β)", "model": "market_model", "est": [-260, -11], "bm": "SPY"},
        {"name": "Mean Adjusted (Constant Mean)", "model": "mean_adjusted", "est": [-260, -11], "bm": None},
        # 130 trading days: the engine needs at least 120 valid days (min_estimation_obs), so the
        # previous [-120, -11] window (110 days) silently excluded every event.
        {"name": "Shorter Est Window (130d)", "model": "market_adjusted", "est": [-140, -11], "bm": "SPY"},
        {"name": "Alternative Benchmark (QQQ)", "model": "market_adjusted", "est": [-260, -11], "bm": "QQQ"},
    ]

    results = []
    for v in variations:
        try:
            r = svc.run_study(
                EventStudyRequest(
                    event_type=req.event_type,
                    asset_symbol=req.asset_symbol,
                    benchmark_symbol=v["bm"],
                    model_type=v["model"],
                    estimation_window=v["est"],
                )
            )
            w_stat = r.window_stats.get("[+0,+1]")
            if w_stat:
                results.append({
                    "variation": v["name"],
                    "model": v["model"],
                    "n_events": w_stat.n_events,
                    "mean_car": w_stat.mean_car,
                    "t_stat": w_stat.t_stat,
                    "p_value": w_stat.p_value_t,
                    "is_significant": w_stat.p_value_t < 0.05,
                    "conclusion": "Statistically Distinguishable" if w_stat.p_value_t < 0.05 else "Not Distinguishable",
                })
        except Exception:
            continue

    return {
        "event_type": req.event_type,
        "asset_symbol": req.asset_symbol,
        "results": results,
    }
