# Cloudflare deployment

This package deploys the statically exported Next.js interface as an assets-only
Cloudflare Worker. The public FastAPI service runs on Render Free, where run
persistence is disabled and uploaded workbooks are processed in memory.

From the repository root:

~~~powershell
python scripts/prepare_cloudflare.py
cd deploy/cloudflare
npm ci
npm exec wrangler -- deploy
~~~

Override the API endpoint with `--api-base-url` or `BONDFX_PUBLIC_API_URL` when
needed. The default is the public Render service declared in `render.yaml`.
The generated frontend is staged under `.cloudflare-build/`.
