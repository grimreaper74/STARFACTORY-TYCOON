[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$PackageRoot,

    [int]$Iterations = 3000,

    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'

$root = [IO.Path]::GetFullPath($PackageRoot)
$game = Join-Path $root 'LineBossCarFactory\Binaries\Win64\LineBossCarFactory.exe'
if (-not (Test-Path -LiteralPath $game)) {
    throw "Packaged game executable was not found: $game"
}
if ($Iterations -lt 1) { throw 'Iterations must be at least 1.' }
if ($TimeoutSeconds -lt 30) { throw 'TimeoutSeconds must be at least 30.' }

$runRoot = Join-Path $root 'Validation\OneFactoryFullProduction'
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
$stamp = Get-Date -Format 'yyyyMMddTHHmmssZ'
$log = Join-Path $runRoot "full_production_$stamp.log"
$receipt = Join-Path $runRoot "full_production_$stamp.json"

# ExecCmds is comma-delimited in UE.  Keeping the entire value quoted avoids
# the launcher treating a following command as a map URL.
$commands = @(
    'LB.OneFactory.BuildWholeFactory',
    'LB.OneFactory.StartProduction 1',
    "LB.OneFactory.Run $Iterations 1 1",
    'LB.OneFactory.Status',
    'quit'
) -join ','

$arguments = @(
    '/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001',
    '-unattended', '-nosound', '-nop4', '-NoSplash', '-stdout',
    '-FullStdOutLogOutput',
    "-abslog=$log",
    "-ExecCmds=`"$commands`""
)

$process = Start-Process -FilePath $game -WorkingDirectory $root -ArgumentList $arguments -PassThru
if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    Stop-Process -Id $process.Id -ErrorAction SilentlyContinue
    throw "Packaged full-production proof timed out after $TimeoutSeconds seconds."
}
if ($process.ExitCode -ne 0) {
    throw "Packaged full-production proof exited $($process.ExitCode). See $log"
}
if (-not (Test-Path -LiteralPath $log)) {
    throw "Packaged run exited without producing a log: $log"
}

$text = Get-Content -LiteralPath $log -Raw
$required = @(
    'LINE_BOSS_DEV_BUILD_WHOLE_FACTORY ok=1',
    'LINE_BOSS_DEV_START_PRODUCTION ok=1 started 1 vehicle order(s)',
    "LINE_BOSS_DEV_RUN ok=1 ran $Iterations x 1.0s; units=1 completed=1 dispatched=1",
    'route: 57 stations',
    'units: 1'
)
$missing = @($required | Where-Object { -not $text.Contains($_) })
if ($missing.Count -gt 0) {
    throw "Packaged full-production proof did not establish its contract: $($missing -join '; '). See $log"
}
if ($text -match 'LINE_BOSS_DEV_(BUILD_WHOLE_FACTORY|START_PRODUCTION|RUN) ok=0') {
    throw "Packaged full-production proof logged a failed production command. See $log"
}

$result = [ordered]@{
    status = 'PASS'
    package_root = $root
    executable = $game
    utc = (Get-Date).ToUniversalTime().ToString('o')
    iterations = $Iterations
    exit_code = $process.ExitCode
    log = $log
    log_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $log).Hash
    required_markers = $required
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receipt -Encoding utf8
$result | ConvertTo-Json -Depth 4
