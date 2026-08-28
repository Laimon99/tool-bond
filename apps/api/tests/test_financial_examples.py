"""Independently checkable examples for the public valuation conventions."""

from __future__ import annotations

from datetime import date
import math
from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
API_DIR = ROOT / "apps" / "api"
QUANT_DIR = ROOT / "services" / "quant-engine"
for candidate in (API_DIR, QUANT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from app.main import app  # noqa: E402
from quant_engine.valuation import BondTRY, FXForwardCurve  # noqa: E402


class TestFinancialExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_zero_coupon_example_matches_hand_calculation(self) -> None:
        payload = {
            "request_id": "verified_zero_coupon_001",
            "input_mode": "manual",
            "valuation": {
                "settlement_date": "2026-02-20",
                "usd_budget": 100000.0,
                "spot_usdtry": 40.0,
                "bond": {
                    "coupon_rate_annual": 0.0,
                    "coupon_frequency": 1,
                    "face_value_per_unit": 100.0,
                    "issue_date": "2025-02-20",
                    "maturity_date": "2027-02-20",
                    "schedule_dates": ["2027-02-20"],
                    "day_count": "ACT/365F",
                },
                "usd_discount_curve": {
                    "df_points": [{"date": "2027-02-20", "df": 0.95}]
                },
                "fx_forward_curve": {
                    "interpolation": "linear",
                    "pillars": [
                        {"end_date": "2027-02-20", "bid": 49.9, "ask": 50.0}
                    ],
                },
                "price_input": {"type": "clean_price", "value": 100.0},
                "options": {
                    "include_breakdown": True,
                    "persist_run": False,
                    "rounding_decimals": 6,
                    "fx_rate_side": "ask",
                },
            },
        }

        response = self.client.post("/run-valuation", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()["result"]

        # Hand calculation:
        # TRY notional = 100,000 USD * 40 TRY/USD = 4,000,000 TRY.
        # PV USD = 4,000,000 / 50 * 0.95 = 76,000 USD.
        # NPV = 76,000 - 100,000 = -24,000 USD.
        self.assertAlmostEqual(result["notional_try"], 4_000_000.0, delta=0.01)
        self.assertAlmostEqual(result["pv_usd_total"], 76_000.0, delta=0.01)
        self.assertAlmostEqual(result["npv_usd"], -24_000.0, delta=0.01)
        self.assertEqual(len(result["breakdown"]), 1)
        self.assertEqual(result["breakdown"][0]["fx_rate_side"], "ask")
        self.assertAlmostEqual(result["breakdown"][0]["fwd_usdtry_rate"], 50.0)

    def test_loglinear_fx_interpolation_is_not_linear(self) -> None:
        start = date(2026, 1, 1)
        end = date(2027, 1, 1)
        target = date(2026, 7, 2)
        pillars = [(start, 40.0, 42.0), (end, 80.0, 84.0)]
        linear = FXForwardCurve(pillars=pillars, interpolation="linear")
        loglinear = FXForwardCurve(pillars=pillars, interpolation="loglinear")
        weight = (target - start).days / (end - start).days
        expected_log_ask = math.exp((1 - weight) * math.log(42.0) + weight * math.log(84.0))

        self.assertNotAlmostEqual(linear.forward(target, "ask"), loglinear.forward(target, "ask"))
        self.assertAlmostEqual(loglinear.forward(target, "ask"), expected_log_ask, places=12)

    def test_coupon_frequency_scales_coupon_cashflows(self) -> None:
        bond = BondTRY(
            coupon_rate_annual=0.10,
            coupon_frequency=2,
            face_value_per_unit=100.0,
            issue_date=date(2026, 1, 1),
            maturity_date=date(2026, 12, 31),
            schedule_dates=[date(2026, 6, 30), date(2026, 12, 31)],
            day_count="ACT/365F",
        )

        cashflows = bond.cashflows_try(100.0, date(2026, 1, 2))
        self.assertEqual(
            cashflows,
            [(date(2026, 6, 30), 5.0), (date(2026, 12, 31), 105.0)],
        )

    def test_accrued_interest_uses_act_365f(self) -> None:
        bond = BondTRY(
            coupon_rate_annual=0.10,
            coupon_frequency=2,
            face_value_per_unit=100.0,
            issue_date=date(2026, 1, 1),
            maturity_date=date(2027, 1, 1),
            schedule_dates=[date(2026, 7, 1), date(2027, 1, 1)],
            day_count="ACT/365F",
        )

        expected_percent = 0.10 * 90.0 / 365.0 * 100.0
        self.assertAlmostEqual(bond.accrued_percent(date(2026, 4, 1)), expected_percent, places=12)


if __name__ == "__main__":
    unittest.main()
