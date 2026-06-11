# Detect real LAN IP for mobile camera QR (excludes Hyper-V / WSL virtual adapters).
# Run: .\scripts\get-lan-ip.ps1
# Then restart backend or refresh Configure page.

$outDir = Join-Path $PSScriptRoot "..\data"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$adapters = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {
    $_.IPAddress -notmatch '^(127\.|169\.254\.)' -and
    $_.InterfaceAlias -notmatch 'vEthernet|WSL|Hyper-V|Default Switch|Loopback|Bluetooth|Docker'
} | Sort-Object @{
    Expression = {
        if ($_.InterfaceAlias -match 'Wi-Fi|WiFi|Wireless') { 0 }
        elseif ($_.InterfaceAlias -match 'Ethernet') { 1 }
        else { 2 }
    }
})

$best = $adapters | Select-Object -First 1
$warning = $null
if (-not $best) {
    $warning = "No active Wi-Fi or Ethernet found. Connect your PC to the same Wi-Fi as your phone, then run this script again."
}

$candidates = @($adapters | ForEach-Object {
    @{ ip = $_.IPAddress; interface = $_.InterfaceAlias; url = "http://$($_.IPAddress):3000" }
})

$payload = [ordered]@{
    lan_ip     = if ($best) { $best.IPAddress } else { $null }
    interface  = if ($best) { $best.InterfaceAlias } else { $null }
    port       = 3000
    updated_at = (Get-Date).ToUniversalTime().ToString("o")
    warning    = $warning
    candidates = $candidates
}

$path = Join-Path $outDir "host-lan.json"
$payload | ConvertTo-Json -Depth 4 | Set-Content $path -Encoding UTF8

if ($best) {
    Write-Host "LAN IP: $($best.IPAddress) ($($best.InterfaceAlias))"
    Write-Host "Mobile URL: http://$($best.IPAddress):3000"
} else {
    Write-Host $warning -ForegroundColor Yellow
}
Write-Host "Saved to $path"
