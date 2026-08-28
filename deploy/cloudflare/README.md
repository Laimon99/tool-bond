# Cloudflare deployment

This package deploys the statically exported Next.js interface and the existing
FastAPI application as one Cloudflare Worker. API calls use the same origin as
the interface. Run persistence is disabled and uploaded workbooks are not
persisted.

From the repository root:

~~~powershell
python scripts/prepare_cloudflare.py
cd deploy/cloudflare
npm ci
uv sync --frozen
uv run pywrangler deploy
~~~

For an unclaimed preview deployment, append `--temporary`. The preparation
script rebuilds the web app with `NEXT_PUBLIC_API_BASE_URL=\"same-origin\"` and
stages only the runtime files required by Wrangler under `.cloudflare-build/`.
