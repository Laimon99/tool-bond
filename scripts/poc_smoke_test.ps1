param(
  [string]$ApiBaseUrl = "http://localhost:8000",
  [string]$WebBaseUrl = "http://localhost:3000"
)

$ErrorActionPreference = "Stop"

Write-Host "Running BondFX smoke test..."

$health = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/health"
if ($health.status -ne "healthy") {
  throw "API health check failed."
}
Write-Host "API /health OK"

$meta = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/meta"
if (-not $meta.version) {
  throw "API /meta missing version."
}
Write-Host "API /meta OK"

$webResponse = Invoke-WebRequest -Method Get -Uri $WebBaseUrl
if ($webResponse.StatusCode -ne 200) {
  throw "Web status check failed."
}
if ($webResponse.Content -notmatch "From TRY bond cash flows") {
  throw "Web content check failed: expected marker text not found."
}
Write-Host "Web homepage OK"

Write-Host "Smoke test completed successfully."
