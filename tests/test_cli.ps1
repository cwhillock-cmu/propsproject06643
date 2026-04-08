$ErrorActionPreference = "Stop"
$passed = 0
$failed = 0
$cli = "python -m idaes_props.cli"

function Test-Command {
    param(
        [string]$Name,
        [string]$Command,
        [int]$ExpectedExit = 0,
        [string[]]$OutputContains = @(),
        [int]$MinLines = 0
    )

    Write-Host -NoNewline "  $Name ... "

    $tempOut = [System.IO.Path]::GetTempFileName()
    $tempErr = [System.IO.Path]::GetTempFileName()

    $process = Start-Process -FilePath "python" `
        -ArgumentList ($Command -replace "^python ", "") `
        -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput $tempOut `
        -RedirectStandardError $tempErr

    $actualExit = $process.ExitCode
    $stdout = Get-Content $tempOut -Raw -ErrorAction SilentlyContinue
    $stderr = Get-Content $tempErr -Raw -ErrorAction SilentlyContinue
    Remove-Item $tempOut, $tempErr -ErrorAction SilentlyContinue

    if ($null -eq $stdout) { $stdout = "" }
    if ($null -eq $stderr) { $stderr = "" }

    $reasons = @()

    if ($actualExit -ne $ExpectedExit) {
        $reasons += "expected exit code $ExpectedExit but got $actualExit"
    }

    foreach ($str in $OutputContains) {
        if (-not $stdout.Contains($str)) {
            $reasons += "stdout missing '$str'"
        }
    }

    if ($MinLines -gt 0) {
        $lineCount = ($stdout.Trim() -split "`n").Count
        if ($lineCount -lt $MinLines) {
            $reasons += "expected at least $MinLines lines, got $lineCount"
        }
    }

    if ($reasons.Count -eq 0) {
        Write-Host "PASSED" -ForegroundColor Green
        $script:passed++
    }
    else {
        Write-Host "FAILED" -ForegroundColor Red
        foreach ($r in $reasons) {
            Write-Host "    -> $r" -ForegroundColor Yellow
        }
        $preview = ($stdout.Trim() -split "`n" | Select-Object -First 3) -join "`n"
        if ($preview) { Write-Host "    stdout: $preview" -ForegroundColor DarkGray }
        if ($stderr.Trim()) { Write-Host "    stderr: $($stderr.Trim())" -ForegroundColor DarkGray }
        $script:failed++
    }
}

Write-Host ""
Write-Host "=== CLI Test Suite ===" -ForegroundColor Cyan
Write-Host ""

# ---- list-components ----
Write-Host "[list-components]" -ForegroundColor White
Test-Command -Name "returns known components" `
    -Command "$cli list-components" `
    -OutputContains @("co2", "h2o") `
    -MinLines 5

# ---- list-properties ----
Write-Host "[list-properties]" -ForegroundColor White
Test-Command -Name "returns property names" `
    -Command "$cli list-properties" `
    -OutputContains @("enth_mol", "pressure") `
    -MinLines 10

# ---- single ----
Write-Host "[single]" -ForegroundColor White
Test-Command -Name "basic single property" `
    -Command "$cli single co2 -T 298.15 -P 101325 enth_mol" `
    -OutputContains @("enth_mol =")

Test-Command -Name "single with Celsius and bar" `
    -Command "$cli single co2 -T 25 -P 1 --temperature-unit C --pressure-unit bar enth_mol" `
    -OutputContains @("enth_mol =")

Test-Command -Name "single with mass basis" `
    -Command "$cli single co2 -T 298.15 -P 101325 enth_mass --basis mass" `
    -OutputContains @("enth_mass =")

Test-Command -Name "single rejects negative temperature" `
    -Command "$cli single co2 -T -5 -P 101325 enth_mol" `
    -ExpectedExit 1

Test-Command -Name "single rejects invalid property" `
    -Command "$cli single co2 -T 298.15 -P 101325 fake_prop" `
    -ExpectedExit 1

Test-Command -Name "single rejects invalid component" `
    -Command "$cli single unobtanium -T 298.15 -P 101325 enth_mol" `
    -ExpectedExit 1

# ---- multi ----
Write-Host "[multi]" -ForegroundColor White
Test-Command -Name "multi with specific properties" `
    -Command "$cli multi co2 -T 298.15 -P 101325 --properties temperature pressure enth_mol" `
    -OutputContains @("phase_id", "temperature", "enth_mol")

Test-Command -Name "multi all properties" `
    -Command "$cli multi co2 -T 298.15 -P 101325" `
    -OutputContains @("phase_id", "mw") `
    -MinLines 2

Test-Command -Name "multi with mass basis" `
    -Command "$cli multi co2 -T 298.15 -P 101325 --properties enth_mass --basis mass" `
    -OutputContains @("enth_mass")

# ---- range ----
Write-Host "[range]" -ForegroundColor White
Test-Command -Name "isobaric range with start:stop:step" `
    -Command "$cli range co2 -T 280:320:10 -P 101325 --properties temperature pressure enth_mol" `
    -OutputContains @("phase_id", "enth_mol") `
    -MinLines 5

Test-Command -Name "isothermal range with comma list" `
    -Command "$cli range co2 -T 298.15 -P 50000,101325,200000 --properties temperature pressure dens_mol" `
    -OutputContains @("dens_mol") `
    -MinLines 3

Test-Command -Name "range all properties" `
    -Command "$cli range co2 -T 290,300 -P 101325" `
    -OutputContains @("phase_id", "mw") `
    -MinLines 2

Test-Command -Name "range with unit options" `
    -Command "$cli range co2 -T 20,25,30 -P 1 --temperature-unit C --pressure-unit bar --properties temperature pressure enth_mol" `
    -OutputContains @("enth_mol") `
    -MinLines 3

Test-Command -Name "range with mass basis" `
    -Command "$cli range co2 -T 298.15 -P 50000,101325 --properties dens_mass --basis mass" `
    -OutputContains @("dens_mass") `
    -MinLines 2

Test-Command -Name "range rejects negative pressure" `
    -Command "$cli range co2 -T 298.15 -P 101325,-100 --properties enth_mol" `
    -ExpectedExit 1

# ---- summary ----
Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failed -gt 0) { exit 1 }
