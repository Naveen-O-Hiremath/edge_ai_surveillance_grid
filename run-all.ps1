<#
.SYNOPSIS
  One command to ship Sentinel AI with Docker.
.EXAMPLE
  .\run-all.ps1 -Detach
  .\run-all.ps1 -Detach -OpenFirewall
#>
[CmdletBinding()]
param(
    [switch]$Detach,
    [switch]$NoBuild,
    [switch]$OpenFirewall,
    [switch]$SkipLanDetect
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Write-Status([string]$text) { Write-Host "[sentinel] $text" -ForegroundColor Cyan }

# Ensure .env exists
$envFile = Join-Path $root '.env'
$envExample = Join-Path $root '.env.example'
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Status "Created .env from .env.example"
}

# Ensure data dir for LAN hints
$dataDir = Join-Path $root 'data'
if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory -Path $dataDir | Out-Null }

# Auto-detect LAN IP for mobile camera QR codes
$jsonPath = Join-Path $dataDir 'host-lan.json'
if (-not $SkipLanDetect) {
    $lanScript = Join-Path $root 'scripts\get-lan-ip.ps1'
    if (Test-Path $lanScript) {
        Write-Status "Detecting LAN IP for mobile cameras..."
        & powershell -NoProfile -ExecutionPolicy Bypass -File $lanScript | Out-Null
    }
}

$publicBaseUrl = $env:PUBLIC_BASE_URL
if (-not $publicBaseUrl -and (Test-Path $jsonPath)) {
    try {
        $payload = Get-Content $jsonPath -Raw | ConvertFrom-Json
        if ($payload.url) { $publicBaseUrl = $payload.url }
        elseif ($payload.lan_ip) { $publicBaseUrl = "http://$($payload.lan_ip):3000" }
        elseif ($payload.candidates -and $payload.candidates.Count -gt 0) {
            $first = $payload.candidates[0]
            if ($first.url) { $publicBaseUrl = $first.url }
            elseif ($first.ip) { $publicBaseUrl = "http://$($first.ip):3000" }
        }
    } catch {
        Write-Status "Could not read host-lan.json — mobile QR may need manual IP."
    }
}
if ($publicBaseUrl) {
    $env:PUBLIC_BASE_URL = $publicBaseUrl
    Write-Status "PUBLIC_BASE_URL=$publicBaseUrl"
}

if ($OpenFirewall) {
    $fw = Join-Path $root 'scripts\open-firewall.ps1'
    if (Test-Path $fw) {
        Write-Status "Opening Windows firewall on port 3000..."
        & powershell -NoProfile -ExecutionPolicy Bypass -File $fw
    }
}

$compose = @('compose', 'up')
if (-not $NoBuild) { $compose += '--build' }
if ($Detach) { $compose += @('-d', '--wait') }

Write-Status "docker $($compose -join ' ')"
docker @compose
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Detach) {
    Write-Host ""
    Write-Host "Sentinel AI is running." -ForegroundColor Green
    Write-Host "  Dashboard:  http://localhost:3000"
    Write-Host "  Login:      admin@sentinel.ai / admin123"
    if ($publicBaseUrl) {
        Write-Host "  Mobile QR:  $publicBaseUrl/publish/..."
    } else {
        Write-Host "  Mobile:     run scripts\get-lan-ip.ps1 and set LAN IP in Configure"
    }
    Write-Host ""
}
