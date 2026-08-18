# Product thesis

ProofMW is designed to become the independent verification layer between AI-infrastructure developers and capital providers.

## Core primitive

For date `t` and confidence `q`:

`MW@q(t) = max m such that P(usable MW at t >= m) >= q`.

This is intentionally different from a generic score. A lender can reason about a quantity, date and probability and trace the result to evidence and assumptions.

## V1 workflow

1. Normalize a project into AIRS.
2. Attach evidence to each material capacity gate.
3. Mark missing evidence as an explicit assumption, never as fact.
4. Build dependencies among power, permits, construction, cooling and network readiness.
5. Apply idiosyncratic and shared/correlated schedule risks.
6. Run Monte Carlo simulations.
7. Output MW@Confidence, COD@Confidence and critical-path frequencies.
8. Shock individual gates through scenarios.
9. Preserve a deterministic evidence fingerprint for auditability.

## Next product layer

The next engineering milestone is document ingestion: PDFs/contracts -> clause extraction -> evidence candidates -> human/automated verification -> AIRS. The LLM is a perception layer only. Numerical underwriting remains in auditable code.
