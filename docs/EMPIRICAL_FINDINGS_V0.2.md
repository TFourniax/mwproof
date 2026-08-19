# Empirical findings — V0.2 public seed

These are **descriptive research findings**, not underwriting probabilities.

## Delivery histories

The current public seed has 12 resolved operations forecast→actual pairs. Using the midpoint of each disclosed forecast window and the midpoint/known point of the actual-operation window, observed slippage ranges from roughly -92 days to +457 days.

Current descriptive statistics:

- mean midpoint slippage: 176.2 days
- median midpoint slippage: 152 days
- p10: 0 days
- p90: 365 days
- on or before forecast midpoint: 25%

These numbers are highly vulnerable to selection bias, operator concentration and differences in disclosure precision. They should **not** be extrapolated as “75% of European data centers are late”.

## A more important finding than the mean

Historical target revisions contain information that current project pages erase. A project can appear on-time relative to its latest published target while being materially late relative to the target available to an earlier lender. That makes versioned guidance itself a potentially valuable predictive feature.

## Precision finding

Treating “Q4 2024” as 31 December produced false delay labels. V0.2 now represents month/quarter/half-year/year disclosures as intervals and carries lower/mid/high slippage bounds. This is essential before any statistical calibration.

## Provenance finding

41 unique sources support the current 73 events, but only about 38% of observations are currently first-party/authoritative under the V0.2 classification. Equinix is also over-represented at roughly 42% of projects. Both weaknesses are encoded as failing readiness gates rather than hidden in a methodology footnote.

## Preliminary baseline finding

A leakage-free walk-forward smoke test can currently score only four examples with a historical-median prior. On those four, the historical-median delay adjustment has lower MAE than blindly trusting the original target. The sample is far too small to infer commercial predictive advantage; its value today is that the test harness exists and future models have a fixed baseline to beat.

## What would change the investment thesis

The thesis strengthens substantially if, after expanding to a broad universe, target revisions, operator/OEM/geography features and project dependency evidence materially improve out-of-time delivery calibration versus simple historical base rates.

The thesis weakens materially if a systematically sampled 100+ project corpus shows that public/private observable evidence cannot predict delivery better than crude base rates, or if lenders do not change decisions when exposed to the improved distributions.
