param(
    [string]$Root = "D:\Simdroid Electronic Cooling V2026.7.3",
    [string]$SkillDir = "$PSScriptRoot\..",
    [string]$Config = "$PSScriptRoot\..\assets\project_config.json"
)

$ErrorActionPreference = "Stop"
$env:EC_INSTALL_ROOT = $Root
$env:EC_CONFIG = $Config

$steps = @(
    "01_import_geometry.py",
    "02_export_bbox.py",
    "03_build_model.py",
    "04_thin_cleanup_mesh.py",
    "05_v5_radiation_frozenflow.py",
    "06_solve.py",
    "07_results_key_parts.py",
    "08_stats_all.py",
    "09_charts.py",
    "10_maps.py",
    "11_report.py"
)

for ($i = 0; $i -lt $steps.Count; $i++) {
    $n = $i + 1
    $s = $steps[$i]
    Write-Host ""
    Write-Host ("===== [{0}/11] {1} =====" -f $n, $s)
    & powershell -ExecutionPolicy Bypass -File (Join-Path $SkillDir "scripts\run_ec.ps1") -Script (Join-Path $SkillDir "scripts\$s")
    if ($LASTEXITCODE -ne 0) {
        throw "step $s failed, exit=$LASTEXITCODE"
    }
}
Write-Host "ALL DONE"
