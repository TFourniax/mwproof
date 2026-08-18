# ProofMW

**From promised megawatts to bankable compute.**

ProofMW is an evidence-backed probabilistic underwriting and verification layer for AI infrastructure. It turns project evidence into a dependency graph, preserves what was knowable at each point in time, and computes how much power is likely to be physically usable by a given date at explicit confidence levels (`MW@90`, `MW@95`, `MW@99`).

## What exists today

The experimental V0.2 branch contains two connected systems:

1. **Underwriting engine** — AIRS project/evidence model, dependency-aware Monte Carlo simulation, correlated schedule shocks, `MW@Confidence`, `COD@Confidence`, scenarios, critical-path frequencies, evidence coverage and tamper-evident evidence roots.
2. **European evidence graph** — an append-only public event ledger designed to reconstruct forecast → revision → outcome histories without look-ahead leakage.

The public seed currently contains **37 timestamped observations across 14 projects and 7 European countries**, including operations histories, permitting outcomes, cancellations/denials and preserved source conflicts. It is deliberately small and selection-biased: infrastructure for future calibration, not a production rating dataset.

## Research guardrails

- A language model may extract candidate facts; it never invents numerical underwriting probabilities.
- Public claims, private evidence and synthetic assumptions remain distinguishable.
- Same-day conflicting claims are preserved rather than overwritten.
- Historical backtests use only information knowable at the decision cutoff.
- Source weights rank evidence for review; they are **not** probabilities of truth.
- Small public-sample base rates are labelled `descriptive_only`.

## Run

```bash
python -m pip install -e .
proofmw underwrite fixtures/start-campus-sin02-public/project.json --dates 2028-03-31 2028-06-30 2028-12-31
proofmw grade fixtures/start-campus-sin02-public/project.json
```

The bundled SIN02 fixture is **not a credit opinion on Start Campus**. It mixes real public claims with explicitly labelled synthetic uncertainty assumptions because no lender data room is public.

## Explore the evidence graph

```bash
proofmw ledger-summary data/europe-public-events-v1.json
proofmw ledger-conflicts data/europe-public-events-v1.json
proofmw data-quality data/europe-public-events-v1.json
proofmw base-rate data/europe-public-events-v1.json --milestone-type operations
proofmw permitting-summary data/europe-public-events-v1.json
proofmw backtest data/europe-public-events-v1.json --milestone-type operations
proofmw export-training data/europe-public-events-v1.json --output /tmp/proofmw-training.json
```

## Repository map

`engine.py` is the deterministic Monte Carlo core. `event_ledger.py` handles append-only observations, snapshots, revisions and conflicts. `base_rates.py`, `backtest.py`, `training.py`, `permitting.py` and `data_quality.py` form the empirical research layer. `schemas/` contains AIRS and event-ledger contracts; `docs/` defines methodology, falsification, governance, market and moat.

## The bar for production

ProofMW has not yet earned the right to issue a production probability or rating. Before that happens it must accumulate a materially larger, systematically sampled planned-vs-actual corpus; beat simple baselines in leakage-free historical backtests; and demonstrate that the output changes a real lender/insurer decision, pricing, covenant or diligence workflow.
