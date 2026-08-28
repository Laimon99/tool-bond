# finance_poc profile

This profile represents a client-specific PoC configuration.

## Current behavior
- API adapter id: `finance_poc`
- If `tenant_id` is missing in manual runs, adapter defaults it to `finance_poc`
- Adapter appends informational warnings in import/run responses

## Usage
- Manual run endpoint:
  - `POST /run-valuation?client_id=finance_poc`
- Excel import endpoint:
  - `POST /import/excel` with form field `client_id=finance_poc`

## Future customizations
- Custom input normalization rules
- Custom report formatting
- Custom scenario presets
