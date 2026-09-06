$ErrorActionPreference = "Stop"
$checks = @(
  "http://localhost:8080/health",
  "http://localhost:8080/dashboard",
  "http://localhost:8080/opportunities",
  "http://localhost:8080/manual-verifications/pending",
  "http://localhost:8080/portfolio",
  "http://localhost:8080/activity",
  "http://localhost:8080/system",
  "http://localhost:3000"
)
foreach ($url in $checks) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 15
    Write-Host "PASS $($r.StatusCode) $url" -ForegroundColor Green
  } catch {
    Write-Host "FAIL $url :: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
  }
}
Write-Host "FC27 app smoke test passed." -ForegroundColor Green
