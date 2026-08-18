from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import underwrite
from .evidence import evidence_coverage
from .guardrails import underwriting_grade
from .io import load_project, request_from_dict


def main() -> None:
    parser = argparse.ArgumentParser(prog="proofmw")
    sub = parser.add_subparsers(dest="command", required=True)
    uw = sub.add_parser("underwrite")
    uw.add_argument("project")
    uw.add_argument("--dates", nargs="+", required=True)
    uw.add_argument("--simulations", type=int, default=20000)
    uw.add_argument("--seed", type=int, default=42)
    uw.add_argument("--output")
    ev = sub.add_parser("evidence")
    ev.add_argument("project")
    grade = sub.add_parser("grade")
    grade.add_argument("project")
    args = parser.parse_args()
    project = load_project(args.project)
    if args.command == "evidence":
        print(json.dumps(evidence_coverage(project), indent=2))
        return
    if args.command == "grade":
        print(json.dumps(underwriting_grade(project), indent=2))
        return
    req = request_from_dict({"as_of_dates": args.dates, "simulations": args.simulations, "seed": args.seed})
    result = underwrite(project, req)
    payload = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
