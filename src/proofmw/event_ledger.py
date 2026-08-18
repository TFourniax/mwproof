from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any


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

    def validate(self) -> None:
        date.fromisoformat(self.observed_on)
        for value in (self.target_start, self.target_end, self.actual_date):
            if value:
                date.fromisoformat(value)
        if self.target_start and self.target_end and self.target_start > self.target_end:
            raise ValueError("target_start must be <= target_end")


def load_event_ledger(path: str | Path) -> list[MilestoneObservation]:
    raw: list[dict[str, Any]] = json.loads(Path(path).read_text(encoding="utf-8"))
    items = [MilestoneObservation(**row) for row in raw]
    for item in items:
        item.validate()
    return items


def _midpoint(start: str | None, end: str | None) -> date | None:
    if not start and not end:
        return None
    a = date.fromisoformat(start or end)  # type: ignore[arg-type]
    b = date.fromisoformat(end or start)  # type: ignore[arg-type]
    return a + (b - a) / 2


def target_revision_days(items: list[MilestoneObservation], project_id: str, milestone_id: str) -> list[dict[str, Any]]:
    rows = sorted(
        [x for x in items if x.project_id == project_id and x.milestone_id == milestone_id and (x.target_start or x.target_end)],
        key=lambda x: x.observed_on,
    )
    revisions: list[dict[str, Any]] = []
    for before, after in zip(rows, rows[1:]):
        old = _midpoint(before.target_start, before.target_end)
        new = _midpoint(after.target_start, after.target_end)
        if old is None or new is None:
            continue
        revisions.append({
            "project_id": project_id,
            "milestone_id": milestone_id,
            "observed_from": before.observed_on,
            "observed_to": after.observed_on,
            "revision_days": (new - old).days,
            "old_target_midpoint": old.isoformat(),
            "new_target_midpoint": new.isoformat(),
        })
    return revisions


def actual_slippage_days(items: list[MilestoneObservation], project_id: str, milestone_id: str) -> int | None:
    rows = sorted([x for x in items if x.project_id == project_id and x.milestone_id == milestone_id], key=lambda x: x.observed_on)
    if not rows:
        return None
    earliest_target = next((_midpoint(x.target_start, x.target_end) for x in rows if x.target_start or x.target_end), None)
    actual = next((date.fromisoformat(x.actual_date) for x in reversed(rows) if x.actual_date), None)
    if earliest_target is None or actual is None:
        return None
    return (actual - earliest_target).days
