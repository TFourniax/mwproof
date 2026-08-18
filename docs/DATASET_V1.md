# Europe Public Infrastructure Event Ledger v1

This dataset is the first seed of ProofMW's planned-vs-actual moat. It is an **event ledger**, not a static project directory: every event records what was publicly knowable at a point in time.

## Current scope

As of 18 August 2026 the v1 seed contains 37 timestamped observations, 14 projects, 7 European countries, 16 tracked milestones, 3 resolved operations forecast→actual pairs, 5 chronological target revisions, 1 preserved same-day source conflict and 3 terminal negative development events.

Countries represented: Portugal, Finland, Denmark, Spain, Germany, Ireland and the United Kingdom.

## Storage model

The file is normalized into a project registry, a source registry and compact events. The loader expands these into immutable `MilestoneObservation` objects and also remains backward compatible with the original list format.

## Why event sourcing matters

A current project page destroys history. ProofMW needs the opposite: the 2024 promise, the 2025 revision and the 2026 outcome must coexist. That lets us reconstruct exactly what a lender could have known at any historical cutoff. `snapshot_as_of()` is the anti-look-ahead guardrail.

## Source policy

Every source uses HTTPS and a source class. Source weights are used only for evidence ranking and conflict surfacing; they are **not probabilities of truth**. Conflicting claims are retained rather than silently overwritten.

## Notable seed histories

Start Campus SIN01 supplies a forecast→actual pair; SIN02 preserves successive 2026→2027 timing revisions and capacity changes. atNorth FIN02 and DEN01 provide additional resolved delivery histories. FIN04 deliberately preserves a material contemporaneous disagreement between public sources. NxN Valencia, Virtus Wustermark and German/Irish planning cases add delay, permitting, denial, cancellation and appeal states.

## Selection bias

The v1 ledger is research seed data assembled from discoverable public histories, not a random sample. Delay statistics are descriptive only. Production calibration requires a much larger systematically collected universe, including successful on-time projects and eventually private planned-vs-actual data.
