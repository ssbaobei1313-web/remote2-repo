<#
Create or remove a python3 forwarder inside a virtualenv Scripts folder,
and print verification results.

Usage:
  .\create_python3.ps1                 # create .cmd forwarder
  .\create_python3.ps1 -Action create  # explicit create
  .\create_python3.ps1 -Action remove  # remove forwarder
  .\create_python3.ps1 -Action create -UseExe $true  # create python3.exe copy
#>

param(
  [ValidateSet("create","remove")]
  [string]$Action = "create",

  [bool]$UseExe = $false,

  [string]$VenvPath = ".\.venv"
)

# Resolve full paths
$venvFull = Resolve-Path -Path $VenvPath -ErrorAction SilentlyContinue
if (-not $venvFull) {
  Write-Error "Virtual environment path '$VenvPath' not found. Please run from project root or set -VenvPath."
  exit 1
}
$venvFull = $venvFull.Path
$scriptsDir = Join-Path $venvFull "Scripts"
if (-not (Test-Path $scriptsDir)) {
  Write-Error "Scripts directory not found at '$scriptsDir'. Is this a Windows venv?"
  exit 1
}

$cmdPath = Join-Path $scriptsDir "python3.cmd"
$exePath = Join-Path $scriptsDir "python3.exe"
$pythonExe = Join-Path $scriptsDir "python.exe"

if ($Action -eq "create") {
  if (-not (Test-Path $pythonExe)) {
    Write-Error "python.exe not found in venv Scripts: $pythonExe"
    exit 1
  }

  if ($UseExe) {
    Copy-Item -Path $pythonExe -Destination $exePath -Force
    Write-Output "Created: $exePath"
  } else {
    $content = "@echo off`n`"%~dp0python.exe`" %*"
    $content | Set-Content -Path $cmdPath -Encoding ascii
    Write-Output "Created: $cmdPath"
  }

  Write-Output ""
  Write-Output "Verification:"
  try { & $pythonExe --version 2>$null | ForEach-Object { Write-Output "venv python: $_" } } catch {}
  try { python3 --version 2>$null | ForEach-Object { Write-Output "python3: $_" } } catch {}
  Get-Command python3 -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Output ("Get-Command result: {0} -> {1}" -f $_.Name, $_.Source)
  }
  where.exe python3 2>$null | ForEach-Object { Write-Output ("where: {0}" -f $_) }
  exit 0
}

if ($Action -eq "remove") {
  $removed = $false
  if (Test-Path $cmdPath) {
    Remove-Item $cmdPath -Force -ErrorAction SilentlyContinue
    Write-Output "Removed: $cmdPath"
    $removed = $true
  }
  if (Test-Path $exePath) {
    Remove-Item $exePath -Force -ErrorAction SilentlyContinue
    Write-Output "Removed: $exePath"
    $removed = $true
  }
  if (-not $removed) {
    Write-Output "Nothing to remove in $scriptsDir"
  }

  Write-Output ""
  Write-Output "Verification after removal:"
  Get-Command python3 -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Output ("Get-Command result: {0} -> {1}" -f $_.Name, $_.Source)
  }
  where.exe python3 2>$null | ForEach-Object { Write-Output ("where: {0}" -f $_) }
  exit 0
}
