$port = 8765
$proc = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($proc) {
    Stop-Process -Id $proc.OwningProcess -Force
    Write-Output "Flower Cutter stopped."
} else {
    Write-Output "Flower Cutter is not running."
}
