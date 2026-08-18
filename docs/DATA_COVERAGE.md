# Data Coverage Policy

## Coverage, not fictional completeness

A public-source infrastructure dataset cannot truthfully promise universal completeness. Relevant facts can live in private contracts, lender data rooms, utility correspondence, planning portals, supplier schedules or unpublished operational records.

ProofMW therefore uses a **dated coverage contract**:

> “This is the set of evidence ProofMW could substantiate as publicly knowable by date X.”

The `dataset-snapshot` command makes that statement reproducible with a ledger SHA-256.

## Acquisition priority

New evidence is ranked by expected underwriting information value:

1. resolved `forecast → actual` operations;
2. material delays and terminal negative outcomes;
3. physical critical-path milestones;
4. forecast revisions and conflicts;
5. independent authoritative corroboration;
6. current portfolio breadth.

A new row that only repeats an already-known current state is lower value than a historical forecast or dated physical milestone.

## Evidence-time rule

`observed_on` means **when the evidence was publicly knowable**, not when the underlying physical event happened.

Example:

- transformer installed: 2025-11-10;
- operator discloses it: 2026-01-15.

The event may store `actual_date=2025-11-10`, but it becomes available to historical training only from `observed_on=2026-01-15`.

## Precision rule

When the source says “Q2 2026”, ProofMW stores an interval. It does not invent June 30 as a precise completion date.

Supported coarse evidence includes month, quarter, half-year and year.

## Contradiction rule

A later source does not erase an earlier statement. A project can legitimately have:

- original forecast;
- revised forecast;
- later first-party statement that conflicts with the revision;
- retrospective actual.

That disagreement is a feature of the underwriting record.

## Unit rule

MVA is not automatically MW. Grid connection ratings reported in MVA remain in notes unless a source explicitly reports MW or a defensible conversion basis exists.

## Generated coverage artifacts

CI emits:

- `dataset-snapshot.json`
- `conditional-benchmark.json`
- `model-risk.json`
- `research-priorities.json`
- `training.json`
- `proofmw.sqlite`
- project decision-card samples

These are generated artifacts, not canonical evidence.
