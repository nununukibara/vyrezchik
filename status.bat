$port = 8765
$proc = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($proc) {
    $pid = $proc.OwningProcess
    $name = (Get-Process -Id $pid -ErrorAction SilentlyContinue).ProcessName
    Write-Output "Flower Cutter is RUNNING (PID: $pid, Port: $port)"
} else {
    Write-Output "Flower Cutter is STOPPED"
}
