"""Regression harness against committed golden valuation datasets."""

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


class TestRegressionGoldenCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        golden_path = Path(__file__).parent / "golden_cases.json"
        cls.golden_cases = json.loads(golden_path.read_text(encoding="utf-8"))["cases"]

    def test_golden_cases(self) -> None:
        self.assertGreater(len(self.golden_cases), 0, "No golden cases found.")
        for case in self.golden_cases:
            with self.subTest(case_id=case["case_id"]):
                response = self.client.post("/run-valuation", json=case["request"])
                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                self.assertEqual(body["status"], "success", body)
                result = body["result"]
                self.assertIsNotNone(result, f"Result missing for case {case['case_id']}")
                assumptions = result["model_assumptions"]
                self.assertEqual(assumptions["day_count"], "ACT/365F")
                self.assertEqual(assumptions["fx_rate_side"], "ask")

                expected = case["expected"]
                tolerances = case["tolerances"]
                self.assertAlmostEqual(
                    float(result["npv_usd"]),
                    float(expected["npv_usd"]),
                    delta=float(tolerances["npv_usd"]),
                )
                self.assertAlmostEqual(
                    float(result["pv_usd_total"]),
                    float(expected["pv_usd_total"]),
                    delta=float(tolerances["pv_usd_total"]),
                )
                self.assertAlmostEqual(
                    float(result["dirty_price_percent"]),
                    float(expected["dirty_price_percent"]),
                    delta=float(tolerances["dirty_price_percent"]),
                )
                self.assertAlmostEqual(
                    float(result["notional_try"]),
                    float(expected["notional_try"]),
                    delta=float(tolerances["notional_try"]),
                )
                self.assertEqual(len(result.get("breakdown", [])), int(expected["cashflow_count"]))


if __name__ == "__main__":
    unittest.main()
