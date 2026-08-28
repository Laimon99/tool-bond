# Contributing

Thanks for considering a contribution to BondFX.

## Before opening a pull request

1. Open an issue for material model or contract changes.
2. Never commit client data, licensed market data, credentials or generated
   desktop binaries.
3. Keep financial assumptions explicit and add an independently checkable test
   for every valuation change.
4. Run the local quality gates:

   ```powershell
   cd apps/api
   .venv\Scripts\python.exe -m unittest discover -s tests -v

   cd ../web
   npm ci
   npm run typecheck
   npm run build
   ```

5. Update documentation when behavior, contracts or limitations change.

## Pull requests

Keep changes focused, describe the financial and technical rationale, and call
out any new approximation. All checks must pass before merge.
