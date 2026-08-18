# Model Card — ProofMW Schedule Challenger V0.6

## Intended use

The V0.6 conditional schedule model is an **interpretable challenger benchmark** for research. It tests whether simple project context improves schedule-delay prediction beyond:

1. trusting the developer target (`0` days slippage);
2. applying the global historical median delay.

It is not a production credit score and is not automatically connected to an approve/decline decision.

## Historical information set

For every historical forecast, the model may only use outcomes whose **evidence publication/observation date** is on or before that forecast date.

A physical milestone can predate its disclosure. That physical date does not become historical knowledge until the evidence is public.

## Outcome contract

V0.6 separates:

- exact physical actuals;
- coarse calendar intervals;
- explicit bounded actual intervals;
- confirmed actual states with no defensible physical date.

Only outcomes with a finite physical interval enter temporal slippage/calibration metrics. Confirmed-but-undated actual states remain evidence but are not scored.

## Control labels

The `<=90d` / `>90d` controls are interval-conservative:

- `<=90d` only when `slippage_high_days <= 90`;
- `>90d` only when `slippage_low_days > 90`;
- otherwise the resolved outcome is `interval_ambiguous`.

This prevents the midpoint of a wide public date interval from creating a false binary label.

## Candidate conditioning variables

The current dependency-free challenger can condition on:

- country;
- operator;
- forecast source class;
- lead-time bucket;
- announced capacity bucket when available.

The estimator uses global-median shrinkage plus segment medians only when a segment has enough prior resolved examples.

## Evaluation

Walk-forward evaluation records MAE and bias for:

- developer target;
- global historical median;
- conditional empirical challenger.

The CI artifact `conditional-benchmark.json` is the build-specific source of truth for current metrics. Metrics are deliberately not hard-coded into this document.

## Publication policy

The challenger must not influence published confidence merely because one backtest looks favorable.

Promotion requires:

- sufficient scorable resolved examples;
- sufficient certain early/on-time and delayed controls;
- country/operator/source diversity;
- stable lift across multiple future cutoffs;
- acceptable interval calibration;
- model-risk gates;
- preferably private-ground-truth validation.

Until then, ProofMW remains `EVIDENCE_ONLY` and confidence levels remain `DIAGNOSTIC_ONLY`.

## Known limitations

- public disclosures are selection-biased;
- project phases and definitions of RFS/COD can differ;
- source reporting behavior can masquerade as an operator effect;
- coarse and censored outcomes reduce effective label count;
- terminal failures remain rare;
- physical causal features are much deeper for some projects than others;
- current evidence cannot yet prove stable production superiority over simple baselines.

## Prohibited interpretations

Do not interpret the challenger as:

- probability of default;
- engineering certification;
- guaranteed completion date;
- insurer/reinsurer pricing opinion;
- regulated credit rating;
- replacement for project-specific due diligence.
