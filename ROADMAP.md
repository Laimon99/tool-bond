# Roadmap

BondFX is intentionally maintained as a small, explainable public PoC.

## Current baseline — v0.2

- guided manual scenario;
- synthetic Excel import;
- versioned request and response contracts;
- explicit model assumptions and warnings;
- cash-flow-level audit trail;
- independently checkable workbook and regression tests;
- Docker, CI and optional desktop wrapper.

## Near term

- add business-calendar and holiday handling;
- add irregular first/last coupon support;
- add scenario comparison for spot, forwards and clean price;
- add CSV/PDF report export;
- publish a hosted read-only demo with rate limits.

## Longer term

- market-data adapter interfaces;
- multiple bond currencies and quote conventions;
- configurable discounting and compounding conventions;
- authentication, database persistence and multi-user audit history;
- portfolio-level aggregation.

These items are not implied by the current output. See
[docs/MODEL_LIMITATIONS.md](docs/MODEL_LIMITATIONS.md).
