# ProofMW V0.5 — Product Readiness

Status date: **2026-08-19**

This document separates “software exists” from “underwriting claim is earned”.

## Green — implemented and testable

| Capability | Gate |
|---|---|
| Immutable event identity + ledger fingerprint | deterministic SHA-256 root |
| Historical `as_of` snapshots | no observation after cutoff |
| Source provenance and concentration | hard data-quality invariants |
| Forecast revision/conflict preservation | contradictory claims remain visible |
| Coarse-date interval handling | no fake exact completion day |
| Evidence Graph / project dossier | lender-facing chronology |
| Physical delivery mapping | power, permitting, transformer, construction, cooling, network |
| Training/hazard exports | actual evidence enters only after disclosure |
| Walk-forward backtest | leakage-safe historical baseline |
| Interval calibration | lower/upper empirical coverage bounds |
| Model-risk policy | unearned q-levels blocked |
| Conditional challenger benchmark | compared OOT with developer target + global median |
| Coverage Snapshot | dated + hashed + explicit gaps |
| SQLite query artifact | reproducible from canonical JSON |
| Decision Card | evidence/gaps/diligence, no fake rating |
| API / analyst cockpit | runnable service |
| Container build | Dockerfile + health check |
| E2E CI | unit, CLI, HTTP and container smoke |
| Evidence watch | recurring primary-source watch workflow |

## Amber — useful, still accumulating evidence

### Dataset breadth
The corpus is materially broader than V0.2, but the hard production gates intentionally remain much higher than today’s public sample.

### Conditional prediction
V0.5 adds an interpretable hierarchical empirical challenger. It is not wired into the underwriting score. Promotion requires repeatable out-of-time lift over both trivial baselines.

### Physical causal features
Sines is the reference deep-underwritten project. More projects need the same cross-layer history before causal/physical predictors can be statistically trusted.

### Source monitoring
The watchlist detects candidate changes. Fully autonomous ingestion should remain evidence-preserving: discovered claims must be normalized, deduplicated, source-dated and schema-validated before entering canonical data.

## Red — cannot be solved honestly with repository code alone

### Private ground truth
Public announcements are selection-biased. Lender data rooms, EPC schedules, OEM purchase orders and grid connection documents are needed to quantify that bias.

### Production calibration
P90/P95 require substantially more out-of-time resolved observations, especially delayed and terminal-negative controls.

### Decision validation
We need evidence that the product changes a real underwriting workflow: faster diligence, better questions, earlier risk detection or better calibrated decisions.

### Legal/commercial perimeter
Before selling the product as a credit, insurance or regulated decision input, counsel should define the allowed claims, disclaimers and data-licensing perimeter.

## Definition of “near-finished”

The software can be considered product-complete before the empirical model is mature if:

- ingestion and evidence provenance are reproducible;
- analysts can query every claim and inspect its source;
- project dossiers and decision cards expose missing diligence;
- model outputs are blocked when unsupported;
- deployment and CI are deterministic;
- dataset snapshots make coverage measurable;
- no human has to reverse-engineer research history from a chat.

V0.5 is designed around that definition.
