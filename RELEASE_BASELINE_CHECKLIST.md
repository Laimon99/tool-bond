# Public release checklist

## Repository hygiene

- [ ] No client, proprietary or live market data is tracked.
- [ ] No credentials, local run artifacts or generated binaries are tracked.
- [ ] README screenshot and synthetic workbook links render correctly.
- [ ] License, security policy and contribution guidance are present.
- [ ] GitHub description, topics and social preview are configured.

## Automated quality gates

~~~powershell
cd apps/api
$env:PERSISTENCE_BACKEND="memory"
.venv\Scripts\python.exe -m unittest discover -s tests -v

cd ../web
npm ci
npm run typecheck
npm run build
npm audit --audit-level=high

cd ../desktop
npm audit --audit-level=high

cd ../..
docker compose config --quiet
~~~

The GitHub Actions workflow repeats the API tests, web typecheck/build,
dependency audits and Compose validation from a clean checkout.

## Manual smoke test

- [ ] Start `docker compose up --build -d`.
- [ ] Run `./scripts/poc_smoke_test.ps1`.
- [ ] Select **Run the example** and confirm a successful valuation.
- [ ] Import all three workbooks under `examples/demo-data` and confirm that
      normalization warnings remain visible.
- [ ] Check desktop and narrow/mobile layouts.

## Publishing

- [ ] Review `docs/MODEL_LIMITATIONS.md` with a qualified finance reviewer.
- [ ] Commit the curated files and push them.
- [ ] Make the GitHub repository public only after the checks above pass.
- [ ] Create the first version tag when the public baseline is approved.
