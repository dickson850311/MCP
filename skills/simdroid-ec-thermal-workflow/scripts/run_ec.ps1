param(
    [Parameter(Mandatory=$true)][string]$Script,
    [ValidateSet("auto", "ec", "system")][string]$Python = "auto",
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$Args
)
$root = $env:EC_INSTALL_ROOT
if (-not $root) { $root = "D:\Simdroid Electronic Cooling V2026.7.3" }

# 09/10/11 only need pymupdf/python-docx and do not import IBE.
if ($Python -eq "auto") {
    $leaf = [System.IO.Path]::GetFileName($Script)
    if ($leaf -match '^(09|10|11)_') { $Python = "system" } else { $Python = "ec" }
}
if ($Python -eq "system") {
    $exe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    if (-not $exe) { throw "system python.exe not found; install Python with pymupdf and python-docx" }
} else {
    $exe = Join-Path $root "bin\python.exe"
}
Set-Location (Join-Path $root "script")
& $exe $Script @Args
exit $LASTEXITCODE
