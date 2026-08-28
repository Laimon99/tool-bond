# Client Modules

This folder contains client-specific assets and documentation, separated from the reusable core.

## Convention
- One folder per client: `clients/<client_id>/`
- Core code stays in `apps/*` and `services/*`
- Custom behavior is wired through API adapters in `apps/api/app/client_modules/`

## Current client profiles
- `finance_poc` (example profile)

## Why this matters
- No project fork per client
- Reusable skeleton stays stable
- Client differences remain explicit and isolated
