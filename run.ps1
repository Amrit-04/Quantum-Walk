# QuMa: Quantum Maze PowerShell Launcher
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   Starting QuMa: Quantum Maze (Qiskit Simulation)     " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$pythonExe = if (Test-Path "$scriptDir\.venv\Scripts\python.exe") {
    "$scriptDir\.venv\Scripts\python.exe"
} else {
    "python"
}

& $pythonExe "$scriptDir\main.py"
