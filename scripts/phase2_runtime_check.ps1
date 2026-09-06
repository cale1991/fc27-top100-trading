param(
    [ValidateSet("Auto", "CleanInstall", "Upgrade")]
    [string]$Mode = "Auto",
    [int]$ApiTimeoutSeconds = 90,
    [int]$WebTimeoutSeconds = 90
)

$ErrorActionPreference = "Stop"
$script:Failures = New-Object System.Collections.Generic.List[string]

function Write-Pass([string]$Name) {
    Write-Host "PASS: $Name" -ForegroundColor Green
}

function Write-Fail([string]$Name, [string]$Message) {
    $entry = "$Name :: $Message"
    $script:Failures.Add($entry)
    Write-Host "FAIL: $entry" -ForegroundColor Red
}

function Invoke-RequiredNative([string]$Name, [scriptblock]$Command) {
    Write-Host "== $Name ==" -ForegroundColor Cyan
    try {
        & $Command | Out-Host
        $code = $LASTEXITCODE
        if ($code -ne 0) {
            throw "native command exited with code $code"
        }
        Write-Pass $Name
        return $true
    } catch {
        Write-Fail $Name $_.Exception.Message
        return $false
    }
}

function Wait-HttpReady([string]$Name, [string]$Url, [int]$TimeoutSeconds) {
    Write-Host "Waiting for $Name readiness: $Url" -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $attempt = 0
    $lastError = "not attempted"
    while ((Get-Date) -lt $deadline) {
        $attempt += 1
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Pass "$Name readiness (attempt $attempt)"
                return $true
            }
            $lastError = "HTTP $($response.StatusCode)"
        } catch {
            $lastError = $_.Exception.Message
        }
        $sleepSeconds = [Math]::Min(1 + [Math]::Floor($attempt / 4), 5)
        Start-Sleep -Seconds $sleepSeconds
    }
    Write-Fail "$Name readiness" "timed out after ${TimeoutSeconds}s; last error: $lastError"
    return $false
}

Write-Host "== FC26 Phase 2 runtime check ==" -ForegroundColor Cyan
Write-Host "Mode: $Mode" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    if ($Mode -eq "Upgrade") {
        Write-Warning "UPGRADE mode: .env is missing in the new release directory. Preserve/copy the previous release's .env here BEFORE relying on credentialed providers. This script will not search for, copy, or print secrets."
        Write-Warning "Creating a blank .env from .env.example so credential-free services (including FUTZIP) can still be validated."
    } elseif ($Mode -eq "CleanInstall") {
        Write-Host "CLEAN INSTALL: creating a blank .env from .env.example. No credentials are included." -ForegroundColor Yellow
    } else {
        Write-Host "AUTO mode: .env is missing; creating a blank .env from .env.example." -ForegroundColor Yellow
        Write-Warning "If this is an UPGRADE, copy/preserve the previous .env into this directory before enabling credentialed providers."
    }
    Copy-Item .env.example .env
} else {
    if ($Mode -eq "Upgrade") {
        Write-Host "UPGRADE mode: existing .env preserved in this directory; contents will not be printed." -ForegroundColor Yellow
    } else {
        Write-Host "Existing .env found; contents will not be printed or modified." -ForegroundColor Yellow
    }
}

$buildOk = Invoke-RequiredNative "Docker build" { docker compose build }
if (-not $buildOk) {
    Write-Host "Phase 2 runtime validation FAILED before startup." -ForegroundColor Red
    exit 1
}

$startOk = Invoke-RequiredNative "Start services and migrations" { docker compose up -d }
if (-not $startOk) {
    Write-Host "Phase 2 runtime validation FAILED during startup." -ForegroundColor Red
    exit 1
}

Invoke-RequiredNative "Service state" { docker compose ps } | Out-Null
$apiReady = Wait-HttpReady "API" "http://localhost:8080/health" $ApiTimeoutSeconds
$webReady = Wait-HttpReady "Web" "http://localhost:3000" $WebTimeoutSeconds

if ($apiReady -and $webReady) {
    Invoke-RequiredNative "Application smoke test" { powershell -ExecutionPolicy Bypass -File .\scripts\smoke_app.ps1 } | Out-Null
} else {
    Write-Fail "Application smoke test" "skipped because API or web readiness failed"
}

Invoke-RequiredNative "Alembic revision" { docker compose exec -T api alembic current } | Out-Null
Invoke-RequiredNative "Pre-collection real-data status" { docker compose exec -T api python scripts/realdata_status.py } | Out-Null

foreach ($feed in @("futzip-movers", "futzip-new", "futzip-sbc")) {
    Invoke-RequiredNative "Required FUTZIP collection: $feed" { docker compose exec -T api python scripts/collect_once.py $feed } | Out-Null
}

Invoke-RequiredNative "Post-collection real-data status" { docker compose exec -T api python scripts/realdata_status.py } | Out-Null

if ($script:Failures.Count -gt 0) {
    Write-Host "" 
    Write-Host "Phase 2 runtime validation FAILED ($($script:Failures.Count) mandatory gate(s))." -ForegroundColor Red
    foreach ($failure in $script:Failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "" 
Write-Host "Phase 2 runtime validation PASSED. Open http://localhost:3000" -ForegroundColor Green
exit 0
