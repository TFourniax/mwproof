from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any, Iterable
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .event_ledger import MilestoneObservation

_AUTHORITATIVE = {"government", "regulator", "grid-operator", "company-filing", "developer-oem-announcement", "developer-release", "developer", "oem"}


def build_watchlist(items: Iterable[MilestoneObservation], *, authoritative_only: bool = True) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in items:
        if authoritative_only and row.source_class not in _AUTHORITATIVE:
            continue
        entry = grouped.setdefault(row.source_url, {"url": row.source_url, "source_class": row.source_class, "source_title": row.source_title, "projects": set(), "last_observed_on": row.observed_on})
        entry["projects"].add(row.project_id)
        entry["last_observed_on"] = max(entry["last_observed_on"], row.observed_on)
    return [{**{k: v for k, v in entry.items() if k != "projects"}, "projects": sorted(entry["projects"])} for _, entry in sorted(grouped.items())]


def fetch_snapshot(url: str, *, timeout: float = 12.0, max_bytes: int = 2_000_000) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "ProofMW-EvidenceWatch/0.3 (+https://github.com/TFourniax/mwproof)", "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"})
    fetched_at = datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read(max_bytes + 1)
            truncated = len(payload) > max_bytes
            payload = payload[:max_bytes]
            return {"url": url, "ok": True, "status": getattr(response, "status", 200), "final_url": response.geturl(), "content_type": response.headers.get("Content-Type"), "etag": response.headers.get("ETag"), "last_modified": response.headers.get("Last-Modified"), "bytes_hashed": len(payload), "truncated": truncated, "sha256": hashlib.sha256(payload).hexdigest(), "fetched_at": fetched_at}
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {"url": url, "ok": False, "error": f"{type(exc).__name__}: {exc}", "fetched_at": fetched_at}


def snapshot_watchlist(watchlist: list[dict[str, Any]], *, limit: int | None = None, timeout: float = 12.0) -> dict[str, Any]:
    selected = watchlist[:limit] if limit is not None else watchlist
    snapshots = [fetch_snapshot(entry["url"], timeout=timeout) for entry in selected]
    success = sum(1 for row in snapshots if row["ok"])
    return {"watchlist_size": len(watchlist), "attempted": len(selected), "successful": success, "failed": len(selected) - success, "success_ratio": round(success / len(selected), 4) if selected else 1.0, "snapshots": snapshots, "note": "Hashes detect public-source changes. Changed pages become review candidates; they are never auto-promoted to underwriting facts."}


def compare_snapshots(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    old = {row["url"]: row for row in before.get("snapshots", []) if row.get("ok")}
    changes = []
    for current in after.get("snapshots", []):
        if not current.get("ok") or current["url"] not in old:
            continue
        previous = old[current["url"]]
        if previous.get("sha256") != current.get("sha256"):
            changes.append({"url": current["url"], "before_sha256": previous.get("sha256"), "after_sha256": current.get("sha256"), "before_fetched_at": previous.get("fetched_at"), "after_fetched_at": current.get("fetched_at")})
    return changes
