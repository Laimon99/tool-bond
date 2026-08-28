# Validation

BondFX separates three different kinds of evidence.

## 1. Independently checkable example

[verified-example.xlsx](../examples/demo-data/verified-example.xlsx) is a
formula-driven, one-period zero-coupon case. Its Checks sheet derives:

- 4,000,000 TRY notional;
- 76,000 USD present value;
- -24,000 USD NPV.

The arithmetic is intentionally simple enough to reproduce with a calculator:

~~~text
4,000,000 TRY = 100,000 USD × 40 TRY/USD
76,000 USD    = 4,000,000 TRY ÷ 50 TRY/USD × 0.95
-24,000 USD   = 76,000 USD − 100,000 USD
~~~

The Python test test_financial_examples.py asserts the same result without
reading expected values from the engine.

## 2. Public end-to-end fixture

test_e2e_demo_data.py uploads the three committed synthetic workbooks, validates
the normalized request, runs the valuation and validates the response contract.
This proves a fresh clone can exercise the complete public workflow.

## 3. Regression cases

golden_cases.json locks expected output for clean-price and yield paths.
Regression values detect unintended changes; they are not a substitute for
independent financial validation.

## Additional coverage

The test suite also verifies:

- ask-side FX conversion;
- distinct linear and log-linear FX interpolation;
- coupon-frequency scaling;
- request and response schemas;
- upload guardrails;
- client adapter behavior;
- memory and local-file persistence interfaces.

## Reproduce

~~~powershell
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PERSISTENCE_BACKEND="memory"
python -m unittest discover -s tests -v
~~~

All tests use synthetic data committed under examples/demo-data.
