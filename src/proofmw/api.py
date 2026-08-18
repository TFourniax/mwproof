"""Optional FastAPI adapter. Core underwriting has zero runtime dependencies."""
from __future__ import annotations

from pathlib import Path

from .dossier import project_dossier
from .engine import underwrite
from .event_ledger import ledger_summary, load_event_ledger
from .guardrails import underwriting_grade
from .io import load_project, request_from_dict
from .readiness import calibration_readiness
from .research_priority import research_priorities

try:
    from fastapi import FastAPI, HTTPException
except ImportError as exc:
    raise RuntimeError("Install ProofMW with the 'api' extra to run the HTTP API") from exc

app = FastAPI(title="ProofMW API", version="0.3.0")
ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "fixtures" / "start-campus-sin02-public" / "project.json"
PUBLIC_LEDGER = ROOT / "data" / "europe-public-events-v2"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.3.0"}


@app.get("/v1/demo")
def demo() -> dict:
    p = load_project(DEMO)
    return {"project": p.metadata | {"id": p.id, "name": p.name, "nameplate_mw": p.nameplate_mw}, "evidence_grade": underwriting_grade(p)}


@app.get("/v1/data/summary")
def data_summary() -> dict:
    return ledger_summary(load_event_ledger(PUBLIC_LEDGER))


@app.get("/v1/data/readiness")
def data_readiness() -> dict:
    return calibration_readiness(load_event_ledger(PUBLIC_LEDGER))


@app.get("/v1/data/research-priorities")
def data_research_priorities() -> dict:
    return research_priorities(load_event_ledger(PUBLIC_LEDGER))


@app.get("/v1/projects/{project_id}/dossier")
def api_project_dossier(project_id: str, as_of: str | None = None) -> dict:
    try:
        return project_dossier(load_event_ledger(PUBLIC_LEDGER), project_id, as_of=as_of)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/underwrite")
def api_underwrite(payload: dict) -> dict:
    try:
        project = load_project(payload.get("project_path", DEMO))
        request = request_from_dict(payload["request"])
        return underwrite(project, request)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
