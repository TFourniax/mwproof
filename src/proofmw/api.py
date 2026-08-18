"""FastAPI serving adapter for the ProofMW research/product build."""
from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path

from .calibration import walk_forward_interval_calibration
from .conditional import walk_forward_conditional_benchmark
from .dataset_snapshot import dataset_snapshot
from .decision_card import project_decision_card
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
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import FileResponse
except ImportError as exc:
    raise RuntimeError("Install ProofMW with the 'api' extra to run the HTTP API") from exc

VERSION = "0.5.0"
app = FastAPI(title="ProofMW API", version=VERSION)


def _discover_root() -> Path:
    """Locate runtime assets in source checkouts and packaged/container installs."""
    candidates: list[Path] = []
    configured = os.getenv("PROOFMW_ROOT")
    if configured:
        candidates.append(Path(configured))
    candidates.extend([Path.cwd(), Path(__file__).resolve().parents[2]])
    seen: set[Path] = set()
    for candidate in candidates:
        root = candidate.resolve()
        if root in seen:
            continue
        seen.add(root)
        if (root / "data" / "europe-public-events-v2").is_dir() and (root / "web" / "index.html").is_file():
            return root
    searched = ", ".join(str(x.resolve()) for x in candidates)
    raise RuntimeError(
        "ProofMW runtime assets not found. Set PROOFMW_ROOT to a directory "
        f"containing data/, fixtures/ and web/. Searched: {searched}"
    )


ROOT = _discover_root()
DEMO = ROOT / "fixtures" / "start-campus-sin02-public" / "project.json"
PUBLIC_LEDGER = ROOT / "data" / "europe-public-events-v2"
WEB_INDEX = ROOT / "web" / "index.html"


@lru_cache(maxsize=1)
def _events():
    # Immutable JSON shards are the canonical source; cache only the parsed view.
    return tuple(load_event_ledger(PUBLIC_LEDGER))


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB_INDEX)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


@app.get("/ready")
def ready() -> dict:
    events = _events()
    readiness = calibration_readiness(events)
    risk = model_risk_report(events, min_history=3)
    summary = ledger_summary(events)
    return {
        "ready": True,
        "version": VERSION,
        "service_mode": "PUBLISHABLE_MODEL" if risk["publishable_levels"] else "EVIDENCE_ONLY",
        "dataset_status": readiness["status"],
        "model_risk_status": risk["status"],
        "ledger_sha256": summary["ledger_sha256"],
    }


@app.get("/v1/demo")
def demo() -> dict:
    p = load_project(DEMO)
    return {
        "project": p.metadata
        | {"id": p.id, "name": p.name, "nameplate_mw": p.nameplate_mw},
        "evidence_grade": underwriting_grade(p),
    }


@app.get("/v1/data/summary")
def data_summary() -> dict:
    return ledger_summary(_events())


@app.get("/v1/data/snapshot")
def data_snapshot(as_of: str | None = None) -> dict:
    try:
        return dataset_snapshot(_events(), as_of=as_of)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/v1/data/readiness")
def data_readiness() -> dict:
    return calibration_readiness(_events())


@app.get("/v1/data/calibration")
def data_calibration() -> dict:
    return walk_forward_interval_calibration(_events(), min_history=3)


@app.get("/v1/data/conditional-benchmark")
def data_conditional_benchmark(
    min_history: int = Query(default=5, ge=2, le=100),
    min_segment: int = Query(default=2, ge=2, le=50),
) -> dict:
    return walk_forward_conditional_benchmark(
        _events(), min_history=min_history, min_segment=min_segment
    )


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
        projects.setdefault(
            row.project_id,
            {
                "id": row.project_id,
                "name": row.project_name or row.project_id,
                "operator": row.operator,
                "country": row.country,
                "observations": 0,
            },
        )
        projects[row.project_id]["observations"] += 1
    return {
        "projects": sorted(
            projects.values(),
            key=lambda x: ((x["country"] or ""), x["name"]),
        )
    }


@app.get("/v1/search")
def search_events(
    project_id: str | None = None,
    operator: str | None = None,
    country: str | None = None,
    milestone_type: str | None = None,
    status: str | None = None,
    as_of: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    rows = list(_events())
    filters = {
        "project_id": project_id,
        "operator": operator,
        "country": country,
        "milestone_type": milestone_type,
        "status": status,
    }
    for field, value in filters.items():
        if value is not None:
            rows = [x for x in rows if getattr(x, field) == value]
    if as_of is not None:
        rows = [x for x in rows if x.observed_on <= as_of]
    rows.sort(key=lambda x: (x.observed_on, x.event_id), reverse=True)
    payload = [
        {
            "event_id": x.event_id,
            "project_id": x.project_id,
            "project_name": x.project_name,
            "operator": x.operator,
            "country": x.country,
            "milestone_id": x.milestone_id,
            "milestone_type": x.milestone_type,
            "observed_on": x.observed_on,
            "status": x.status,
            "target_start": x.target_start,
            "target_end": x.target_end,
            "actual_date": x.actual_date,
            "capacity_mw": x.capacity_mw,
            "source_url": x.source_url,
            "source_class": x.source_class,
            "precision": x.precision,
        }
        for x in rows[:limit]
    ]
    return {
        "total_matches": len(rows),
        "returned": len(payload),
        "events": payload,
    }


@app.get("/v1/projects/{project_id}/dossier")
def api_project_dossier(project_id: str, as_of: str | None = None) -> dict:
    try:
        return project_dossier(_events(), project_id, as_of=as_of)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/v1/projects/{project_id}/decision-card")
def api_project_decision_card(project_id: str, as_of: str | None = None) -> dict:
    try:
        return project_decision_card(_events(), project_id, as_of=as_of)
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
