from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from .models import Evidence, Project


def evidence_fingerprint(evidence: Evidence) -> str:
    payload = json.dumps(asdict(evidence), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def project_evidence_root(project: Project) -> str:
    """Deterministic Merkle-like root over sorted evidence fingerprints.

    V0.1 uses a simple SHA-256 fold; this is for tamper-evident provenance,
    not blockchain or timestamping claims.
    """
    hashes = sorted(evidence_fingerprint(e) for e in project.evidence)
    acc = hashlib.sha256(b"proofmw-evidence-v0.1").digest()
    for item in hashes:
        acc = hashlib.sha256(acc + bytes.fromhex(item)).digest()
    return acc.hex()
