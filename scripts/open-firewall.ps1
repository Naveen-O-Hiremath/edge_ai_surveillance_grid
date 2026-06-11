# Run as Administrator — opens Docker port for Sentinel mobile camera access
# Only port 3000 is required (nginx proxies /api to backend)
$ports = @(3000)
foreach ($port in $ports) {
    $name = "Sentinel AI Port $port"
    $existing = Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue
    if (-not $existing) {
        New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow -Protocol TCP -LocalPort $port | Out-Null
        Write-Host "Opened port $port"
    } else {
        Write-Host "Port $port already open"
    }
}
Write-Host "Done. Run scripts\get-lan-ip.ps1 to find your Wi-Fi IP, then scan QR on phone (same Wi-Fi)."
