# Europe Public Infrastructure Event Ledger v1

This dataset is the first seed of ProofMW's planned-vs-actual moat. It is an **event ledger**, not a static project directory: every event records what was publicly knowable at a point in time.

## Current scope — 18 August 2026

- 73 timestamped observations
- 24 projects
- 13 operators
- 9 European countries
- 26 tracked milestones
- 41 unique source URLs
- 12 resolved operations forecast→actual pairs
- 14 non-zero schedule revisions
- 3 capacity revisions
- 1 deliberately preserved same-day source conflict
- 3 terminal negative development events (`canceled`/`denied`)

Countries represented: Denmark, Finland, France, Germany, Ireland, Italy, Portugal, Spain and the United Kingdom.

The normalized ledger SHA-256 fingerprint is generated at runtime so a research result can be tied to the exact corpus version used.

## Storage model

The public seed is sharded under `data/europe-public-events-v2/`. Each JSON file is normalized into a project registry, a source registry and compact immutable events. `load_event_ledger()` can load a single manifest or a directory of shards, then rejects duplicates across the combined corpus.

## Why event sourcing matters

A current project page destroys history. ProofMW needs the opposite: the original target, every revision and the eventual outcome must coexist. Looking only at the latest target can make a late project appear “on time” because the promise itself moved.

The ledger therefore stores what was knowable *when*. `snapshot_as_of()` is the anti-look-ahead primitive for historical experiments, and the walk-forward backtester only lets an outcome enter the history after its actual date became observable.

## Date precision is first-class

Public infrastructure disclosures frequently say “Q3 2022”, “H2 2027” or “2026” rather than an exact day. V0.2 models these as intervals.

For a forecast window and an actual window, ProofMW carries a slippage interval rather than pretending the quarter-end date is exact. This fixed a real calibration bug discovered during enrichment: Start Campus SIN01 was initially being given an artificial delay even though both forecast and observed operation fell inside Q4 2024.

## Primary-source reconstruction

The dataset now includes historical company filings in addition to developer releases and trade reporting. Equinix filings are particularly useful because they preserve old expansion targets. Those older targets reveal schedule drift that disappears if one only reads later project updates.

Examples in the seed include:

- Equinix Madrid 3x-1: initial Q3 2022 target followed by multiple target revisions before opening was reported in Q4 2023.
- Equinix LS2 Lisbon: older company filings and later opening evidence create a resolved history rather than a current-state record.
- atNorth DEN01: initial Q4 2024 target, later revision, then Q4 2025 operation evidence.
- Start Campus SIN02: successive 2026 → 2027 timing revisions and public capacity changes.
- atNorth FIN04: a material contemporaneous disagreement between public sources is preserved as a conflict instead of silently selecting one date.
- German and Irish development cases add denial, cancellation, appeal and pending-permission states.

## Source policy

Every event has an HTTPS source and source class. Current classes include company filings, developer/developer-OEM disclosures, specialist monitoring and trade press.

Source weights are **review/ranking metadata only**. They are not probabilities that a claim is true. Material conflicts remain visible until resolved by better evidence.

## Known concentration problem

The corpus is currently over-represented by Equinix because its historical filings are unusually structured and accessible. That is useful for building the machinery but unsafe for calibration. `data-quality` now exposes operator concentration, and `calibration-readiness` fails if the largest operator exceeds 25% of projects.

## Selection bias

The v1 ledger is a deliberately assembled research seed, not a random sample of all European data-center projects. Discoverable delays are easier to find than quiet on-time deliveries. Descriptive delay statistics therefore **must not** be interpreted as a market-wide delay probability.

The next dataset milestone is 100+ projects, 500+ observations, 100+ resolved operations outcomes, a deliberate on-time control cohort, materially more first-party/regulator evidence and lower operator concentration.
