# Backtesting discipline

ProofMW must earn the right to output probabilities.

## Rule 1 — no future knowledge

For a historical decision date `T`, only ledger observations with `observed_on <= T` may be used as features, priors or evidence. `snapshot_as_of()` enforces this at the data layer. The walk-forward backtester goes further: a resolved outcome may enter historical training only after its actual date was knowable.

## Rule 2 — separate extraction from calibration

A source may say “ready Q4 2024”. That is an observation. The probability that it will actually be ready is a model output and must come from calibrated history, not from language-model confidence.

## Rule 3 — benchmarks before sophistication

Every future model must beat at least developer target with zero adjustment, global historical median slippage, country/milestone-type hierarchical base rate and a simple statistical survival model. Metrics should include MAE for delivery date, Brier/log loss for binary milestone probability, calibration error and interval coverage for MW@Confidence.

## Current state

The v1 public dataset has only three resolved operations forecast→actual pairs. That is enough to test machinery but **not enough to validate a probability model**. Empirical base rates are therefore `descriptive_only`, and the walk-forward report currently returns `INSUFFICIENT_HISTORY` rather than leaking future outcomes.

The next data milestone is 100+ projects and 500+ milestone observations with a deliberately constructed on-time control sample.
