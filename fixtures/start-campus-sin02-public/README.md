# Start Campus SIN02 public-information fixture

This fixture is deliberately **not** presented as a real lender data room or a credit opinion on Start Campus.
It combines verified public claims about the SINES campus/SIN02 with synthetic uncertainty distributions so the ProofMW V1 engine can be exercised end-to-end.

## Why this project

SIN02 is a useful European test case because public sources expose several different evidence classes that ProofMW must reconcile: developer statements, OCP facility material, and Portuguese environmental-process records.

## Public vs synthetic

- `kind=public`: a claim observed in a public source.
- `kind=synthetic`: an explicit modelling assumption used only because private EPC, interconnection, commissioning, carrier and financing documents are unavailable.

A production underwriting must never silently promote a synthetic assumption to verified evidence.
