# BondFX

[![CI](https://github.com/Laimon99/tool-bond/actions/workflows/ci.yml/badge.svg)](https://github.com/Laimon99/tool-bond/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-167D78.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-17233C.svg)](https://www.python.org/)

BondFX turns a Turkish-lira bond into an auditable USD valuation, showing each
cash flow, currency conversion and discounting step.

**[Try the live demo](https://bondfx-demo.trail-seahorse.workers.dev/)** ·
[See how the result is verified](#verification)

![BondFX demo](docs/images/demo.png)

> **Educational use only.** BondFX is not investment advice, a trading system,
> an executable market quote or a production pricing library.

## Project in 30 seconds

- **Problem:** cross-currency bond analysis is often split across spreadsheets
  and manual calculations that are difficult to audit.
- **Input:** use a guided example or import three synthetic Excel workbooks.
- **Output:** see the TRY amount invested, the USD value of every hedged cash
  flow, the total present value and the NPV versus the initial USD budget.
- **Value:** assumptions, warnings and intermediate calculations remain visible
  instead of being hidden inside a black-box result.

## What this project demonstrates

- **Finance engineering:** bond schedules, forward FX conversion, discounting
  and explicit model conventions.
- **Explainable product design:** one workflow for guided inputs and Excel
  imports, with a cash-flow-level audit trail.
- **Full-stack delivery:** a Next.js interface, a FastAPI service and a
  framework-independent Python valuation engine.
- **Reproducibility:** synthetic data, versioned JSON contracts, an independently
  checkable spreadsheet and automated tests in CI.

## Try it

Open the **[hosted public demo](https://bondfx-demo.trail-seahorse.workers.dev/)**
and select **Run the example**. The app starts with a complete synthetic
scenario, so no files or configuration are required.

The [API documentation](https://bondfx-api-laimon99.onrender.com/docs) is also
public. The FastAPI service runs on a free Render instance and can take up to
about a minute to wake after a period without traffic. Uploaded workbooks are
processed in memory and are not persisted by the public deployment.

### Try the Excel flow

Download or select these three committed synthetic files together:

- [Curve_swap.xlsx](examples/demo-data/Curve_swap.xlsx)
- [bond_storico.xlsx](examples/demo-data/bond_storico.xlsx)
- [Bond_tURCO.xlsx](examples/demo-data/Bond_tURCO.xlsx)

The files contain no client data, proprietary data or live market observations.

## How BondFX works

BondFX makes the valuation workflow explicit and repeatable:

1. normalize manual or Excel inputs to one JSON contract;
2. validate every request;
3. generate the bond cash-flow schedule;
4. convert TRY cash flows with selected USDTRY forward rates;
5. discount the resulting USD cash flows;
6. return the assumptions, warnings and cash-flow-level audit trail.

## Verification

[verified-example.xlsx](examples/demo-data/verified-example.xlsx) derives a
one-period zero-coupon case using visible spreadsheet formulas:

~~~text
TRY notional = 100,000 USD × 40 USDTRY = 4,000,000 TRY
PV USD       = 4,000,000 TRY ÷ 50 forward ask × 0.95 DF = 76,000 USD
NPV USD      = 76,000 − 100,000 = −24,000 USD
~~~

The same example is asserted independently in the Python test suite. See
[Validation](docs/VALIDATION.md) for the complete evidence chain.

## Architecture

~~~text
Next.js UI
    │  Cloudflare static assets
    ▼
FastAPI validation and orchestration (Render Free)
    │
    ├── Excel normalization
    ├── JSON Schema contracts
    └── persistence adapter (memory by default)
            │
            ▼
Python quantitative engine
~~~

The same request contract is used by manual input and Excel import. See
[Architecture](docs/ARCHITECTURE.md) and
[Run valuation contract](contracts/RUN_VALUATION_CONTRACT.md).

## Model scope

The public contract deliberately supports a narrow, documented scope:

- USDTRY means TRY per USD;
- the default conversion side is ask, representing the conservative rate used
  when buying USD with TRY;
- supported coupon frequencies are annual, semi-annual and quarterly;
- day count is ACT/365 Fixed;
- discount factors are interpolated log-linearly;
- FX forwards support linear or log-linear interpolation;
- curve endpoints are held flat and generate an explicit warning;
- NPV is the hedged USD cash-flow present value minus the initial USD budget.

Every successful API response includes these conventions in
`result.model_assumptions`. Read [Model limitations](docs/MODEL_LIMITATIONS.md)
before interpreting results.

## Run locally

For an immediate local start, use Docker:

~~~powershell
git clone https://github.com/Laimon99/tool-bond.git
cd tool-bond
docker compose up --build
~~~

Then open:

- Web app: http://localhost:3000
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Developer setup

<details>
<summary>Run the API and web app separately</summary>

#### API

~~~powershell
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PERSISTENCE_BACKEND="memory"
python -m uvicorn app.main:app --reload --port 8000
~~~

#### Web

Node.js 22.12 or newer is recommended.

~~~powershell
cd apps/web
npm ci
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
~~~

</details>

### Quality gates

~~~powershell
cd apps/api
.venv\Scripts\python.exe -m unittest discover -s tests -v

cd ../web
npm run typecheck
npm run build

cd ../..
docker compose config --quiet
~~~

CI runs the same public test suite from a clean checkout.

## Repository map

~~~text
apps/
  api/             FastAPI service and tests
  web/             Next.js public demo
  desktop/         optional Electron wrapper
contracts/         versioned request/response JSON Schemas
examples/          synthetic demo and validation workbooks
services/
  quant-engine/    framework-independent valuation core
docs/              architecture, validation and model scope
~~~

## Privacy and security

- Real or client source files under `data/` are ignored.
- Runtime artifacts, uploaded data and local runs are ignored.
- The default Docker profile uses in-memory persistence.
- Confidential workbooks must not be submitted in issues or pull requests.

See the [security policy](SECURITY.md).

## Project status

BondFX is a complete public proof of concept, not a production valuation
platform. Planned extensions are tracked in [ROADMAP.md](ROADMAP.md).
Maintainers can use the [public-release settings](docs/PUBLIC_RELEASE.md) and
[release checklist](RELEASE_BASELINE_CHECKLIST.md) before changing repository
visibility.

## License

Released under the [MIT License](LICENSE).
