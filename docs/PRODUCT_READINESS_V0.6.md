# ProofMW V0.6 — Product Readiness

Status date: **2026-08-19**

V0.6 separates three questions that must never be conflated:

1. **Does the software run as a product?**
2. **Is the evidence corpus decision-useful?**
3. **Is an empirical probability model validated enough to publish?**

A green answer to (1) does not imply a green answer to (3).

## Green — implemented and CI-testable

| Capability | V0.6 gate |
|---|---|
| Immutable observation identity | legacy IDs remain stable when new fields are absent |
| Ledger fingerprint | deterministic SHA-256 over event IDs |
| Historical `as_of` snapshots | no observation after cutoff |
| Evidence-time anti-lookahead | outcome enters training only after public disclosure |
| Coarse dates | interval preserved; no fake exact day |
| Explicit actual bounds | bounded physical outcomes supported |
| Confirmed state without COD | visible but excluded from temporal scoring |
| Control classification | whole interval must be on one side of +90d threshold |
| Provenance | developer/customer/regulator/grid/OEM classes explicit |
| Revision/conflict preservation | later claims do not overwrite prior claims |
| Evidence Graph / dossier | chronology + source provenance + temporal scorability |
| Physical delivery mapping | power, permitting, transformer, construction, cooling, network |
| Training/hazard export | leakage-safe and interval-aware |
| Walk-forward baselines | developer target + historical median |
| Conditional challenger | contextual benchmark; not auto-promoted |
| Interval calibration | lower/upper empirical coverage bounds |
| Model-risk policy | unsupported confidence levels blocked |
| Coverage Snapshot | dated, hashed, explicit gaps and overdue queue |
| Research prioritization | acquisition work directed to highest-value missing labels |
| SQLite query index | reproducible from canonical JSON |
| Decision Card | diligence support without fake approve/decline |
| API | FastAPI with health/readiness/search/dossiers/data endpoints |
| API deployment boundary | optional API key + confined fixture access |
| Analyst cockpit | V0.6 live dataset/model/diligence views |
| Docker | runnable image + unauthenticated liveness healthcheck |
| End-to-end CI | tests + artifacts + HTTP + authenticated Docker smoke |
| Source watch | change detection only; no unsafe auto-promotion |

## Amber — valuable, still accumulating evidence

### Public corpus breadth

The corpus is now broad enough to support real longitudinal analysis and automated gap finding, but it remains a **dated public-evidence corpus**, not universal market truth.

### Resolved schedule labels

The highest-value data work is converting historical forecasts into defensible outcomes. V0.6 distinguishes:

- fully scorable outcomes;
- interval-censored outcomes;
- operational/current-state confirmations whose exact physical date is unavailable.

Only the first two can support temporal error/calibration metrics.

### Physical causal features

Sines is the reference full physical chain. London 4, BER02, Wustermark, Madrid and other projects now add partial cross-layer histories. More projects need similarly deep timelines before physical milestones can be trusted as generalizable predictors.

### Conditional model

The challenger remains research-only. A one-off MAE improvement over a trivial baseline is insufficient. Promotion requires stable out-of-time lift, calibration and segment robustness.

## Red — cannot be honestly solved with repository code alone

### Private ground truth

Public announcements are selection-biased. We need lender data rooms, EPC baselines/revisions, OEM purchase orders, grid schedules and commissioning records to quantify the bias between public evidence and project truth.

### Production calibration

Published high-confidence percentiles require substantially more future resolved observations across multiple cutoffs, including delays and terminal-negative cases.

### Decision validation

We need real analysts to show that ProofMW changes a workflow: faster diligence, earlier detection, better questions, fewer missed schedule risks, or measurably better calibration.

### Enterprise identity / tenancy

API-key protection is suitable for a controlled pilot, not multi-tenant enterprise SaaS. OIDC/SSO, tenant isolation, RBAC, audit trails, rate limits and secret management are later production requirements.

### Legal/commercial perimeter

Before paid deployment as a credit/insurance/regulated decision input, counsel should review source rights, permitted claims, disclaimers, liability and regulatory classification.

## Definition of “near-finished product” for the current stage

ProofMW is software-near-finished when:

- a clean checkout installs and runs;
- a container starts and is health-checkable;
- evidence can be queried and inspected down to source level;
- all dataset/model states are reproducible from a ledger hash;
- historical leakage and false precision have regression tests;
- current-state evidence is not confused with dated outcomes;
- model outputs are blocked when unsupported;
- project dossiers and Decision Cards expose what is known and missing;
- the UI reflects the same risk boundary as the backend;
- deployment does not expose arbitrary filesystem reads;
- CI tests the product as a running service, not merely as a Python package.

V0.6 targets that definition. The next increase in enterprise value should come primarily from **ground truth, resolved labels, physical depth and customer validation**, not cosmetic feature count.
