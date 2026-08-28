# API test suite

Run every public test from `apps/api`:

~~~powershell
$env:PERSISTENCE_BACKEND="memory"
.venv\Scripts\python.exe -m unittest discover -s tests -v
~~~

The suite contains:

- `test_e2e_demo_data.py`: complete import and valuation flow using the three
  synthetic workbooks under `examples/demo-data`;
- `test_financial_examples.py`: independent arithmetic and model-convention
  checks;
- `test_regression_golden_cases.py`: stable clean-price and yield outputs;
- `test_api_hardening.py`: upload, metadata, adapter and persistence behavior.

No test depends on files under the ignored `data/` directory.
