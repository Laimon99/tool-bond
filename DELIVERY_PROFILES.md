# Delivery profiles

BondFX keeps the valuation core independent from its delivery channel.

## Hosted web profile

The public demo separates static and compute workloads:

- Next.js static export: Cloudflare Workers Static Assets;
- FastAPI, Excel normalization and quantitative engine: Render Free;
- persistence: disabled for the public deployment.

Deployment settings are versioned in `deploy/cloudflare/wrangler.jsonc` and
`render.yaml`.

## Local web profile (recommended for development)

The reproducible local stack is:

~~~powershell
docker compose up --build
~~~

- Web UI: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Persistence: in memory by default

This is the reproducible path documented in the root README and exercised by
the public smoke test.

## Desktop profile (optional)

The Electron shell is an optional Windows packaging experiment. It reuses the
same static web application and FastAPI service; it does not contain a second
valuation implementation.

For development, start the web profile, then:

~~~powershell
cd apps/desktop
npm ci
$env:TOOL_BOND_WEB_URL="http://localhost:3000"
npm start
~~~

Node.js 22.12 or newer is required. The standalone Windows build is outside the
primary public quality gate and should be treated as an experimental artifact.
