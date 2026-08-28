# Model scope and limitations

BondFX is an educational proof of concept. Its output is a deterministic
illustration under supplied assumptions, not a fair-value opinion or tradeable
quote.

## Implemented conventions

| Area | Current convention |
|---|---|
| Bond currency | TRY |
| Reporting currency | USD |
| FX quote | USDTRY, expressed as TRY per USD |
| FX conversion side | ask by default; bid and mid are optional |
| Coupon frequency | 1, 2 or 4 payments per year |
| Day count | ACT/365 Fixed |
| Yield compounding | periodic, aligned with coupon frequency |
| USD discount factors | supplied points, log-linear interpolation |
| FX forwards | linear or log-linear interpolation |
| Extrapolation | flat endpoint, with response warning |
| NPV | PV of hedged USD cash flows minus initial USD budget |

## Deliberate simplifications

The model does not currently include:

- business-day calendars, settlement lags or holiday adjustment;
- irregular first or final coupon periods;
- inflation linkage, amortization, calls, puts or other embedded options;
- default probabilities, recovery, credit migration or counterparty exposure;
- liquidity, funding, collateral, capital or XVA adjustments;
- transaction costs, brokerage, taxes, withholding or bid/ask beyond the
  selected FX rate side;
- hedge rebalancing, partial hedge ratios or forward settlement mechanics;
- stochastic rates, FX volatility or scenario probabilities;
- live, licensed or guaranteed market data.

The clean-price path assumes the supplied price is valid for the supplied
settlement and schedule. The yield path is a simplified periodic-yield
calculation, not a complete implementation of every market convention.

## Excel normalization

The Excel importer recognizes the committed demonstration layouts. When an
optional value is unavailable, it may synthesize an assumption and returns a
warning. Missing FX pillars are a hard error.

The importer creates USD discount factors from a user-supplied flat continuous
rate. This is visible in the normalized payload and always produces a warning.

## Interpretation

A negative NPV means that the discounted converted cash flows are below the
initial USD budget under the stated assumptions. It is not, on its own, a buy
or sell signal.

Before using a result, inspect:

1. result.model_assumptions;
2. response warnings;
3. the cash-flow breakdown;
4. the source and rights of every input.

Do not use BondFX with real capital without independent validation, production
controls and appropriately licensed data.
