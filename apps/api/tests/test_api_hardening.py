"""API hardening checks for runtime metadata and file guardrails."""

from __future__ import annotations

from copy import deepcopy
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


class TestApiHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        golden = json.loads((Path(__file__).parent / "golden_cases.json").read_text(encoding="utf-8"))
        cls.valid_payload = golden["cases"][0]["request"]

    def test_meta_endpoint(self) -> None:
        response = self.client.get("/meta")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["service"], "tool-bond-api")
        self.assertIn("version", body)
        self.assertIn("limits", body)
        self.assertEqual(body["features"]["db_required"], False)

    def test_import_rejects_non_excel_file(self) -> None:
        response = self.client.post(
            "/import/excel",
            files=[("files", ("notes.txt", b"hello", "text/plain"))],
            data={
                "usd_budget": "100000",
                "include_breakdown": "true",
                "persist_run": "true",
                "rounding_decimals": "6",
                "usd_flat_rate": "0.05",
            },
        )
        self.assertEqual(response.status_code, 400, response.text)
        body = response.json()
        self.assertEqual(body["status"], "failed")
        self.assertEqual(body["errors"][0]["code"], "UNSUPPORTED_FILE_TYPE")

    def test_run_with_client_adapter_warning(self) -> None:
        payload = {
            "request_id": "req_client_adapter_001",
            "input_mode": "manual",
            "valuation": {
                "settlement_date": "2026-02-20",
                "usd_budget": 100000.0,
                "spot_usdtry": 43.76245,
                "bond": {
                    "coupon_rate_annual": 0.275,
                    "coupon_frequency": 1,
                    "face_value_per_unit": 10000.0,
                    "issue_date": "2023-03-06",
                    "maturity_date": "2028-03-06",
                    "schedule_dates": [
                        "2024-03-06",
                        "2025-03-06",
                        "2026-03-06",
                        "2027-03-06",
                        "2028-03-06",
                    ],
                    "day_count": "ACT/365F",
                },
                "usd_discount_curve": {
                    "df_points": [
                        {"date": "2026-03-06", "df": 0.995},
                        {"date": "2027-03-06", "df": 0.955},
                        {"date": "2028-03-06", "df": 0.91},
                    ]
                },
                "fx_forward_curve": {
                    "interpolation": "linear",
                    "pillars": [
                        {"end_date": "2026-03-06", "bid": 44.2, "ask": 44.3},
                        {"end_date": "2027-03-06", "bid": 58.0, "ask": 58.1},
                        {"end_date": "2028-03-06", "bid": 75.0, "ask": 75.2},
                    ],
                },
                "price_input": {"type": "clean_price", "value": 90.0},
                "options": {
                    "include_breakdown": True,
                    "persist_run": False,
                    "rounding_decimals": 6,
                    "fx_rate_side": "ask",
                },
            },
        }
        response = self.client.post("/run-valuation?client_id=finance_poc", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertIn("finance_poc adapter active.", body["warnings"])

    def test_run_persistence_includes_backend(self) -> None:
        payload = {
            "request_id": "req_storage_backend_001",
            "input_mode": "manual",
            "valuation": {
                "settlement_date": "2026-02-20",
                "usd_budget": 100000.0,
                "spot_usdtry": 43.76245,
                "bond": {
                    "coupon_rate_annual": 0.275,
                    "coupon_frequency": 1,
                    "face_value_per_unit": 10000.0,
                    "issue_date": "2023-03-06",
                    "maturity_date": "2028-03-06",
                    "schedule_dates": [
                        "2024-03-06",
                        "2025-03-06",
                        "2026-03-06",
                        "2027-03-06",
                        "2028-03-06",
                    ],
                    "day_count": "ACT/365F",
                },
                "usd_discount_curve": {
                    "df_points": [
                        {"date": "2026-03-06", "df": 0.995},
                        {"date": "2027-03-06", "df": 0.955},
                        {"date": "2028-03-06", "df": 0.91},
                    ]
                },
                "fx_forward_curve": {
                    "interpolation": "linear",
                    "pillars": [
                        {"end_date": "2026-03-06", "bid": 44.2, "ask": 44.3},
                        {"end_date": "2027-03-06", "bid": 58.0, "ask": 58.1},
                        {"end_date": "2028-03-06", "bid": 75.0, "ask": 75.2},
                    ],
                },
                "price_input": {"type": "clean_price", "value": 90.0},
                "options": {
                    "include_breakdown": True,
                    "persist_run": True,
                    "rounding_decimals": 6,
                    "fx_rate_side": "ask",
                },
            },
        }
        response = self.client.post("/run-valuation", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "success")
        storage = body.get("storage", {})
        self.assertEqual(storage.get("persisted"), True)
        self.assertIsInstance(storage.get("backend"), str)
        self.assertTrue(storage.get("path"))

    def test_run_defaults_to_no_persistence(self) -> None:
        payload = deepcopy(self.valid_payload)
        payload["request_id"] = "req_default_no_persistence"
        payload["valuation"].pop("options")

        response = self.client.post("/run-valuation", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["storage"], {"persisted": False})

    def test_semantic_validation_rejects_incoherent_financial_inputs(self) -> None:
        mutations = {
            "invalid date": lambda payload: payload["valuation"].update(
                {"settlement_date": "2026-99-99"}
            ),
            "settlement outside life": lambda payload: payload["valuation"].update(
                {"settlement_date": "2029-01-01"}
            ),
            "maturity absent from schedule": lambda payload: payload["valuation"]["bond"].update(
                {"schedule_dates": ["2026-03-06", "2027-03-06"]}
            ),
            "crossed FX quote": lambda payload: payload["valuation"]["fx_forward_curve"]["pillars"][0].update(
                {"bid": 44.4, "ask": 44.3}
            ),
            "duplicate discount date": lambda payload: payload["valuation"]["usd_discount_curve"]["df_points"].append(
                {"date": "2026-03-06", "df": 0.994}
            ),
        }

        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = deepcopy(self.valid_payload)
                payload["request_id"] = f"req_semantic_{label.replace(' ', '_')}"
                mutate(payload)
                response = self.client.post("/run-valuation", json=payload)
                self.assertEqual(response.status_code, 400, response.text)
                expected_code = "REQUEST_SCHEMA_ERROR" if label == "invalid date" else "REQUEST_SEMANTIC_ERROR"
                self.assertTrue(any(error["code"] == expected_code for error in response.json()["errors"]), response.text)


if __name__ == "__main__":
    unittest.main()
