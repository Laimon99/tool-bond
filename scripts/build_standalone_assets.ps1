param()

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$webDir = Join-Path $root "apps\web"
$apiDir = Join-Path $root "apps\api"
$quantDir = Join-Path $root "services\quant-engine"
$contractsDir = Join-Path $root "contracts"

$standaloneResources = Join-Path $root "apps\desktop\standalone-resources"
$standaloneWeb = Join-Path $standaloneResources "web"
$standaloneBin = Join-Path $standaloneResources "bin"

Write-Host "Preparing standalone resources folder..."
if (Test-Path $standaloneResources) {
  Remove-Item -Path $standaloneResources -Recurse -Force
}
New-Item -ItemType Directory -Path $standaloneWeb | Out-Null
New-Item -ItemType Directory -Path $standaloneBin | Out-Null

Write-Host "Building static web app (Next export)..."
Push-Location $webDir
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
npm run build | Out-Host
Pop-Location

$webOut = Join-Path $webDir "out"
if (!(Test-Path $webOut)) {
  throw "Web static output folder not found: $webOut"
}
Copy-Item -Path (Join-Path $webOut "*") -Destination $standaloneWeb -Recurse -Force

Write-Host "Building standalone API executable (PyInstaller)..."
$pythonExe = Join-Path $apiDir ".venv\Scripts\python.exe"
if (!(Test-Path $pythonExe)) {
  throw "Python venv not found at $pythonExe"
}

Push-Location $apiDir
& $pythonExe -m pip install pyinstaller | Out-Host
& $pythonExe -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name tool-bond-api `
  --paths $apiDir `
  --paths $quantDir `
  --collect-submodules app `
  --collect-submodules quant_engine `
  --collect-all uvicorn `
  --collect-all fastapi `
  --collect-all pydantic `
  --collect-all jsonschema `
  --collect-all openpyxl `
  --add-data "$contractsDir;contracts" `
  (Join-Path $apiDir "standalone_entry.py") | Out-Host
Pop-Location

$apiExe = Join-Path $apiDir "dist\tool-bond-api.exe"
if (!(Test-Path $apiExe)) {
  throw "Standalone API executable not found: $apiExe"
}
Copy-Item -Path $apiExe -Destination (Join-Path $standaloneBin "tool-bond-api.exe") -Force

Write-Host "Standalone assets prepared at:"
Write-Host " - $standaloneResources"
