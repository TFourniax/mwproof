from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.guardrails import underwriting_grade
from proofmw.io import load_project


def test_public_demo_cannot_masquerade_as_verified_underwriting():
    p = load_project(ROOT / "fixtures" / "start-campus-sin02-public" / "project.json")
    assert underwriting_grade(p)["grade"] == "DEMO_ONLY"
