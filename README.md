# ProofMW

**Evidence-first underwriting infrastructure for AI/data-center delivery risk.**

ProofMW reconstructs what developers, utilities, regulators, OEMs, customers and other primary sources said **at the time**, preserves revisions and contradictions, maps physical delivery dependencies, and only then evaluates what probabilistic statements the evidence can support.

> **Current product mode: `EVIDENCE_ONLY`.** The software is runnable and decision-useful. Empirical confidence levels remain blocked by explicit model-risk gates until sufficient out-of-time evidence exists. ProofMW does not manufacture a P90/P95 because a UI would look better with one.

## V0.6 — what changed

V0.6 turns the V0.5 research service into a much stricter product boundary:

- **Interval-censored actuals.** `actual_start` / `actual_end` can represent a defensible physical completion interval without inventing an exact COD.
- **Confirmed-but-unscored actual states.** If a first-party/customer source says a site is operational but does not disclose when it became operational, ProofMW records the fact while excluding it from MAE/calibration.
- **Conservative control labels.** A resolved operation is called `<=90d` or `>90d` only when its *whole* slippage interval falls on one side of that threshold. Overlapping cases stay ambiguous.
- **Customer evidence as first-party provenance.** Customer releases can corroborate operator claims without silently replacing them.
- **More longitudinal/physical data.** Follow-ups include Hamar customer confirmations, London 4 physical construction/cooling/power milestones, BER02 schedule revision evidence and Madrid schedule/power/current-state evidence.
- **Hardened HTTP boundary.** Optional `PROOFMW_API_KEY` protects `/ready` and `/v1/*`; `/health` remains available for orchestrators.
- **No arbitrary filesystem reads.** `/v1/underwrite` can only open fixtures shipped below `fixtures/`; absolute paths and traversal are rejected.
- **Deployment-safe health checks.** Container liveness stays independent of API authentication.
- **V0.6 analyst cockpit.** Coverage snapshot, overdue queue, benchmark comparison, model risk, Decision Card, physical depth and project timelines are visible in one UI.
- **CI now exercises auth as a deployed product**, in addition to tests, artifact generation, live HTTP and Docker execution.

## Why the data model matters

A normal market database tends to keep the latest state: `RFS 2028`. ProofMW keeps the **claim history**:

```text
forecast → revised forecast → conflict → physical milestone → confirmed state → scorable actual
```

Every observation has an `observed_on` date. Historical features may only use evidence publicly knowable by their cutoff. A transformer installed in March but disclosed in June becomes training-eligible in June, not March.

ProofMW separates three temporal concepts:

1. **evidence time** — when the claim became knowable;
2. **physical time** — when the underlying milestone happened, if disclosed;
3. **precision/censoring** — exact day, month/quarter/year interval, explicit bounds, or a confirmed state with no defensible physical date.

This distinction is a core anti-lookahead and anti-false-precision guarantee.

## Product architecture

```text
Primary / customer / public evidence
        │
        ▼
Append-only Event Ledger ──► provenance / conflict / revision checks
        │
        ├──► Evidence Graph + project dossier
        ├──► Physical dependency depth
        ├──► Coverage Snapshot + overdue/research queues
        ├──► Leakage-safe training / hazard exports
        ├──► Walk-forward baselines + interval calibration
        ├──► Conditional challenger benchmark
        ├──► Model-risk publication policy
        ├──► Decision Card
        └──► FastAPI / SQLite / analyst cockpit
```

The dependency-aware Monte Carlo engine remains available for structured project fixtures. Empirical public-data probabilities are gated separately and are **not** promoted into production merely because they can be computed.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[api,dev]"
pytest -q
```

Inspect the corpus:

```bash
proofmw dataset-snapshot data/europe-public-events-v2 --as-of 2026-08-19
proofmw data-quality data/europe-public-events-v2
proofmw calibration-readiness data/europe-public-events-v2
proofmw model-risk data/europe-public-events-v2
proofmw conditional-benchmark data/europe-public-events-v2 --min-history 5
proofmw research-priorities data/europe-public-events-v2
```

Open lender-facing evidence:

```bash
proofmw project-dossier data/europe-public-events-v2 start-campus-sines --as-of 2026-08-19
proofmw decision-card data/europe-public-events-v2 start-campus-sines --as-of 2026-08-19
proofmw project-dossier data/europe-public-events-v2 greenmountain-hamar-b1 --as-of 2026-08-19
```

Build a reproducible serving index:

```bash
proofmw index-ledger data/europe-public-events-v2 --output build/proofmw.sqlite
proofmw query-index build/proofmw.sqlite --country Portugal --limit 10
```

## Run the product

Local development:

```bash
uvicorn proofmw.api:app --reload
# open http://127.0.0.1:8000
```

Protected deployment:

```bash
export PROOFMW_API_KEY='replace-with-a-long-random-secret'
uvicorn proofmw.api:app --host 0.0.0.0 --port 8080
```

Docker:

```bash
docker build -t proofmw .
docker run --rm -p 8080:8080 \
  -e PROOFMW_API_KEY='replace-with-a-long-random-secret' \
  proofmw
```

The web cockpit accepts the API key and stores it in **sessionStorage only** for the current browser session.

## HTTP surface

- `GET /health` — unauthenticated process liveness and version.
- `GET /ready` — service mode, dataset/model state and ledger hash.
- `GET /v1/data/snapshot?as_of=YYYY-MM-DD` — dated/hashable coverage contract.
- `GET /v1/data/readiness` — hard corpus gates.
- `GET /v1/data/calibration` — interval-aware walk-forward calibration.
- `GET /v1/data/conditional-benchmark` — challenger vs simple out-of-time baselines.
- `GET /v1/data/model-risk` — publishability policy.
- `GET /v1/data/physical-depth` — cross-layer delivery evidence.
- `GET /v1/data/research-priorities` — highest-value missing evidence.
- `GET /v1/projects` — registry derived from canonical evidence.
- `GET /v1/projects/{id}/dossier` — evidence chronology.
- `GET /v1/projects/{id}/decision-card` — lender diligence card.
- `GET /v1/search?...` — event search/filtering.
- `POST /v1/underwrite` — dependency-aware structured-fixture simulation.

If `PROOFMW_API_KEY` is set, send it as `X-API-Key` to `/ready` and `/v1/*`.

## Dataset: coverage, not fictional completeness

A public-source infrastructure dataset cannot truthfully promise universal completeness. Private EPC baselines, transformer purchase orders, grid agreements, lender reports and incident records are often unavailable.

Every build therefore emits a **Coverage Snapshot** containing:

- exact ledger SHA-256;
- evidence and physical-time span;
- projects/operators/countries/sources;
- provenance and source concentration;
- scorable resolved outcomes;
- certain early/on-time, certain delayed and interval-ambiguous controls;
- confirmed actual states without a defensible physical date;
- unresolved, overdue and stale forecasts;
- physical-depth coverage;
- hard readiness gates.

Exact current counts are intentionally **not hard-coded here**. The CI artifact is the source of truth for a build.

## Model policy

The empirical layer follows a strict promotion sequence:

1. reconstruct the historical information set;
2. preserve interval uncertainty instead of collapsing it;
3. benchmark against simple alternatives;
4. calibrate out of time;
5. require sufficient sample size and diversity;
6. validate against private ground truth where possible;
7. publish a confidence level only when independent model-risk gates pass.

The conditional model is a **challenger benchmark**, not a production predictor. See [`docs/MODEL_CARD_V0.6.md`](docs/MODEL_CARD_V0.6.md).

## Repository layout

```text
data/europe-public-events-v2/   append-only public evidence shards
fixtures/                       structured underwriting examples
schemas/                        event-ledger and AIRS schemas
src/proofmw/                    engine, evidence, calibration, storage, API
tests/                          unit + empirical + security invariants
web/                            analyst cockpit
docs/                           methodology, governance and product notes
.github/workflows/              CI + source-watch automation
```

## Non-negotiable guardrails

- No future evidence in historical features.
- No MVA→MW conversion without an explicit engineering basis.
- No fake exact day when the source only gives coarse timing.
- No fake COD when a source only confirms that something is currently operational.
- No midpoint-forced class when an interval crosses a risk threshold.
- No silent overwrite of contradictory first-party statements.
- No missing evidence interpreted as failure or success.
- No confidence label promoted merely because code can calculate it.
- No arbitrary filesystem path exposed through the public API.
- JSON evidence shards remain canonical; generated databases are rebuildable artifacts.
- ProofMW is not, by itself, a credit opinion, engineering certification, legal opinion or insurance determination.

## What still separates V0.6 from a validated underwriting model

The remaining moat is primarily **ground truth, labels and decision validation**, not another dashboard:

1. resolve more historical forecast→actual operations, especially overdue forecasts;
2. accumulate rare terminal failures and genuinely delayed controls;
3. replicate Sines-style physical mapping across more projects;
4. compare public evidence with private lender/EPC/operator truth;
5. demonstrate stable out-of-time lift and calibration across future cutoffs;
6. run live/dry-run decision pilots with lenders, insurers and infrastructure investors;
7. define the legal/commercial perimeter before regulated or credit-like claims.

See [`docs/PRODUCT_READINESS_V0.6.md`](docs/PRODUCT_READINESS_V0.6.md), [`docs/DATA_COVERAGE.md`](docs/DATA_COVERAGE.md) and [`SECURITY.md`](SECURITY.md).
