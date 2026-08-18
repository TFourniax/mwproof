"""Optional FastAPI adapter. Core underwriting has zero runtime dependencies."""
from __future__ import annotations

from pathlib import Path

from .engine import underwrite
from .guardrails import underwriting_grade
from .io import load_project, request_from_dict

try:
    from fastapi import FastAPI, HTTPException
except ImportError as exc:
    raise RuntimeError("Install ProofMW with the 'api' extra to run the HTTP API") from exc

app = FastAPI(title="ProofMW API", version="0.1.0")
ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "fixtures" / "start-campus-sin02-public" / "project.json"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/v1/demo")
def demo() -> dict:
    p = load_project(DEMO)
    return {"project": p.metadata | {"id": p.id, "name": p.name, "nameplate_mw": p.nameplate_mw}, "evidence_grade": underwriting_grade(p)}


@app.post("/v1/underwrite")
def api_underwrite(payload: dict) -> dict:
    try:
        project = load_project(payload.get("project_path", DEMO))
        request = request_from_dict(payload["request"])
        return underwrite(project, request)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
