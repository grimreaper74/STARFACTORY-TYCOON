# TRELLIS one-shot generation lane, v002 (2026-08-31).
# Supersedes trellis_generate_v001.ps1, which dies the moment it runs with
# a redirected stderr (any unattended host): under Windows PowerShell 5.1,
# `2>&1` on a native command wraps each stderr line in a NativeCommandError
# record, and with $ErrorActionPreference='Stop' the CLI's FIRST progress
# message ("[trellis] generating model with seed 42") became a terminating
# error at the invocation line. Interactive runs never see it - which is
# exactly how v001 validated clean and then failed its first unattended
# call from the agent's generate_3d_asset tool. v002 scopes the preference
# to 'Continue' around the native call and stringifies the records; the
# REAL failure gates are unchanged ($LASTEXITCODE + output existence).
#
# Validated CLI timings on this machine: 139,488-tri textured GLB in
# 52.8 s at -Res 512; ~290 s at 1024 (final quality).
#
# Output: <name>.glb + <name>.manifest.json (sha256 of input and output,
# parameters, timings) under SourceAssets\Spacecraft\TrellisGenerated_v001\<name>\.
#
# Usage:
#   .\Scripts\trellis_generate_v002.ps1 -Image ref.png -Name engine_station_body
#   .\Scripts\trellis_generate_v002.ps1 -Image ref.png -Name x -Res 1024 -Seed 7

param(
    [Parameter(Mandatory = $true)]
    [string]$Image,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_]{1,64}$')]
    [string]$Name,

    [ValidateSet(512, 1024)]
    [int]$Res = 512,

    [int]$Seed = 42,

    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'

$cli = Join-Path $env:LOCALAPPDATA 'trellis-studio\runtime\trellis-cli.exe'
$models = Join-Path $env:LOCALAPPDATA 'trellis-studio\models\q8'
if (-not (Test-Path -LiteralPath $cli)) { throw "trellis-cli.exe not found at $cli" }
if (-not (Test-Path -LiteralPath $models)) { throw "Q8 models not found at $models" }
if (-not (Test-Path -LiteralPath $Image)) { throw "Input image not found: $Image" }

$projectRoot = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $projectRoot "SourceAssets\Spacecraft\TrellisGenerated_v001\$Name"
$outGlb = Join-Path $outDir "$Name.glb"
$manifest = Join-Path $outDir "$Name.manifest.json"

if ((Test-Path -LiteralPath $outGlb) -and -not $Overwrite) {
    throw "Output already exists: $outGlb (pass -Overwrite to replace). The lane refuses silent replacement."
}
New-Item -ItemType Directory -Force $outDir | Out-Null

$inputHash = (Get-FileHash -LiteralPath $Image -Algorithm SHA256).Hash.ToLower()
$started = [DateTime]::UtcNow
Write-Host "TRELLIS: $Image -> $outGlb (res $Res, seed $Seed)..."

# Native call under 'Continue': stderr records must not terminate the lane
# (see header). "$_" stringifies both output lines and ErrorRecords.
$ErrorActionPreference = 'Continue'
& $cli -i $Image -o $outGlb -m $models --res $Res --seed $Seed --require-gpu 2>&1 | ForEach-Object {
    # Keep only milestone lines in the harness log; the full spew stays
    # available by running the CLI by hand.
    if ("$_" -match 'done in|ERROR|error|FAILED|decimate|textured GLB') { Write-Host "  $_" }
}
$exit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
$seconds = ([DateTime]::UtcNow - $started).TotalSeconds

if ($exit -ne 0 -or -not (Test-Path -LiteralPath $outGlb)) {
    throw "TRELLIS generation FAILED (exit $exit) after $([int]$seconds)s - no output claimed."
}

$outHash = (Get-FileHash -LiteralPath $outGlb -Algorithm SHA256).Hash.ToLower()
$outSize = (Get-Item -LiteralPath $outGlb).Length

@{
    name = $Name
    inputImage = (Resolve-Path -LiteralPath $Image).Path
    inputSha256 = $inputHash
    outputGlb = $outGlb
    outputSha256 = $outHash
    outputBytes = $outSize
    res = $Res
    seed = $Seed
    generator = 'trellis-cli q8'
    generatedUtc = $started.ToString('o')
    seconds = [Math]::Round($seconds, 1)
} | ConvertTo-Json | Out-File -LiteralPath $manifest -Encoding utf8

Write-Host "OK: $outGlb ($([Math]::Round($outSize/1MB,1)) MB, $([int]$seconds)s). Manifest: $manifest"
