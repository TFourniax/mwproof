from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

SOURCE_WEIGHTS: dict[str, float] = {
    "government": 1.00,
    "regulator": 1.00,
    "grid-operator": 1.00,
    "company-filing": 0.98,
    "developer-oem-announcement": 0.95,
    "developer-release": 0.95,
    "developer": 0.90,
    "oem": 0.90,
    "specialist-monitor": 0.80,
    "mainstream-press": 0.75,
    "trade-press": 0.70,
    "other": 0.50,
}

TERMINAL_NEGATIVE = {"canceled", "denied", "withdrawn"}
FORECAST_STATUSES = {"forecast", "revised_forecast", "conflicting_forecast", "delayed"}


@dataclass(frozen=True)
class MilestoneObservation:
    project_id: str
    milestone_id: str
    observed_on: str
    status: str
    target_start: str | None
    target_end: str | None
    actual_date: str | None
    capacity_mw: float | None
    source_url: str
    source_class: str
    notes: str = ""
    project_name: str | None = None
    operator: str | None = None
    country: str | None = None
    milestone_type: str | None = None
    source_title: str = ""
    precision: str = "day"

    def validate(self) -> None:
        date.fromisoformat(self.observed_on)
        for value in (self.target_start, self.target_end, self.actual_date):
            if value:
                date.fromisoformat(value)
        if self.target_start and self.target_end and self.target_start > self.target_end:
            raise ValueError("target_start must be <= target_end")
        if self.capacity_mw is not None and self.capacity_mw < 0:
            raise ValueError("capacity_mw must be non-negative")
        if not self.source_url.startswith("https://"):
            raise ValueError("source_url must use https")

    @property
    def source_weight(self) -> float:
        return SOURCE_WEIGHTS.get(self.source_class, SOURCE_WEIGHTS["other"])

    @property
    def event_id(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _expand_manifest(raw: dict[str, Any]) -> list[dict[str, Any]]:
    if raw.get("schema_version") != "1.0":
        raise ValueError("unsupported event-ledger schema_version")
    projects = raw.get("projects", {})
    sources = raw.get("sources", {})
    output: list[dict[str, Any]] = []
    for event in raw.get("events", []):
        project = projects[event["p"]]
        source = sources[event["src"]]
        output.append({
            "project_id": event["p"],
            "project_name": project.get("name"),
            "operator": project.get("operator"),
            "country": project.get("country"),
            "milestone_id": event["m"],
            "milestone_type": event.get("type"),
            "observed_on": event["observed"],
            "status": event["status"],
            "target_start": event.get("target_start"),
            "target_end": event.get("target_end"),
            "actual_date": event.get("actual"),
            "capacity_mw": event.get("mw"),
            "source_url": source["url"],
            "source_class": source["class"],
            "source_title": source.get("title", ""),
            "precision": event.get("precision", "day"),
            "notes": event.get("notes", ""),
        })
    return output


def _rows_from_path(path: Path) -> list[dict[str, Any]]:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return _expand_manifest(raw)
    if isinstance(raw, list):
        return raw
    raise ValueError(f"{path}: event ledger must be a list or v1 manifest")


def load_event_ledger(path: str | Path) -> list[MilestoneObservation]:
    source = Path(path)
    if source.is_dir():
        files = sorted(p for p in source.glob("*.json") if p.is_file())
        if not files:
            raise ValueError(f"{source}: no JSON ledger shards found")
        rows = [row for file in files for row in _rows_from_path(file)]
    else:
        rows = _rows_from_path(source)

    items = [MilestoneObservation(**row) for row in rows]
    seen: set[str] = set()
    for item in items:
        item.validate()
        if item.event_id in seen:
            raise ValueError(f"duplicate event across ledger: {item.event_id}")
        seen.add(item.event_id)
    return items


def _midpoint(start: str | None, end: str | None) -> date | None:
    if not start and not end:
        return None
    a = date.fromisoformat(start or end)  # type: ignore[arg-type]
    b = date.fromisoformat(end or start)  # type: ignore[arg-type]
    return a + (b - a) / 2


def snapshot_as_of(items: Iterable[MilestoneObservation], cutoff: str) -> list[MilestoneObservation]:
    """Return only observations that were knowable by cutoff.

    This is the core anti-look-ahead guardrail for historical backtests.
    """
    limit = date.fromisoformat(cutoff)
    return [x for x in items if date.fromisoformat(x.observed_on) <= limit]


def timeline(items: Iterable[MilestoneObservation], project_id: str, milestone_id: str | None = None) -> list[MilestoneObservation]:
    rows = [x for x in items if x.project_id == project_id and (milestone_id is None or x.milestone_id == milestone_id)]
    return sorted(rows, key=lambda x: (x.observed_on, x.milestone_id, x.event_id))


def target_revision_days(items: list[MilestoneObservation], project_id: str, milestone_id: str) -> list[dict[str, Any]]:
    rows = sorted(
        [x for x in items if x.project_id == project_id and x.milestone_id == milestone_id and (x.target_start or x.target_end) and x.status in FORECAST_STATUSES],
        key=lambda x: (x.observed_on, -x.source_weight),
    )
    revisions: list[dict[str, Any]] = []
    previous: MilestoneObservation | None = None
    for current in rows:
        if previous is None:
            previous = current
            continue
        # Same-day multi-source claims are conflicts, not chronological revisions.
        if current.observed_on == previous.observed_on:
            continue
        old = _midpoint(previous.target_start, previous.target_end)
        new = _midpoint(current.target_start, current.target_end)
        if old is None or new is None:
            previous = current
            continue
        delta_days = (new - old).days
        if delta_days != 0:
            revisions.append({
                "project_id": project_id,
                "milestone_id": milestone_id,
                "observed_from": previous.observed_on,
                "observed_to": current.observed_on,
                "revision_days": delta_days,
                "old_target_midpoint": old.isoformat(),
                "new_target_midpoint": new.isoformat(),
                "source_from": previous.source_url,
                "source_to": current.source_url,
            })
        previous = current
    return revisions


def _precision_window(anchor: str, precision: str) -> tuple[date, date]:
    d = date.fromisoformat(anchor)
    if precision == "day":
        return d, d
    if precision == "month":
        start = d.replace(day=1)
        if start.month == 12:
            end = date(start.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(start.year, start.month + 1, 1) - timedelta(days=1)
        return start, end
    if precision == "quarter":
        q_month = ((d.month - 1) // 3) * 3 + 1
        start = date(d.year, q_month, 1)
        if q_month == 10:
            end = date(d.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(d.year, q_month + 3, 1) - timedelta(days=1)
        return start, end
    if precision == "half-year":
        start = date(d.year, 1 if d.month <= 6 else 7, 1)
        end = (date(d.year, 7, 1) - timedelta(days=1)) if start.month == 1 else date(d.year, 12, 31)
        return start, end
    if precision == "year":
        return date(d.year, 1, 1), date(d.year, 12, 31)
    raise ValueError(f"unsupported precision: {precision}")


def actual_window(item: MilestoneObservation) -> tuple[date, date] | None:
    if not item.actual_date:
        return None
    return _precision_window(item.actual_date, item.precision)


def actual_slippage_interval_days(items: list[MilestoneObservation], project_id: str, milestone_id: str) -> dict[str, int] | None:
    rows = timeline(items, project_id, milestone_id)
    if not rows:
        return None
    forecast = next((x for x in rows if (x.target_start or x.target_end) and x.status in FORECAST_STATUSES), None)
    actual = next((x for x in reversed(rows) if x.status == "actual" and x.actual_date), None)
    if forecast is None or actual is None:
        return None
    target_start = date.fromisoformat(forecast.target_start or forecast.target_end)  # type: ignore[arg-type]
    target_end = date.fromisoformat(forecast.target_end or forecast.target_start)  # type: ignore[arg-type]
    actual_bounds = actual_window(actual)
    if actual_bounds is None:
        return None
    actual_start, actual_end = actual_bounds
    target_mid = target_start + (target_end - target_start) / 2
    actual_mid = actual_start + (actual_end - actual_start) / 2
    return {
        "low": (actual_start - target_end).days,
        "mid": (actual_mid - target_mid).days,
        "high": (actual_end - target_start).days,
    }


def capacity_revisions(items: list[MilestoneObservation], project_id: str, milestone_id: str) -> list[dict[str, Any]]:
    rows = sorted(
        [x for x in items if x.project_id == project_id and x.milestone_id == milestone_id and x.capacity_mw is not None and x.status in FORECAST_STATUSES],
        key=lambda x: (x.observed_on, -x.source_weight),
    )
    revisions: list[dict[str, Any]] = []
    previous: MilestoneObservation | None = None
    for current in rows:
        if previous is None:
            previous = current
            continue
        if current.observed_on == previous.observed_on:
            continue
        old = float(previous.capacity_mw or 0.0)
        new = float(current.capacity_mw or 0.0)
        if new != old:
            revisions.append({
                "project_id": project_id,
                "milestone_id": milestone_id,
                "observed_from": previous.observed_on,
                "observed_to": current.observed_on,
                "old_capacity_mw": old,
                "new_capacity_mw": new,
                "delta_mw": new - old,
                "delta_ratio": round((new - old) / old, 6) if old else None,
                "source_from": previous.source_url,
                "source_to": current.source_url,
            })
        previous = current
    return revisions


def actual_slippage_days(items: list[MilestoneObservation], project_id: str, milestone_id: str) -> int | None:
    interval = actual_slippage_interval_days(items, project_id, milestone_id)
    return interval["mid"] if interval else None


def detect_source_conflicts(items: Iterable[MilestoneObservation], target_tolerance_days: int = 60, capacity_tolerance_ratio: float = 0.15) -> list[dict[str, Any]]:
    """Detect materially different same-day claims for the same milestone.

    Conflicts are preserved rather than silently choosing a preferred source.
    """
    grouped: dict[tuple[str, str, str], list[MilestoneObservation]] = defaultdict(list)
    for item in items:
        if item.target_start or item.target_end or item.capacity_mw is not None:
            grouped[(item.project_id, item.milestone_id, item.observed_on)].append(item)

    conflicts: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        if len(rows) < 2:
            continue
        target_dates = [(r, _midpoint(r.target_start, r.target_end)) for r in rows]
        target_values = [d for _, d in target_dates if d is not None]
        target_spread = (max(target_values) - min(target_values)).days if len(target_values) >= 2 else 0
        capacities = [r.capacity_mw for r in rows if r.capacity_mw is not None]
        capacity_ratio = 0.0
        if len(capacities) >= 2 and max(capacities) > 0:
            capacity_ratio = (max(capacities) - min(capacities)) / max(capacities)
        if target_spread > target_tolerance_days or capacity_ratio > capacity_tolerance_ratio:
            conflicts.append({
                "project_id": key[0],
                "milestone_id": key[1],
                "observed_on": key[2],
                "target_spread_days": target_spread,
                "capacity_spread_ratio": round(capacity_ratio, 4),
                "claims": [
                    {
                        "source_class": r.source_class,
                        "source_weight": r.source_weight,
                        "source_url": r.source_url,
                        "target_start": r.target_start,
                        "target_end": r.target_end,
                        "capacity_mw": r.capacity_mw,
                    }
                    for r in sorted(rows, key=lambda x: -x.source_weight)
                ],
            })
    return sorted(conflicts, key=lambda x: (x["project_id"], x["milestone_id"], x["observed_on"]))


def resolved_forecast_pairs(items: Iterable[MilestoneObservation]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[MilestoneObservation]] = defaultdict(list)
    for item in items:
        grouped[(item.project_id, item.milestone_id)].append(item)

    pairs: list[dict[str, Any]] = []
    for (project_id, milestone_id), rows in grouped.items():
        ordered = sorted(rows, key=lambda x: x.observed_on)
        forecast = next((x for x in ordered if (x.target_start or x.target_end) and x.status in FORECAST_STATUSES), None)
        actual = next((x for x in reversed(ordered) if x.status == "actual" and x.actual_date), None)
        if not forecast or not actual:
            continue
        target = _midpoint(forecast.target_start, forecast.target_end)
        if target is None:
            continue
        bounds = actual_window(actual)
        if bounds is None:
            continue
        actual_start, actual_end = bounds
        actual_mid = actual_start + (actual_end - actual_start) / 2
        target_start = date.fromisoformat(forecast.target_start or forecast.target_end)  # type: ignore[arg-type]
        target_end = date.fromisoformat(forecast.target_end or forecast.target_start)  # type: ignore[arg-type]
        pairs.append({
            "project_id": project_id,
            "project_name": forecast.project_name or actual.project_name,
            "operator": forecast.operator or actual.operator,
            "country": forecast.country or actual.country,
            "milestone_id": milestone_id,
            "milestone_type": forecast.milestone_type or actual.milestone_type,
            "forecast_observed_on": forecast.observed_on,
            "forecast_target_midpoint": target.isoformat(),
            "actual_date": actual.actual_date,
            "actual_window_start": actual_start.isoformat(),
            "actual_window_end": actual_end.isoformat(),
            "slippage_days": (actual_mid - target).days,
            "slippage_low_days": (actual_start - target_end).days,
            "slippage_high_days": (actual_end - target_start).days,
            "forecast_source_class": forecast.source_class,
            "forecast_source_weight": forecast.source_weight,
        })
    return sorted(pairs, key=lambda x: (x["actual_date"], x["project_id"], x["milestone_id"]))


def ledger_fingerprint(items: Iterable[MilestoneObservation]) -> str:
    """Stable root over immutable observation identifiers."""
    event_ids = sorted(x.event_id for x in items)
    payload = "\n".join(event_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def ledger_summary(items: Iterable[MilestoneObservation]) -> dict[str, Any]:
    rows = list(items)
    projects = {x.project_id for x in rows}
    countries = {x.country for x in rows if x.country}
    milestones = {(x.project_id, x.milestone_id) for x in rows}
    revisions = []
    cap_revisions = []
    for project_id, milestone_id in milestones:
        revisions.extend(target_revision_days(rows, project_id, milestone_id))
        cap_revisions.extend(capacity_revisions(rows, project_id, milestone_id))
    resolved = resolved_forecast_pairs(rows)
    negatives = [x for x in rows if x.status in TERMINAL_NEGATIVE]
    return {
        "ledger_sha256": ledger_fingerprint(rows),
        "observations": len(rows),
        "projects": len(projects),
        "countries": len(countries),
        "milestones": len(milestones),
        "resolved_forecast_pairs": len(resolved),
        "target_revisions": len(revisions),
        "capacity_revisions": len(cap_revisions),
        "source_conflicts": len(detect_source_conflicts(rows)),
        "terminal_negative_events": len(negatives),
        "source_classes": dict(sorted(Counter(x.source_class for x in rows).items())),
        "statuses": dict(sorted(Counter(x.status for x in rows).items())),
        "country_counts": dict(sorted(Counter(x.country for x in rows if x.country).items())),
    }
