from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backtest import walk_forward_delay_backtest
from .base_rates import delay_base_rate, hierarchical_delay_base_rate
from .data_quality import data_quality_report
from .engine import underwrite
from .event_ledger import detect_source_conflicts, ledger_summary, load_event_ledger
from .evidence import evidence_coverage
from .guardrails import underwriting_grade
from .io import load_project, request_from_dict
from .permitting import permitting_summary
from .training import build_hazard_rows, build_training_rows


def _dump(payload: object, output: str | None = None) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


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
    ledger = sub.add_parser("ledger-summary")
    ledger.add_argument("ledger")
    conflicts = sub.add_parser("ledger-conflicts")
    conflicts.add_argument("ledger")

    rates = sub.add_parser("base-rate")
    rates.add_argument("ledger")
    rates.add_argument("--country")
    rates.add_argument("--milestone-type", default="operations")
    rates.add_argument("--min-samples", type=int, default=2)
    rates.add_argument("--hierarchical", action="store_true")

    permits = sub.add_parser("permitting-summary")
    permits.add_argument("ledger")
    quality = sub.add_parser("data-quality")
    quality.add_argument("ledger")

    backtest = sub.add_parser("backtest")
    backtest.add_argument("ledger")
    backtest.add_argument("--milestone-type", default="operations")
    backtest.add_argument("--min-history", type=int, default=2)

    training = sub.add_parser("export-training")
    training.add_argument("ledger")
    training.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.command in {"ledger-summary", "ledger-conflicts", "base-rate", "permitting-summary", "data-quality", "backtest", "export-training"}:
        events = load_event_ledger(args.ledger)
        if args.command == "ledger-summary":
            _dump(ledger_summary(events))
        elif args.command == "ledger-conflicts":
            _dump(detect_source_conflicts(events))
        elif args.command == "base-rate":
            if args.hierarchical:
                payload = hierarchical_delay_base_rate(events, args.country, args.milestone_type, args.min_samples)
            else:
                payload = delay_base_rate(events, country=args.country, milestone_type=args.milestone_type, min_samples=args.min_samples)
            _dump(payload)
        elif args.command == "permitting-summary":
            _dump(permitting_summary(events))
        elif args.command == "data-quality":
            _dump(data_quality_report(events))
        elif args.command == "backtest":
            _dump(walk_forward_delay_backtest(events, milestone_type=args.milestone_type, min_history=args.min_history))
        else:
            _dump({"forecast_rows": build_training_rows(events), "hazard_rows": build_hazard_rows(events)}, args.output)
        return

    project = load_project(args.project)
    if args.command == "evidence":
        _dump(evidence_coverage(project))
        return
    if args.command == "grade":
        _dump(underwriting_grade(project))
        return
    req = request_from_dict({"as_of_dates": args.dates, "simulations": args.simulations, "seed": args.seed})
    _dump(underwrite(project, req), args.output)


if __name__ == "__main__":
    main()
