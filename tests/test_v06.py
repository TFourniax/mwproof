from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

import proofmw.api as api
from proofmw.dataset_snapshot import dataset_snapshot
from proofmw.dossier import project_dossier
from proofmw.event_ledger import MilestoneObservation, actual_window, ledger_fingerprint, load_event_ledger, target_revision_days
from proofmw.physical_depth import physical_depth_report
from proofmw.readiness import calibration_readiness
from proofmw.research_priority import research_priorities

LEDGER = ROOT / "data" / "europe-public-events-v2"


def _legacy_event_id(item: MilestoneObservation) -> str:
    payload = asdict(item)
    payload.pop("actual_start", None)
    payload.pop("actual_end", None)
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()[:20]


def test_old_event_identity_is_backward_compatible():
    events = load_event_ledger(LEDGER)
    old = next(x for x in events if x.project_id == "start-campus-sines" and x.actual_start is None and x.actual_end is None)
    assert old.event_id == _legacy_event_id(old)


def test_explicit_actual_bounds_override_calendar_precision():
    item = MilestoneObservation(
        project_id="bounded",
        milestone_id="operations",
        observed_on="2026-08-19",
        status="actual",
        target_start=None,
        target_end=None,
        actual_date=None,
        actual_start="2026-03-10",
        actual_end="2026-04-20",
        capacity_mw=10,
        source_url="https://example.com/evidence",
        source_class="developer-release",
        precision="year",
    )
    item.validate()
    bounds = actual_window(item)
    assert bounds is not None
    assert bounds[0].isoformat() == "2026-03-10"
    assert bounds[1].isoformat() == "2026-04-20"


def test_one_sided_explicit_actual_bounds_are_rejected():
    item = MilestoneObservation(
        project_id="bad-bounds",
        milestone_id="operations",
        observed_on="2026-08-19",
        status="actual",
        target_start=None,
        target_end=None,
        actual_date=None,
        actual_start="2026-03-10",
        actual_end=None,
        capacity_mw=None,
        source_url="https://example.com/evidence",
        source_class="developer-release",
    )
    try:
        item.validate()
    except ValueError as exc:
        assert "actual_start and actual_end" in str(exc)
    else:
        raise AssertionError("one-sided explicit bounds must not validate")


def test_confirmed_hamar_actual_is_visible_but_not_temporally_scored():
    events = load_event_ledger(LEDGER)
    dossier = project_dossier(events, "greenmountain-hamar-b1", as_of="2026-08-19")
    operations = next(x for x in dossier["milestones"] if x["milestone_id"] == "operations")
    assert operations["actual"] is not None
    assert operations["actual"]["temporally_scorable"] is False
    assert operations["slippage_interval_days"] is None
    snap = dataset_snapshot(events, as_of="2026-08-19")
    assert snap["labels"]["confirmed_actual_without_scorable_time"] >= 3
    assert not any(x["project_id"] == "greenmountain-hamar-b1" and x["milestone_id"] == "operations" for x in snap["open_forecasts"]["top_overdue"])


def test_interval_control_labels_are_conservative_and_exhaustive():
    events = load_event_ledger(LEDGER)
    readiness = calibration_readiness(events)
    labels = readiness["control_labels"]
    assert labels["certainly_early_or_on_time"] + labels["certainly_materially_delayed"] + labels["interval_ambiguous"] == readiness["gates"]["resolved_operations"]["actual"]
    assert labels["interval_ambiguous"] >= 0


def test_research_priorities_reuse_readiness_control_labels():
    events = load_event_ledger(LEDGER)
    readiness = calibration_readiness(events)
    priorities = research_priorities(events)
    labels = readiness["control_labels"]
    assert priorities["current"]["certainly_early_or_on_time_controls"] == labels["certainly_early_or_on_time"]
    assert priorities["current"]["certainly_materially_delayed_controls"] == labels["certainly_materially_delayed"]
    assert priorities["current"]["interval_ambiguous_controls"] == labels["interval_ambiguous"]
    assert priorities["gaps"]["early_or_on_time_controls"] == max(0, 25 - labels["certainly_early_or_on_time"])
    assert priorities["gaps"]["materially_delayed_controls"] == max(0, 25 - labels["certainly_materially_delayed"])


def test_followups_add_real_physical_depth_and_schedule_revisions():
    events = load_event_ledger(LEDGER)
    depth = physical_depth_report(events)
    colt = next(x for x in depth["project_details"] if x["project_id"] == "colt-hayes1")
    assert {"construction", "cooling", "power"}.issubset(set(colt["physical_types_present"]))

    ber_revisions = target_revision_days(events, "maincubes-ber02", "construction-start")
    assert ber_revisions
    assert ber_revisions[-1]["new_target_midpoint"].startswith("2026-")

    madrid_revisions = target_revision_days(events, "ironmountain-mad1", "operations")
    assert madrid_revisions
    assert madrid_revisions[-1]["new_target_midpoint"].startswith("2027-")


def test_ledger_snapshot_hash_matches_loaded_events():
    events = load_event_ledger(LEDGER)
    snap = dataset_snapshot(events, as_of="2026-08-19")
    assert snap["ledger_sha256"] == ledger_fingerprint(events)


def test_api_rejects_path_traversal_and_bad_dates():
    client = TestClient(api.app)
    traversal = client.post(
        "/v1/underwrite",
        json={"fixture": "../README.md", "request": {"as_of_dates": ["2026-08-19"]}},
    )
    assert traversal.status_code == 422
    assert "escapes fixtures" in traversal.json()["detail"]

    bad_date = client.get("/v1/search?as_of=not-a-date")
    assert bad_date.status_code == 422


def test_optional_api_key_protects_product_surface(monkeypatch):
    monkeypatch.setattr(api, "API_KEY", "proofmw-test-key")
    client = TestClient(api.app)
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 401
    allowed = client.get("/ready", headers={"X-API-Key": "proofmw-test-key"})
    assert allowed.status_code == 200
    assert allowed.json()["ready"] is True
