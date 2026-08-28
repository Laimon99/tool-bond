# Architecture

BondFX is a small monorepo with one quantitative core and two delivery profiles.

## Request flow

~~~text
Manual form ───────────────┐
                           ├─> RunValuationRequest JSON Schema
Synthetic Excel workbooks ─┘             │
                                         ▼
                              FastAPI orchestration
                                         │
                          client adapter │ persistence adapter
                                         ▼
                               Python quant engine
                                         │
                                         ▼
                         RunValuationResponse JSON Schema
~~~

Manual and Excel input deliberately converge before valuation. The quantitative
engine does not know whether a payload came from a browser form or workbook.

## Components

### Web app

The Next.js app is a static export. It provides:

- a one-click synthetic scenario;
- guided inputs for the most important variables;
- advanced contract inputs behind a disclosure;
- synthetic Excel downloads and upload;
- interpretation, warnings, assumptions and technical JSON.

### API

FastAPI owns transport concerns, upload limits, schema validation,
normalization, response shaping and optional persistence.

### Quantitative engine

The Python package under services/quant-engine has no FastAPI dependency. It
owns cash-flow generation, accrued interest, price-from-yield, FX conversion
and USD discounting.

### Contracts

JSON Schema files under contracts/ are the public integration boundary.
Additional properties are rejected so contract drift is visible.

### Persistence

Memory is the public-demo default. Local-file persistence remains available for
development and the optional desktop wrapper. The app never requires a
database.

## Extension points

- apps/api/app/client_modules: client-specific preprocessing;
- apps/api/app/persistence: storage backends;
- services/quant-engine: reusable financial logic;
- contracts: versioned API boundary.

See [SKELETON_CORE_CUSTOM_GUIDE.md](../SKELETON_CORE_CUSTOM_GUIDE.md) for the
core/custom separation.
