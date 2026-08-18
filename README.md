# ProofMW

**From promised megawatts to bankable compute.**

ProofMW is an evidence-backed probabilistic underwriting and verification layer for AI infrastructure. It turns project evidence into a dependency graph, preserves what was knowable at each point in time, and computes how much power is likely to be physically usable by a given date at explicit confidence levels (`MW@90`, `MW@95`, `MW@99`).

## V0.2 — underwriting engine + longitudinal evidence graph

The experimental branch now contains two connected systems:

1. **Underwriting engine** — AIRS project/evidence model, dependency-aware Monte Carlo simulation, correlated schedule shocks, `MW@Confidence`, `COD@Confidence`, scenarios, critical-path frequencies, evidence coverage and tamper-evident evidence roots.
2. **European evidence graph** — an append-only, source-versioned event ledger that reconstructs forecast → revision → outcome histories without look-ahead leakage.

The public seed currently contains **73 timestamped observations across 24 projects, 13 operators and 9 European countries**, backed by **41 unique sources**. It contains 12 resolved operations forecast→actual pairs, 14 non-zero schedule revisions, 3 capacity revisions, permitting/appeal/cancellation histories and preserved source conflicts.

This is intentionally **not** a production rating dataset. `proofmw calibration-readiness` currently returns `NOT_READY` because the corpus is still too small, too concentrated and too dependent on secondary reporting. That failure is a feature: ProofMW has to earn the right to issue probabilities.

## Research guardrails

- A language model may extract candidate facts; it never invents numerical underwriting probabilities.
- Public claims, private evidence and synthetic assumptions remain distinguishable.
- Historical promises are never overwritten by newer guidance.
- Same-day conflicting claims are preserved rather than silently resolved.
- Coarse public dates (month/quarter/half/year) are modeled as **intervals**, not fake exact days.
- Historical backtests use only information knowable at the decision cutoff; outcomes become training data only after they were observable.
- Source weights rank evidence for review; they are **not** probabilities of truth.
- Small public-sample base rates are labelled `descriptive_only`.
- Calibration readiness uses hard gates, including operator concentration and first-party provenance; there is no opaque blended “trust score”.

## Run the underwriting demo

```bash
python -m pip install -e .
proofmw underwrite fixtures/start-campus-sin02-public/project.json \
  --dates 2028-03-31 2028-06-30 2028-12-31
proofmw grade fixtures/start-campus-sin02-public/project.json
```

The bundled SIN02 fixture is **not a credit opinion on Start Campus**. It mixes real public claims with explicitly labelled synthetic uncertainty assumptions because no lender data room is public.

## Explore the European evidence graph

```bash
proofmw ledger-summary data/europe-public-events-v2
proofmw ledger-conflicts data/europe-public-events-v2
proofmw data-quality data/europe-public-events-v2
proofmw calibration-readiness data/europe-public-events-v2
proofmw base-rate data/europe-public-events-v2 --milestone-type operations
proofmw permitting-summary data/europe-public-events-v2
proofmw backtest data/europe-public-events-v2 --milestone-type operations
proofmw export-training data/europe-public-events-v2 --output /tmp/proofmw-training.json
```

## Repository map

- `src/proofmw/engine.py` — deterministic Monte Carlo underwriting core.
- `src/proofmw/event_ledger.py` — event sourcing, precision-aware date windows, snapshots, revisions, conflicts and ledger fingerprint.
- `src/proofmw/base_rates.py` — empirical schedule-delay seeds and hierarchical fallback.
- `src/proofmw/backtest.py` — leakage-free walk-forward baseline testing.
- `src/proofmw/training.py` — as-of-safe delivery and hazard-model training exports.
- `src/proofmw/permitting.py` — descriptive permitting resolution timelines.
- `src/proofmw/data_quality.py` — provenance, source/operator concentration and coverage audit.
- `src/proofmw/readiness.py` — hard minimum gates before any calibrated-public-model claim.
- `schemas/` — AIRS and public event-ledger contracts.
- `docs/DATASET_V1.md` — dataset scope, methodology and limitations.
- `docs/BACKTESTING.md` — falsification and calibration discipline.
- `docs/DATA_GOVERNANCE.md` — provenance and defensibility rules.
- `docs/EMPIRICAL_FINDINGS_V0.2.md` — current descriptive findings and why they are not yet underwriting probabilities.

## The bar for production

ProofMW has not yet earned the right to issue a production probability or rating. Before that happens it must accumulate a materially larger and deliberately balanced planned-vs-actual corpus, diversify operator/source exposure, beat simple baselines in leakage-free historical tests, demonstrate calibration/interval coverage, and show that its output changes a real lender or insurer decision, pricing, covenant or diligence workflow.

See `docs/PRODUCT.md`, `docs/METHODOLOGY.md`, `docs/MARKET_VALIDATION.md`, `docs/MOAT.md`, `docs/FAILURE_TESTS.md` and the V0.2 data/backtesting documents for the current thesis and kill criteria.
