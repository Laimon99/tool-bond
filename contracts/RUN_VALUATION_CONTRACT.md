# Run valuation contract

## Endpoint

POST /run-valuation

## Contract files

- Request: contracts/run_valuation.request.schema.json
- Response: contracts/run_valuation.response.schema.json

Manual input and Excel upload must converge to the same RunValuationRequest.
This keeps the quantitative engine independent from the user-interface mode.

## Required payload blocks

- request_id;
- input_mode: manual or excel_import;
- valuation:
  - settlement, budget and spot;
  - bond definition and coupon frequency;
  - USD discount curve;
  - USDTRY forward curve;
  - price input;
  - run options.

## Public model conventions

- bond.day_count is ACT/365F;
- bond.coupon_frequency is one of 1, 2 or 4;
- valuation.options.fx_rate_side is ask by default;
- each breakdown row reports the FX rate and side actually used;
- result.model_assumptions exposes interpolation, extrapolation and NPV
  definitions.

## Response behavior

- status success: result is populated;
- status failed: result is null and errors contains at least one item;
- breakdown is controlled by valuation.options.include_breakdown;
- persistence is controlled by valuation.options.persist_run and is disabled
  by default;

Requests are validated before valuation and run_id is generated server-side.
