# Methodology v0.1

## Model

A project is a directed acyclic graph of capacity gates. A gate has a maximum MW contribution, target date, bounded delay distribution, bounded derating distribution, dependencies, evidence and loadings to common risk factors.

Per simulation, ProofMW samples common risk-factor shocks first, then gate-specific uncertainty. A dependent gate cannot become usable before its dependencies. Project usable MW is the minimum available capacity across required gates and nameplate capacity.

`MW@95` is the fifth percentile of simulated usable capacity: a quantity met or exceeded in approximately 95% of modelled trajectories.

`COD@95` is the 95th percentile of simulated delivery dates: approximately 95% of modelled trajectories deliver by that date.

## Correlation

V0.1 supports shared delay factors. This prevents the common modelling error of treating transformer, electrical construction and cooling schedules as independent when a supply-chain shock can affect all of them.

## Non-goals

V0.1 is not a rating agency methodology, insurance pricing model, legal opinion, power-flow study or engineering certification. Calibration distributions in the public demo are synthetic. Production use requires backtesting and domain-specific calibration.
