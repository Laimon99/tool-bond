# Synthetic demo data

These workbooks are intentionally synthetic and redistributable. They contain
no client data, licensed market data or real trading recommendation.

Use all three files together in the Excel upload flow:

- `Curve_swap.xlsx`: synthetic USDTRY spot and forward pillars;
- `bond_storico.xlsx`: illustrative annual-coupon bond and clean price;
- `Bond_tURCO.xlsx`: synthetic yield history.

`verified-example.xlsx` is a separate, formula-driven zero-coupon example.
Its Checks sheet independently derives:

- TRY notional: 4,000,000;
- PV of the hedged USD cash flow: 76,000;
- NPV: -24,000.

The API tests use these public fixtures. Changes to the import contract or
valuation conventions must update the fixtures, validation workbook and tests
together.
