[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$PackageRoot,

    [int]$SettleFrames = 120,

    [int]$SampleFrames = 300,

    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'

$root = [IO.Path]::GetFullPath($PackageRoot)
$game = Join-Path $root 'LineBossCarFactory\Binaries\Win64\LineBossCarFactory.exe'
if (-not (Test-Path -LiteralPath $game)) {
    throw "Packaged game executable was not found: $game"
}
if ($SettleFrames -lt 1) { throw 'SettleFrames must be at least 1.' }
if ($SampleFrames -lt 30) { throw 'SampleFrames must be at least 30.' }
if ($TimeoutSeconds -lt 30) { throw 'TimeoutSeconds must be at least 30.' }

$runRoot = Join-Path $root 'Validation\OneFactoryPerformance'
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
$stamp = Get-Date -Format 'yyyyMMddTHHmmssZ'
$log = Join-Path $runRoot "performance_lod_$stamp.log"
$receipt = Join-Path $runRoot "performance_lod_$stamp.json"
$fallbackLog = Join-Path (Split-Path -Parent $game) 'LineBossCarFactory.log'

# ExecCmds is comma-delimited.  The capture actor itself quits only after it
# has sampled settled rendered frames, so this cannot leave a high-load factory
# process running after the evidence has been collected.
$commands = @(
    'LB.OneFactory.BuildWholeFactory',
    'LB.OneFactory.StartProduction 1',
    'LB.OneFactory.View All',
    "LB.OneFactory.PerfCapture $SettleFrames $SampleFrames WholeFactory 1"
) -join ','

$arguments = @(
    '/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001',
    '-unattended', '-nosound', '-nop4', '-NoSplash', '-stdout',
    '-FullStdOutLogOutput', '-windowed', '-ResX=1920', '-ResY=1080',
    "-abslog=$log",
    "-ExecCmds=`"$commands`""
)

$startedUtc = (Get-Date).ToUniversalTime()
$process = Start-Process -FilePath $game -WorkingDirectory $root `
    -ArgumentList $arguments -PassThru
if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    Stop-Process -Id $process.Id -ErrorAction SilentlyContinue
    throw "Packaged performance/LOD validation timed out after $TimeoutSeconds seconds."
}
if ($process.ExitCode -ne 0) {
    throw "Packaged performance/LOD validation exited $($process.ExitCode). See $log"
}
if (-not (Test-Path -LiteralPath $log)) {
    # Bootstrap-owned packaged launches can ignore -abslog and write beside
    # the executable.  This is accepted only when the fallback is current.
    if ((Test-Path -LiteralPath $fallbackLog) -and
        ((Get-Item -LiteralPath $fallbackLog).LastWriteTimeUtc -ge $startedUtc)) {
        $log = $fallbackLog
    } else {
        throw "Packaged performance/LOD validation exited without producing a current log: $log or $fallbackLog"
    }
}

$text = Get-Content -LiteralPath $log -Raw
$match = [regex]::Match($text,
    'LINE_BOSS_DEV_PERF_CAPTURE_PASS label=(?<label>\S+) samples=(?<samples>\d+) avg_ms=(?<avg>[\d.]+) p50_ms=(?<p50>[\d.]+) p95_ms=(?<p95>[\d.]+) viewport=(?<width>\d+)x(?<height>\d+) static_mesh_components=(?<components>\d+) meshes_with_lods=(?<multiLod>\d+) total_lods=(?<lods>\d+) forced_lod_components=(?<forced>\d+)')
if (-not $match.Success) {
    throw "Packaged performance/LOD validation did not emit a completed capture. See $log"
}
if ([int]$match.Groups['samples'].Value -lt $SampleFrames) {
    throw "Capture returned fewer samples than requested. See $log"
}
# The viewport reports logical pixels under Windows DPI scaling; 1024x576 is
# the minimum meaningful 16:9 management view, while the launcher still asks
# the OS for 1920x1080 physical pixels.
if ([int]$match.Groups['width'].Value -lt 1024 -or
    [int]$match.Groups['height'].Value -lt 576) {
    throw "Capture did not run at a meaningful viewport size. See $log"
}
if ([int]$match.Groups['components'].Value -lt 1 -or
    [int]$match.Groups['lods'].Value -lt 1) {
    throw "Capture found no live static-mesh/LOD population. See $log"
}

$result = [ordered]@{
    status = 'PASS'
    package_root = $root
    executable = $game
    utc = (Get-Date).ToUniversalTime().ToString('o')
    settle_frames = $SettleFrames
    sample_frames = $SampleFrames
    exit_code = $process.ExitCode
    label = $match.Groups['label'].Value
    avg_ms = [double]$match.Groups['avg'].Value
    p50_ms = [double]$match.Groups['p50'].Value
    p95_ms = [double]$match.Groups['p95'].Value
    viewport = "$($match.Groups['width'].Value)x$($match.Groups['height'].Value)"
    static_mesh_components = [int]$match.Groups['components'].Value
    meshes_with_multiple_lods = [int]$match.Groups['multiLod'].Value
    total_available_lods = [int]$match.Groups['lods'].Value
    forced_lod_components = [int]$match.Groups['forced'].Value
    log = $log
    log_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $log).Hash
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receipt -Encoding utf8
$result | ConvertTo-Json -Depth 4
