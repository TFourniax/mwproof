from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
import sqlite3
from typing import Any, Iterable

from .event_ledger import MilestoneObservation, ledger_fingerprint

_COLUMNS = (
    "event_id", "project_id", "project_name", "operator", "country",
    "milestone_id", "milestone_type", "observed_on", "status",
    "target_start", "target_end", "actual_date", "actual_start", "actual_end",
    "capacity_mw", "source_url", "source_class", "source_title", "precision", "notes",
)


def build_sqlite_index(items: Iterable[MilestoneObservation], output: str | Path) -> dict[str, Any]:
    """Materialize a disposable SQLite query index from canonical JSON evidence."""
    rows = list(items)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    db = sqlite3.connect(path)
    try:
        db.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE events (
              event_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              project_name TEXT,
              operator TEXT,
              country TEXT,
              milestone_id TEXT NOT NULL,
              milestone_type TEXT,
              observed_on TEXT NOT NULL,
              status TEXT NOT NULL,
              target_start TEXT,
              target_end TEXT,
              actual_date TEXT,
              actual_start TEXT,
              actual_end TEXT,
              capacity_mw REAL,
              source_url TEXT NOT NULL,
              source_class TEXT NOT NULL,
              source_title TEXT,
              precision TEXT NOT NULL,
              notes TEXT NOT NULL
            );
            CREATE INDEX idx_events_project ON events(project_id, observed_on);
            CREATE INDEX idx_events_operator ON events(operator, observed_on);
            CREATE INDEX idx_events_country ON events(country, observed_on);
            CREATE INDEX idx_events_type ON events(milestone_type, observed_on);
            CREATE INDEX idx_events_status ON events(status, observed_on);
            CREATE INDEX idx_events_source ON events(source_class, observed_on);
            """
        )
        fingerprint = ledger_fingerprint(rows)
        db.executemany("INSERT INTO metadata(key,value) VALUES (?,?)", [
            ("ledger_sha256", fingerprint),
            ("observations", str(len(rows))),
            ("schema", "proofmw-sqlite-index-v1.1"),
        ])
        placeholders = ",".join("?" for _ in _COLUMNS)
        for row in rows:
            payload = asdict(row)
            payload["event_id"] = row.event_id
            db.execute(f"INSERT INTO events({','.join(_COLUMNS)}) VALUES ({placeholders})", [payload.get(name) for name in _COLUMNS])
        db.commit()
    finally:
        db.close()

    return {"status": "BUILT", "path": str(path), "observations": len(rows), "ledger_sha256": ledger_fingerprint(rows), "schema": "proofmw-sqlite-index-v1.1"}


def index_metadata(database: str | Path) -> dict[str, str]:
    db = sqlite3.connect(database)
    try:
        return dict(db.execute("SELECT key,value FROM metadata ORDER BY key").fetchall())
    finally:
        db.close()


def query_sqlite(database: str | Path, *, project_id: str | None = None, operator: str | None = None, country: str | None = None, milestone_type: str | None = None, status: str | None = None, as_of: str | None = None, limit: int = 100) -> dict[str, Any]:
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    if as_of is not None:
        date.fromisoformat(as_of)
    clauses: list[str] = []
    values: list[Any] = []
    for column, value in (("project_id", project_id), ("operator", operator), ("country", country), ("milestone_type", milestone_type), ("status", status)):
        if value is not None:
            clauses.append(f"{column} = ?")
            values.append(value)
    if as_of is not None:
        clauses.append("observed_on <= ?")
        values.append(as_of)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    db = sqlite3.connect(database)
    db.row_factory = sqlite3.Row
    try:
        total = db.execute(f"SELECT COUNT(*) AS n FROM events{where}", values).fetchone()["n"]
        result = db.execute(f"SELECT * FROM events{where} ORDER BY observed_on DESC, event_id LIMIT ?", [*values, limit]).fetchall()
        metadata = dict(db.execute("SELECT key,value FROM metadata").fetchall())
    finally:
        db.close()

    return {"metadata": metadata, "filters": {"project_id": project_id, "operator": operator, "country": country, "milestone_type": milestone_type, "status": status, "as_of": as_of}, "total_matches": total, "returned": len(result), "events": [dict(row) for row in result]}
