# Model Card — Conditional Schedule Challenger V0.5

## Purpose

Test whether simple, interpretable context can improve schedule-delay prediction beyond:

1. trusting the developer target (`0` days slippage);
2. applying the global historical median delay.

This model is a **challenger benchmark**, not a production underwriting model.

## Information set

For every historical forecast, only outcomes whose **public evidence date** is on or before that forecast date can enter the training history.

Candidate conditioning variables:

- country;
- operator;
- forecast source class;
- lead-time bucket;
- announced capacity bucket when recoverable from the forecast observation.

## Estimator

The estimator starts with a global historical median as a shrinkage anchor. Segment medians can pull the estimate only when a segment has a minimum number of prior resolved observations. Small segments are therefore not allowed to dominate.

No third-party ML library is required.

## Evaluation

Walk-forward evaluation records MAE and bias for:

- developer target;
- global median;
- conditional empirical challenger.

The report explicitly states whether the challenger beats each baseline on MAE.

## Promotion criteria

The challenger must **not** be injected into live underwriting merely because it beats a baseline once.

Promotion requires:

- sufficient resolved examples;
- balanced early/on-time and delayed controls;
- operator/country diversity;
- stable out-of-time lift across cutoffs;
- interval calibration;
- model-risk publication gates;
- preferably private-ground-truth validation.

## Known limitations

- public disclosures are selection-biased;
- project phases and “RFS” definitions can differ;
- operator identity can proxy for geography, project scale or reporting style;
- coarse dates create interval-censored labels;
- terminal failures remain rare;
- current sample size is below the production target.

## Output policy

Until the independent model-risk layer says otherwise, quantitative confidence labels remain `DIAGNOSTIC_ONLY` and the product remains in `EVIDENCE_ONLY` mode.
