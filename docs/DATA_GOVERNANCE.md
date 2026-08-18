# Data governance and defensibility

ProofMW's moat is the longitudinal evidence graph, not scraped text.

## Immutable observation principle

Never rewrite an old forecast because a newer page changed. Append a new observation. Corrections should be additive and linked to the superseded event.

## Provenance requirements

Every production observation should eventually carry source/document identifier, publication or observation date, retrieval timestamp, source class, exact excerpt or structured claim, parser/extractor version, verification status and a content hash where legally/technically possible.

The v1 public manifest already separates project identity, source identity and event history. Deterministic event hashes let the ingestion layer reject exact duplicates.

## Conflict policy

ProofMW must not choose a convenient source silently. Material date/capacity conflicts are first-class objects and should reduce downstream confidence until resolved.

## Private-data flywheel

The strategic step is contractual rights to use anonymized planned-vs-actual outcomes from lenders, developers, EPCs, OEMs and insurers for aggregate calibration. Raw client documents remain segregated; derived anonymous calibration statistics can become cross-client proprietary IP where contracts permit.

## Anti-copy strategy

A competitor can copy UI and formulas. It is materially harder to recreate years of timestamped forecast revisions, actual outcomes, source conflicts, private milestone attestations and backtested calibration history.
