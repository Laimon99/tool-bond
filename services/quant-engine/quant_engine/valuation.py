"""Transparent bond + FX-forward valuation logic for the educational PoC.

The engine deliberately supports a narrow set of conventions. Every convention
used in a result is returned in model_assumptions and the public limitations
document explains what is outside scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
from typing import Any, Dict, List, Tuple

Date = date
SUPPORTED_DAY_COUNT = "ACT/365F"
SUPPORTED_COUPON_FREQUENCIES = {1, 2, 4}
SUPPORTED_FX_SIDES = {"mid", "bid", "ask"}


def _year_frac_act_365f(start: Date, end: Date) -> float:
    """ACT/365 Fixed year fraction."""
    return (end - start).days / 365.0


def _interp_loglinear_df(df_points: Dict[Date, float], target: Date) -> float:
    dates = sorted(df_points.keys())
    if not dates:
        raise ValueError("usd_discount_curve.df_points is empty.")
    if target <= dates[0]:
        return df_points[dates[0]]
    if target >= dates[-1]:
        return df_points[dates[-1]]
    for i in range(len(dates) - 1):
        d0, d1 = dates[i], dates[i + 1]
        if d0 <= target <= d1:
            w = (target - d0).days / (d1 - d0).days
            ln_df = (1 - w) * math.log(df_points[d0]) + w * math.log(df_points[d1])
            return math.exp(ln_df)
    return df_points[dates[-1]]


@dataclass
class USDDiscountCurve:
    df_points: Dict[Date, float]

    def df(self, target: Date) -> float:
        return _interp_loglinear_df(self.df_points, target)

    def requires_extrapolation(self, target: Date) -> bool:
        dates = sorted(self.df_points)
        return bool(dates) and (target < dates[0] or target > dates[-1])


@dataclass
class FXForwardCurve:
    pillars: List[Tuple[Date, float, float]]
    interpolation: str = "linear"

    def forward(self, target: Date, side: str = "ask") -> float:
        if not self.pillars:
            raise ValueError("fx_forward_curve.pillars is empty.")
        if side not in SUPPORTED_FX_SIDES:
            raise ValueError(f"Unsupported FX rate side '{side}'.")

        ps = sorted(self.pillars, key=lambda x: x[0])
        bid: float
        ask: float

        if target <= ps[0][0]:
            bid, ask = ps[0][1], ps[0][2]
        elif target >= ps[-1][0]:
            bid, ask = ps[-1][1], ps[-1][2]
        else:
            for i in range(len(ps) - 1):
                d0, b0, a0 = ps[i]
                d1, b1, a1 = ps[i + 1]
                if d0 <= target <= d1:
                    w = (target - d0).days / (d1 - d0).days
                    if self.interpolation == "loglinear":
                        bid = math.exp((1 - w) * math.log(b0) + w * math.log(b1))
                        ask = math.exp((1 - w) * math.log(a0) + w * math.log(a1))
                    else:
                        bid = (1 - w) * b0 + w * b1
                        ask = (1 - w) * a0 + w * a1
                    break
            else:  # pragma: no cover - sorted interval loop is exhaustive
                bid, ask = ps[-1][1], ps[-1][2]

        mid = (bid + ask) / 2.0
        return {"mid": mid, "bid": bid, "ask": ask}[side]

    def requires_extrapolation(self, target: Date) -> bool:
        dates = sorted(p[0] for p in self.pillars)
        return bool(dates) and (target < dates[0] or target > dates[-1])


@dataclass
class BondTRY:
    coupon_rate_annual: float
    coupon_frequency: int
    face_value_per_unit: float
    issue_date: Date
    maturity_date: Date
    schedule_dates: List[Date]
    day_count: str = SUPPORTED_DAY_COUNT

    def __post_init__(self) -> None:
        if self.day_count != SUPPORTED_DAY_COUNT:
            raise ValueError(f"Only {SUPPORTED_DAY_COUNT} is supported by this PoC.")
        if self.coupon_frequency not in SUPPORTED_COUPON_FREQUENCIES:
            raise ValueError("coupon_frequency must be one of 1, 2 or 4.")
        if self.issue_date >= self.maturity_date:
            raise ValueError("issue_date must be before maturity_date.")
        if self.maturity_date not in self.schedule_dates:
            raise ValueError("schedule_dates must include maturity_date.")
        if any(d <= self.issue_date or d > self.maturity_date for d in self.schedule_dates):
            raise ValueError("Every schedule date must be after issue_date and on or before maturity_date.")

    @property
    def coupon_rate_per_period(self) -> float:
        return self.coupon_rate_annual / self.coupon_frequency

    def accrued_percent(self, settlement: Date) -> float:
        previous_dates = [self.issue_date, *[d for d in self.schedule_dates if d <= settlement]]
        next_dates = [d for d in self.schedule_dates if d > settlement]
        if not next_dates:
            return 0.0
        previous = max(previous_dates)
        if settlement <= previous:
            return 0.0
        return self.coupon_rate_annual * _year_frac_act_365f(previous, settlement) * 100.0

    def price_from_yield(self, ytm_annual: float, settlement: Date) -> float:
        periodic_base = 1.0 + ytm_annual / self.coupon_frequency
        if periodic_base <= 0:
            raise ValueError("Yield produces an invalid discount base.")

        pv = 0.0
        for cashflow_date, amount in self.cashflows_try(self.face_value_per_unit, settlement):
            t = _year_frac_act_365f(settlement, cashflow_date)
            discount_factor = periodic_base ** (-self.coupon_frequency * t)
            pv += amount * discount_factor
        return 100.0 * pv / self.face_value_per_unit

    def cashflows_try(self, notional_try: float, settlement: Date) -> List[Tuple[Date, float]]:
        by_date: Dict[Date, float] = {}
        coupon_amount = notional_try * self.coupon_rate_per_period
        for cashflow_date in self.schedule_dates:
            if cashflow_date > settlement:
                by_date[cashflow_date] = by_date.get(cashflow_date, 0.0) + coupon_amount
        if self.maturity_date > settlement:
            by_date[self.maturity_date] = by_date.get(self.maturity_date, 0.0) + notional_try
        return sorted(by_date.items())


@dataclass
class HedgedNPVResult:
    notional_try: float
    units: float
    dirty_price_percent: float
    breakdown: List[Dict[str, Any]]
    pv_usd_total: float
    npv_usd: float
    warnings: List[str]


def compute_npv_usd(
    usd_budget: float,
    settlement: Date,
    bond: BondTRY,
    fx_curve: FXForwardCurve,
    usd_curve: USDDiscountCurve,
    spot_usdtry: float,
    price_input: Dict[str, Any],
    fx_rate_side: str = "ask",
) -> HedgedNPVResult:
    if settlement < bond.issue_date or settlement >= bond.maturity_date:
        raise ValueError("settlement_date must be on or after issue_date and before maturity_date.")
    if price_input["type"] == "ytm":
        clean_pct = bond.price_from_yield(float(price_input["value"]), settlement)
    else:
        clean_pct = float(price_input["value"])

    accrued_pct = bond.accrued_percent(settlement)
    dirty_pct = clean_pct + accrued_pct

    try_available = usd_budget * spot_usdtry
    cost_per_unit_try = dirty_pct * bond.face_value_per_unit / 100.0
    if cost_per_unit_try <= 0:
        raise ValueError("Invalid cost_per_unit_try computed from inputs.")

    units = try_available / cost_per_unit_try
    notional_try = units * bond.face_value_per_unit

    cfs_try = bond.cashflows_try(notional_try, settlement)
    breakdown: List[Dict[str, Any]] = []
    warnings: List[str] = []
    pv_total = 0.0
    fx_extrapolated = False
    usd_extrapolated = False

    for cashflow_date, amount_try in cfs_try:
        fx_extrapolated = fx_extrapolated or fx_curve.requires_extrapolation(cashflow_date)
        usd_extrapolated = usd_extrapolated or usd_curve.requires_extrapolation(cashflow_date)
        fwd_rate = fx_curve.forward(cashflow_date, side=fx_rate_side)
        usd_amount = amount_try / fwd_rate
        df_usd = usd_curve.df(cashflow_date)
        pv = usd_amount * df_usd
        breakdown.append(
            {
                "date": cashflow_date.isoformat(),
                "try_cashflow": amount_try,
                "fwd_usdtry_rate": fwd_rate,
                "fx_rate_side": fx_rate_side,
                "usd_cashflow": usd_amount,
                "usd_df": df_usd,
                "pv_usd": pv,
            }
        )
        pv_total += pv

    if fx_extrapolated:
        warnings.append("At least one cash flow uses flat endpoint extrapolation of the FX forward curve.")
    if usd_extrapolated:
        warnings.append("At least one cash flow uses flat endpoint extrapolation of the USD discount curve.")

    return HedgedNPVResult(
        notional_try=notional_try,
        units=units,
        dirty_price_percent=dirty_pct,
        breakdown=breakdown,
        pv_usd_total=pv_total,
        npv_usd=pv_total - usd_budget,
        warnings=warnings,
    )


def run_valuation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compute a valuation result from a validated RunValuationRequest payload."""
    valuation = payload["valuation"]

    settlement = Date.fromisoformat(valuation["settlement_date"])
    bond_in = valuation["bond"]
    bond = BondTRY(
        coupon_rate_annual=float(bond_in["coupon_rate_annual"]),
        coupon_frequency=int(bond_in.get("coupon_frequency", 1)),
        face_value_per_unit=float(bond_in["face_value_per_unit"]),
        issue_date=Date.fromisoformat(bond_in["issue_date"]),
        maturity_date=Date.fromisoformat(bond_in["maturity_date"]),
        schedule_dates=sorted(Date.fromisoformat(d) for d in bond_in["schedule_dates"]),
        day_count=bond_in.get("day_count", SUPPORTED_DAY_COUNT),
    )

    usd_points = {
        Date.fromisoformat(row["date"]): float(row["df"])
        for row in valuation["usd_discount_curve"]["df_points"]
    }
    usd_curve = USDDiscountCurve(df_points=usd_points)

    fx_curve_in = valuation["fx_forward_curve"]
    fx_pillars = [
        (Date.fromisoformat(row["end_date"]), float(row["bid"]), float(row["ask"]))
        for row in fx_curve_in["pillars"]
    ]
    fx_curve = FXForwardCurve(
        pillars=fx_pillars,
        interpolation=fx_curve_in.get("interpolation", "linear"),
    )
    fx_rate_side = valuation.get("options", {}).get("fx_rate_side", "ask")

    result = compute_npv_usd(
        usd_budget=float(valuation["usd_budget"]),
        settlement=settlement,
        bond=bond,
        fx_curve=fx_curve,
        usd_curve=usd_curve,
        spot_usdtry=float(valuation["spot_usdtry"]),
        price_input=valuation["price_input"],
        fx_rate_side=fx_rate_side,
    )

    return {
        "notional_try": result.notional_try,
        "units": result.units,
        "dirty_price_percent": result.dirty_price_percent,
        "pv_usd_total": result.pv_usd_total,
        "npv_usd": result.npv_usd,
        "breakdown": result.breakdown,
        "model_assumptions": {
            "day_count": bond.day_count,
            "coupon_frequency": bond.coupon_frequency,
            "fx_quote_convention": "USDTRY (TRY per USD)",
            "fx_rate_side": fx_rate_side,
            "fx_interpolation": fx_curve.interpolation,
            "discount_factor_interpolation": "log-linear",
            "curve_extrapolation": "flat endpoint",
            "npv_definition": "PV of hedged USD cash flows minus initial USD budget",
        },
        "_warnings": result.warnings,
    }
