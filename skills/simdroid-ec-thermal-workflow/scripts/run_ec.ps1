param(
    [Parameter(Mandatory = $true)]
    [string]$Script,
    [string]$Root = "D:\Simdroid Electronic Cooling V2026.7.3",
    [ValidateSet("auto", "ec", "system")]
    [string]$Python = "auto"
)

$ErrorActionPreference = "Stop"
$scriptPath = (Resolve-Path $Script).Path
$scriptName = Split-Path $scriptPath -Leaf
$scriptDir = Split-Path $scriptPath -Parent

# 09/10/11 只做绘图/Word，不 import IBE，用系统 Python（需 pymupdf、python-docx）
if ($Python -eq "auto") {
    if ($scriptName -match '^(09|10|11)_') {
        $Python = "system"
    } else {
        $Python = "ec"
    }
}

if ($Python -eq "ec") {
    $py = Join-Path $Root "bin\python.exe"
    $cwd = Join-Path $Root "script"
} else {
    $py = (Get-Command python -ErrorAction Stop).Source
    $cwd = $scriptDir
}

if (-not (Test-Path $py)) {
    throw "Python not found: $py"
}
if (-not (Test-Path $cwd)) {
    throw "Work dir not found: $cwd"
}

Write-Host "python=$py"
Write-Host "cwd=$cwd"
Write-Host "script=$scriptPath"

Push-Location $cwd
try {
    & $py $scriptPath
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
