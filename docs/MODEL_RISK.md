# Model risk policy — V0.4

ProofMW must not turn a model-development diagnostic into a financing-grade probability merely because the UI can display it.

## Publication gate

A confidence level is `PUBLISHABLE` only when all configured conditions pass:

1. the public/private calibration corpus passes the hard `READY_FOR_CALIBRATION` volume, diversity and control-balance gates;
2. at least 50 out-of-time examples are scored for the evaluated quantile;
3. the claimed confidence level lies inside the empirical coverage bounds after accounting for interval-censored completion dates;
4. the empirical coverage bound width is no more than 15 percentage points.

Failure of any rule produces `DIAGNOSTIC_ONLY` for that quantile. No blended score can override a failed publication gate.

These thresholds are methodology defaults, not proof that 50 samples are universally sufficient. Independent validation, portfolio-specific calibration, legal review and lender/insurer governance remain required before production use.

## Current consequence

The V0.4 public corpus remains `NOT_PUBLISHABLE`. In particular the tail confidence levels do not currently earn financing-grade use. The correct product behavior is to surface that limitation, not hide it.

## Separation of concerns

- LLM/document extraction may propose evidence candidates.
- Evidence graph records what was publicly or privately knowable and when.
- Statistical modules estimate/calibrate distributions.
- Model-risk policy decides whether those estimates may be presented as validated probabilities.
- Human/legal/credit governance remains outside the software's current authority.
