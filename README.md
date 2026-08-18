# ProofMW

**From promised megawatts to bankable compute.**

ProofMW is an evidence-backed probabilistic underwriting engine for AI infrastructure. It converts project evidence into a dependency graph and computes how many megawatts are likely to be physically usable by a given date at explicit confidence levels (`MW@90`, `MW@95`, `MW@99`).

## V0.1 delivered

- AIRS v0.1 project/evidence model.
- Evidence lineage with public/private/synthetic classification.
- Tamper-evident SHA-256 evidence root.
- Dependency-aware Monte Carlo risk engine.
- Shared risk factors to model correlated schedule shocks.
- `MW@Confidence` capacity curves.
- `COD@Confidence` delivery-date distributions.
- Scenario overrides for delay, capacity and derating shocks.
- Guardrail that prevents a public/synthetic demo from masquerading as verified underwriting.
- Europe-first real public case: Start Campus SIN02 (Sines, Portugal), with synthetic assumptions explicitly labelled.
- Optional FastAPI adapter and zero-dependency core CLI.
- Test suite.

## Run

```bash
python -m pip install -e .
proofmw underwrite fixtures/start-campus-sin02-public/project.json \
  --dates 2028-03-31 2028-06-30 2028-12-31
proofmw grade fixtures/start-campus-sin02-public/project.json
```

API (optional):

```bash
python -m pip install -e '.[api]'
uvicorn proofmw.api:app --reload
```

## Important

The bundled SIN02 fixture is **not a credit opinion on Start Campus**. It is a product test built from real public claims plus clearly labelled synthetic uncertainty distributions because no lender data room is publicly available.

See `docs/PRODUCT.md`, `docs/METHODOLOGY.md`, `docs/MARKET_VALIDATION.md`, `docs/MOAT.md`, and `docs/FAILURE_TESTS.md`.
