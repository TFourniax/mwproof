# ProofMW V0.3 — maturation gates

This phase deliberately separates **data improvement**, **method validation** and **productization**. A feature is not considered delivered because code exists; it must pass an observable gate.

## Gate A — break operator concentration

Target: largest operator <= 25% of projects.

Action: add primary-source histories from NTT Global Data Centers, Vantage, CyrusOne, DATA4, Digital Realty, Colt DCS, Kao Data and Iron Mountain.

Why: a Europe model dominated by one public operator would learn disclosure behavior rather than infrastructure risk.

## Gate B — primary-source majority

Target: authoritative / first-party observations >= 50%.

Preferred evidence: regulators / grid operators / government, company filings, developer and OEM releases, specialist monitoring, then secondary press only where primary history is unavailable.

## Gate C — anti-leakage research infrastructure

Outcomes enter a walk-forward training set only when the evidence reporting the outcome was observable, not merely when the physical event occurred. Coarse actual dates are interval-censored.

V0.3 adds interval-aware quantile diagnostics and bounded calibration coverage.

## Gate D — product workflow

`project-dossier` turns the event graph into an as-of evidence packet: project identity, milestone timeline, latest forecast and actual, target/capacity revisions, conflicts, evidence quality, stale forecasts and missing physical milestone categories.

It is intentionally not a credit opinion.

## Gate E — recurring evidence acquisition

A separate scheduled `evidence-watch` workflow hashes authoritative public sources and produces a review artifact. Page changes are **candidates**, never automatically promoted to facts.

This protects the underwriting core from flaky network crawling while creating the beginning of a continuous evidence pipeline.

## What still blocks production

Even if A and B pass, ProofMW remains `NOT_READY` until the minimum corpus gates and leakage-free predictive/calibration tests are met. Commercial validation remains separate: a lender or insurer must show that the output changes diligence, structure, pricing, covenants or a go/no-go decision.
