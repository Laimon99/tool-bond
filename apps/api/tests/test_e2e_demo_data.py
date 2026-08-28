"""End-to-end validation against committed synthetic demo workbooks."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
API_DIR = ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.main import app  # noqa: E402
from app.schema_validation import validate_request, validate_response  # noqa: E402


class TestE2EDemoData(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.data_dir = ROOT / "examples" / "demo-data"
        cls.expected = json.loads(
            (Path(__file__).parent / "demo_expected_values.json").read_text(encoding="utf-8")
        )

    def test_synthetic_demo_e2e_flow(self) -> None:
        required_files = ["Curve_swap.xlsx", "bond_storico.xlsx", "Bond_tURCO.xlsx"]
        for name in required_files:
            self.assertTrue((self.data_dir / name).exists(), f"Missing public demo file: {name}")

        files = [
            (
                "files",
                (
                    name,
                    (self.data_dir / name).read_bytes(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            )
            for name in required_files
        ]

        import_response = self.client.post(
            "/import/excel",
            files=files,
            data={
                "usd_budget": "100000",
                "include_breakdown": "true",
                "persist_run": "false",
                "rounding_decimals": "6",
                "usd_flat_rate": "0.05",
            },
        )
        self.assertEqual(import_response.status_code, 200, import_response.text)
        import_body = import_response.json()
        self.assertEqual(import_body.get("status"), "success", import_body)
        self.assertEqual(import_body.get("errors"), [], import_body)
        self.assertIn(
            "USD discount curve synthesized from flat rate for PoC normalization.",
            import_body.get("warnings", []),
        )

        normalized = import_body.get("normalized_request")
        self.assertIsNotNone(normalized, "normalized_request missing from /import/excel")
        self.assertEqual(validate_request(normalized), [])

        valuation = normalized["valuation"]
        self.assertEqual(valuation["settlement_date"], self.expected["settlement_date"])
        self.assertAlmostEqual(
            float(valuation["spot_usdtry"]),
            float(self.expected["spot_usdtry"]),
            delta=float(self.expected["spot_tolerance"]),
        )
        self.assertEqual(
            len(valuation["fx_forward_curve"]["pillars"]),
            int(self.expected["fx_pillars"]),
        )
        self.assertEqual(
            len(valuation["usd_discount_curve"]["df_points"]),
            int(self.expected["df_points"]),
        )
        self.assertEqual(valuation["price_input"]["type"], "clean_price")
        self.assertAlmostEqual(
            float(valuation["price_input"]["value"]),
            float(self.expected["clean_price"]),
            delta=float(self.expected["price_tolerance"]),
        )

        run_response = self.client.post("/run-valuation", json=normalized)
        self.assertEqual(run_response.status_code, 200, run_response.text)
        run_body = run_response.json()
        self.assertEqual(run_body.get("status"), "success", run_body)
        self.assertEqual(run_body.get("errors"), [], run_body)
        self.assertEqual(validate_response(run_body), [])

        result = run_body["result"]
        self.assertAlmostEqual(
            float(result["npv_usd"]),
            float(self.expected["npv_usd"]),
            delta=float(self.expected["npv_tolerance"]),
        )
        self.assertEqual(len(result["breakdown"]), int(self.expected["cashflow_count"]))
        self.assertEqual(result["model_assumptions"]["fx_rate_side"], "ask")
        self.assertEqual(result["model_assumptions"]["day_count"], "ACT/365F")
        self.assertEqual(run_body["storage"], {"persisted": False})


if __name__ == "__main__":
    unittest.main()
