"""Optional FastAPI adapter. Core underwriting has zero runtime dependencies."""
from __future__ import annotations

from pathlib import Path

from .calibration import walk_forward_interval_calibration
from .dossier import project_dossier
from .engine import underwrite
from .event_ledger import ledger_summary, load_event_ledger
from .guardrails import underwriting_grade
from .io import load_project, request_from_dict
from .model_risk import model_risk_report
from .physical_depth import physical_depth_report
from .readiness import calibration_readiness
from .research_priority import research_priorities

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
except ImportError as exc:
    raise RuntimeError("Install ProofMW with the 'api' extra to run the HTTP API") from exc

app = FastAPI(title="ProofMW API", version="0.4.0")
ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "fixtures" / "start-campus-sin02-public" / "project.json"
PUBLIC_LEDGER = ROOT / "data" / "europe-public-events-v2"
WEB_INDEX = ROOT / "web" / "index.html"


def _events():
    return load_event_ledger(PUBLIC_LEDGER)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB_INDEX)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.4.0"}


@app.get("/v1/demo")
def demo() -> dict:
    p = load_project(DEMO)
    return {"project": p.metadata | {"id": p.id, "name": p.name, "nameplate_mw": p.nameplate_mw}, "evidence_grade": underwriting_grade(p)}


@app.get("/v1/data/summary")
def data_summary() -> dict:
    return ledger_summary(_events())


@app.get("/v1/data/readiness")
def data_readiness() -> dict:
    return calibration_readiness(_events())


@app.get("/v1/data/calibration")
def data_calibration() -> dict:
    return walk_forward_interval_calibration(_events(), min_history=3)


@app.get("/v1/data/model-risk")
def data_model_risk() -> dict:
    return model_risk_report(_events(), min_history=3)


@app.get("/v1/data/physical-depth")
def data_physical_depth() -> dict:
    return physical_depth_report(_events())


@app.get("/v1/data/research-priorities")
def data_research_priorities() -> dict:
    return research_priorities(_events())


@app.get("/v1/projects")
def projects() -> dict:
    rows = _events()
    projects: dict[str, dict] = {}
    for row in rows:
        projects.setdefault(row.project_id, {"id": row.project_id, "name": row.project_name or row.project_id, "operator": row.operator, "country": row.country, "observations": 0})
        projects[row.project_id]["observations"] += 1
    return {"projects": sorted(projects.values(), key=lambda x: ((x["country"] or ""), x["name"]))}


@app.get("/v1/projects/{project_id}/dossier")
def api_project_dossier(project_id: str, as_of: str | None = None) -> dict:
    try:
        return project_dossier(_events(), project_id, as_of=as_of)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/underwrite")
def api_underwrite(payload: dict) -> dict:
    try:
        project = load_project(payload.get("project_path", DEMO))
        request = request_from_dict(payload["request"])
        result = underwrite(project, request)
        result["evidence_grade"] = underwriting_grade(project)
        return result
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
