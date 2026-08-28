# BondFX web demo

## Run locally

~~~powershell
npm ci
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
~~~

Open http://localhost:3000.

The predev and prebuild scripts copy the committed synthetic workbooks from
../../examples/demo-data into the generated static public directory.

The interface keeps advanced contract fields available for inspection while
leading with a one-click example and plain-language result interpretation.
