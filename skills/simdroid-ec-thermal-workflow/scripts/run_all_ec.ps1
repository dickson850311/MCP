# 伏图电子散热（Simdroid Electronic Cooling）QR-V23 全流程一键执行。
# 注意：01 会新建并覆盖 QR-V23_EC.simec；只重跑部分步骤时请单独调用 run_ec.ps1。
# 用法：powershell -ExecutionPolicy Bypass -File .\run_all_ec.ps1
#       powershell -ExecutionPolicy Bypass -File .\run_all_ec.ps1 -From 6

param([int]$From = 1, [string]$Config = "")

$ErrorActionPreference = "Stop"
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($Config) {
    $env:EC_CONFIG = (Resolve-Path -LiteralPath $Config).Path
}
$Run = Join-Path $PSScriptRoot "run_ec.ps1"

$steps = @(
    @{ n = 1;  f = "01_import_geometry.py" },
    @{ n = 2;  f = "02_export_bbox.py" },
    @{ n = 3;  f = "03_build_model.py" },
    @{ n = 4;  f = "04_thin_cleanup_mesh.py" },
    @{ n = 5;  f = "05_v5_radiation_frozenflow.py" },
    @{ n = 6;  f = "06_solve.py" },
    @{ n = 7;  f = "07_results_key_parts.py" },
    @{ n = 8;  f = "08_stats_all.py" },
    @{ n = 9;  f = "09_charts.py" },
    @{ n = 10; f = "10_maps.py" },
    @{ n = 11; f = "11_report.py" }
)

foreach ($s in $steps) {
    if ($s.n -lt $From) { continue }
    Write-Host ("=" * 60)
    Write-Host ("STEP {0}: {1}" -f $s.n, $s.f)
    & $Run -Script (Join-Path $PSScriptRoot $s.f)
    if ($LASTEXITCODE -ne 0) {
        throw ("step {0} failed, exit code {1}" -f $s.n, $LASTEXITCODE)
    }
}
Write-Host "EC pipeline finished."
