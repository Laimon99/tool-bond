# BondFX quantitative engine

Framework-independent valuation package used by the API.

Implemented scope:

- ACT/365 Fixed accrued interest;
- annual, semi-annual and quarterly coupon cash flows;
- clean-price and periodic-yield input;
- ask, bid or mid USDTRY conversion;
- linear or log-linear FX interpolation;
- log-linear USD discount-factor interpolation;
- explicit flat-endpoint extrapolation warnings;
- model assumptions returned with every result.

See ../../docs/MODEL_LIMITATIONS.md before interpreting results.
