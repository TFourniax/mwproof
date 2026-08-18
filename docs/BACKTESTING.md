# Backtesting discipline

ProofMW must earn the right to output probabilities.

## Rule 1 — no future knowledge

For a historical decision date `T`, only ledger observations with `observed_on <= T` may be used as features, priors or evidence. `snapshot_as_of()` enforces this at the data layer.

The walk-forward backtester applies a stricter rule: a resolved project outcome may enter the historical baseline only after the actual outcome date was knowable. Later observations are never backfilled into earlier decisions.

## Rule 2 — preserve date uncertainty

A public “Q4 2024” statement is a window, not 31 December 2024. Forecast and actual windows are carried through the event layer so we do not manufacture delays from imprecise disclosure dates.

## Rule 3 — separate extraction from calibration

A source may say “ready Q4 2024”. That is an observation. The probability that it will actually be ready is a model output and must come from calibrated history, not from language-model confidence.

## Rule 4 — benchmarks before sophistication

Every future ProofMW model must beat at least:

1. developer target with zero adjustment;
2. global historical median slippage;
3. country/milestone-type hierarchical base rate;
4. simple statistical survival model.

Metrics should include delivery-date MAE/bias, Brier/log loss for milestone probabilities, calibration error and empirical interval coverage for `MW@Confidence`.

## Current V0.2 smoke test

The public ledger now contains 12 resolved operations forecast→actual histories. A leakage-free walk-forward baseline can be scored, but only four later examples currently have enough prior resolved history for the historical-median comparator.

On this tiny and selection-biased slice:

- developer-target baseline: MAE ≈ 191.5 days across 12 examples;
- historical-median baseline: MAE ≈ 143.9 days across only 4 scorable later examples.

This **does not validate ProofMW** and is not statistically persuasive. It only proves the machinery can perform a temporally honest comparison and already gives us a baseline that future models must beat.

`backtest` returns `SCORABLE_BASELINE`, not a production-readiness claim. Separately, `calibration-readiness` remains `NOT_READY`.

## Hard data gates

The current readiness policy requires, at minimum, 500 observations, 100 projects, 100 resolved operations outcomes, 100 unique sources, at least 25 early/on-time controls and 25 materially delayed controls, sufficient country/operator diversity, >=50% authoritative/first-party evidence and no single operator above 25% of projects.

Even passing these volume/diversity gates will not be enough: predictive accuracy, calibration and out-of-time performance remain mandatory.
