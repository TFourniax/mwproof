from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofmw.engine import underwrite
from proofmw.evidence import evidence_coverage
from proofmw.io import load_project, request_from_dict

PROJECT = ROOT / "fixtures" / "start-campus-sin02-public" / "project.json"


def test_reproducible_and_confidence_monotone():
    project = load_project(PROJECT)
    req = request_from_dict({"as_of_dates": ["2028-06-30"], "simulations": 4000, "seed": 7})
    a = underwrite(project, req)
    b = underwrite(project, req)
    assert a == b
    q = a["results"]["2028-06-30"]["capacity"]
    assert q["MW@99"] <= q["MW@95"] <= q["MW@90"] <= q["MW@50"]
    assert 0 <= q["MW@99"] <= project.nameplate_mw


def test_later_date_is_not_worse_for_any_power_probability():
    project = load_project(PROJECT)
    req = request_from_dict({"as_of_dates": ["2027-06-30", "2028-06-30"], "simulations": 3000, "seed": 11})
    r = underwrite(project, req)["results"]
    assert r["2028-06-30"]["probability_any_power"] >= r["2027-06-30"]["probability_any_power"]


def test_adverse_grid_scenario_reduces_capacity():
    project = load_project(PROJECT)
    base = request_from_dict({"as_of_dates": ["2028-06-30"], "simulations": 5000, "seed": 13})
    bad = request_from_dict({"as_of_dates": ["2028-06-30"], "simulations": 5000, "seed": 13, "overrides": [{"gate_id": "grid", "delay_shift_days": 180, "max_mw_multiplier": 0.75}]})
    rb = underwrite(project, base)["results"]["2028-06-30"]
    rs = underwrite(project, bad)["results"]["2028-06-30"]
    assert rs["capacity"]["MW@90"] <= rb["capacity"]["MW@90"]
    assert rs["expected_mw"] < rb["expected_mw"]


def test_evidence_layer_exposes_synthetic_assumptions():
    project = load_project(PROJECT)
    cov = evidence_coverage(project)
    assert cov["covered_gate_ratio"] == 1.0
    assert cov["public_evidence_gate_ratio"] == 1.0
    assert cov["synthetic_assumption_gate_ratio"] == 1.0


def test_delivery_confidence_dates_are_monotone():
    project = load_project(PROJECT)
    req = request_from_dict({"as_of_dates": ["2028-12-31"], "simulations": 3000, "seed": 21})
    d = underwrite(project, req)["delivery_date"]
    assert d["COD@50"] <= d["COD@90"] <= d["COD@95"] <= d["COD@99"]
