# GitHub public-release settings

Use these values when the local baseline has been committed and pushed.

## Repository profile

- **Description:** Educational Bond + FX valuation demo with guided/Excel
  inputs, USDTRY forwards and an auditable USD NPV.
- **Website:** https://bondfx-demo.trail-seahorse.workers.dev
- **Topics:** `fixed-income`, `bonds`, `foreign-exchange`,
  `quantitative-finance`, `financial-modeling`, `fastapi`, `nextjs`, `python`,
  `typescript`, `educational`.
- **Social preview:** use `docs/images/social-preview.png`.

## Recommended repository settings

1. Keep the repository private until the release checklist passes from the
   exact commit that will be published.
2. Enable Issues and private vulnerability reporting.
3. Enable Dependabot alerts, security updates and secret scanning where the
   account plan supports them.
4. Protect `main`: require the CI workflow and block force pushes.
5. Keep GitHub Pages disabled; the supported public frontend is the Cloudflare
   static deployment backed by the Render API.

## First public release

1. Commit and push the curated baseline.
2. Confirm CI passes on GitHub.
3. Review the repository file list and generated social preview.
4. Change visibility to public.
5. Create a tagged release and move the changelog entries out of Unreleased.

Changing visibility and publishing a release are intentionally separate from
the local preparation performed in this repository.
