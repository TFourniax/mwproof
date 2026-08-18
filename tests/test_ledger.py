from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.io import load_project
from proofmw.ledger import project_evidence_root


def test_evidence_root_is_deterministic():
    p = load_project(ROOT / "fixtures" / "start-campus-sin02-public" / "project.json")
    assert project_evidence_root(p) == project_evidence_root(p)
    assert len(project_evidence_root(p)) == 64
