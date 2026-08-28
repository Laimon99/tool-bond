# Optional desktop shell

The Electron application wraps the BondFX web UI. It is experimental and not
part of the primary public demo.

## Development

Node.js 22.12 or newer is required. Start the Docker or local web/API profile,
then run:

~~~powershell
npm ci
$env:TOOL_BOND_WEB_URL="http://localhost:3000"
npm start
~~~

## Standalone Windows build

~~~powershell
npm ci
npm run build:win
~~~

The build script prepares a static web bundle and a local API executable before
creating a portable Windows artifact under `artifacts/desktop-standalone`.
Generated artifacts and staging resources are ignored by Git.
