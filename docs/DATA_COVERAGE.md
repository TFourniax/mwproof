# Data Coverage Policy

## Coverage, not fictional completeness

A public-source infrastructure dataset cannot truthfully promise universal completeness. Relevant facts can live in private contracts, lender data rooms, utility correspondence, planning portals, supplier schedules or unpublished operational records.

ProofMW therefore uses a **dated coverage contract**:

> “This is the set of evidence ProofMW could substantiate as publicly knowable by date X.”

The `dataset-snapshot` command makes that statement reproducible with a ledger SHA-256.

## Acquisition priority

New evidence is ranked by expected underwriting information value:

1. scorable `forecast → actual` operations;
2. material delays and terminal negative outcomes;
3. physical critical-path milestones;
4. forecast revisions and conflicts;
5. independent first-party / customer / authoritative corroboration;
6. confirmed current states whose exact physical dates are still unknown;
7. portfolio breadth.

A row that merely repeats an already-known state is lower value than a dated historical claim or physical milestone. But a customer confirmation can still be valuable if it independently proves that an operator/developer state is real.

## Evidence time vs physical time

`observed_on` means **when the evidence was publicly knowable**, not when the underlying physical event happened.

Example:

- transformer installed: 2025-11-10;
- operator discloses it: 2026-01-15.

The observation may store `actual_date=2025-11-10`, but it becomes available to historical training only from `observed_on=2026-01-15`.

Retrospective timelines are therefore useful evidence but do not get backfilled into old historical feature sets.

## Four temporal evidence states

V0.6 distinguishes four cases:

### 1. Exact actual

The source gives a defensible physical day. `actual_date` + `precision=day` yields a one-day outcome window.

### 2. Coarse actual

The source says month/quarter/half-year/year. ProofMW expands that calendar precision to an interval instead of inventing a day.

### 3. Explicit bounded actual

When source evidence provides defensible lower and upper bounds, `actual_start` and `actual_end` preserve that interval directly. These bounds override generic calendar precision.

### 4. Confirmed actual state, physical date unknown

A source may say “the building is operational today” without disclosing when operation began. ProofMW records `status=actual` but leaves the physical date empty.

That confirmation:

- is visible in the dossier;
- means the milestone is no longer an unresolved existence/state question;
- is **not** used in MAE, slippage or calibration until a defensible physical time window is found.

This prevents “known to be live by X” from being silently rewritten as “COD = X”.

## Control-label rule

For the `<=90 days` vs `>90 days` schedule controls, V0.6 does not classify on midpoint alone.

- certainly early/on-time: the **high** end of slippage is `<=90d`;
- certainly materially delayed: the **low** end is `>90d`;
- otherwise: interval-ambiguous.

Ambiguous outcomes remain useful interval data but do not inflate either control class.

## Contradiction rule

A later source does not erase an earlier statement. A project can legitimately have:

- original forecast;
- revised forecast;
- later first-party statement that conflicts with the revision;
- physical progress evidence;
- customer confirmation;
- retrospective actual.

That disagreement is a feature of the underwriting record.

## Unit rule

MVA is not automatically MW. Grid connection ratings reported in MVA remain in notes unless a source explicitly reports MW or a defensible conversion basis exists.

Likewise, facility-level capacity is not allocated across individual buildings unless the source gives the split.

## Current-state source rule

For undated live webpages, `observed_on` is the date ProofMW actually observed the current claim, not an invented publication date.

For dated releases/filings, `observed_on` uses the public release/filing date when available.

## Generated coverage artifacts

CI emits:

- `dataset-snapshot.json`
- `conditional-benchmark.json`
- `model-risk.json`
- `research-priorities.json`
- `training.json`
- `proofmw.sqlite`
- project dossier / decision-card samples

These are generated artifacts, not canonical evidence.
