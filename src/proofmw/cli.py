from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backtest import walk_forward_delay_backtest
from .base_rates import delay_base_rate, hierarchical_delay_base_rate
from .calibration import walk_forward_interval_calibration
from .data_quality import data_quality_report
from .dossier import project_dossier
from .engine import underwrite
from .event_ledger import detect_source_conflicts, ledger_summary, load_event_ledger
from .evidence import evidence_coverage
from .guardrails import underwriting_grade
from .io import load_project, request_from_dict
from .model_risk import model_risk_report
from .permitting import permitting_summary
from .physical_depth import physical_depth_report
from .readiness import calibration_readiness
from .research_priority import research_priorities
from .source_watch import build_watchlist, snapshot_watchlist
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

    for name in ("permitting-summary", "data-quality", "calibration-readiness", "research-priorities", "physical-depth", "model-risk"):
        p = sub.add_parser(name)
        p.add_argument("ledger")

    backtest = sub.add_parser("backtest")
    backtest.add_argument("ledger")
    backtest.add_argument("--milestone-type", default="operations")
    backtest.add_argument("--min-history", type=int, default=2)

    calibration = sub.add_parser("calibration")
    calibration.add_argument("ledger")
    calibration.add_argument("--milestone-type", default="operations")
    calibration.add_argument("--min-history", type=int, default=5)

    dossier = sub.add_parser("project-dossier")
    dossier.add_argument("ledger")
    dossier.add_argument("project_id")
    dossier.add_argument("--as-of")

    watch = sub.add_parser("source-watch")
    watch.add_argument("ledger")
    watch.add_argument("--all-sources", action="store_true")
    watch.add_argument("--limit", type=int, default=50)
    watch.add_argument("--timeout", type=float, default=12.0)
    watch.add_argument("--output", required=True)

    training = sub.add_parser("export-training")
    training.add_argument("ledger")
    training.add_argument("--output", required=True)

    args = parser.parse_args()
    data_commands = {"ledger-summary", "ledger-conflicts", "base-rate", "permitting-summary", "data-quality", "calibration-readiness", "backtest", "calibration", "research-priorities", "project-dossier", "source-watch", "export-training", "physical-depth", "model-risk"}
    if args.command in data_commands:
        events = load_event_ledger(args.ledger)
        if args.command == "ledger-summary":
            _dump(ledger_summary(events))
        elif args.command == "ledger-conflicts":
            _dump(detect_source_conflicts(events))
        elif args.command == "base-rate":
            payload = hierarchical_delay_base_rate(events, args.country, args.milestone_type, args.min_samples) if args.hierarchical else delay_base_rate(events, country=args.country, milestone_type=args.milestone_type, min_samples=args.min_samples)
            _dump(payload)
        elif args.command == "permitting-summary":
            _dump(permitting_summary(events))
        elif args.command == "data-quality":
            _dump(data_quality_report(events))
        elif args.command == "calibration-readiness":
            _dump(calibration_readiness(events))
        elif args.command == "backtest":
            _dump(walk_forward_delay_backtest(events, milestone_type=args.milestone_type, min_history=args.min_history))
        elif args.command == "calibration":
            _dump(walk_forward_interval_calibration(events, milestone_type=args.milestone_type, min_history=args.min_history))
        elif args.command == "research-priorities":
            _dump(research_priorities(events))
        elif args.command == "physical-depth":
            _dump(physical_depth_report(events))
        elif args.command == "model-risk":
            _dump(model_risk_report(events))
        elif args.command == "project-dossier":
            _dump(project_dossier(events, args.project_id, as_of=args.as_of))
        elif args.command == "source-watch":
            watchlist = build_watchlist(events, authoritative_only=not args.all_sources)
            _dump(snapshot_watchlist(watchlist, limit=args.limit, timeout=args.timeout), args.output)
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
