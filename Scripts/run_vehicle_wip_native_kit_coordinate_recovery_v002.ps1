[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('VALIDATE_PRESERVED_VEHICLE_WIP_NATIVE_KIT_COORDINATE_RECOVERY_V002_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$Python = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Preparer = Join-Path $Root 'Scripts\prepare_vehicle_wip_native_kit_coordinate_recovery_v002.py'
$Validator = Join-Path $Root 'Scripts\validate_vehicle_wip_native_kit_coordinate_recovery_v002.py'
$Contract = Join-Path $Root 'Scripts\vehicle_wip_native_kit_coordinate_recovery_v002_contract.json'
$Sidecar = Join-Path $Root 'Scripts\vehicle_wip_native_kit_coordinate_recovery_v002_contract.sha256'
$Audit = Join-Path $Root 'Saved\Audits\Vehicles\Cairnwell2040\VehicleWIPNativeKit_v001\CoordinateRecovery_v002'
$Pass = 'PASS__VEHICLE_WIP_NATIVE_KIT_V001_COORDINATE_RECOVERY_V002__READ_ONLY_16_ASSET_48_LOD_VALIDATION'

function Hash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant() }
function Assert-NoEditor {
    $names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT')
    $live = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $names -contains $_.ProcessName })
    if ($live.Count) { throw "Unreal/build process active: $(($live | ForEach-Object { $_.ProcessName + ':' + $_.Id }) -join ', ')" }
}

Assert-NoEditor
if (-not (Test-Path -LiteralPath $Contract -PathType Leaf) -or -not (Test-Path -LiteralPath $Sidecar -PathType Leaf)) { throw 'Frozen coordinate recovery pair missing' }
if ((Get-Content -Raw -LiteralPath $Sidecar).Trim().Split()[0].ToUpperInvariant() -cne (Hash $Contract)) { throw 'Coordinate recovery sidecar mismatch' }
$verify = (& $Python -B $Preparer --verify 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0 -or $verify -notmatch 'PASS__VEHICLE_WIP_NATIVE_KIT_COORDINATE_RECOVERY_V002_REVERIFIED') { throw "Offline recovery verification failed: $verify" }
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
$run = Join-Path $Audit $stamp
New-Item -ItemType Directory -Path $run | Out-Null
$old = [Environment]::GetEnvironmentVariable('LINEBOSS_VEHICLE_WIP_NATIVE_COORDINATE_RUN', 'Process')
try {
    [Environment]::SetEnvironmentVariable('LINEBOSS_VEHICLE_WIP_NATIVE_COORDINATE_RUN', $run, 'Process')
    $args = @(('"{0}"' -f $Project), '-Unattended','-NoSplash','-NoSound','-NullRHI','-NoCompile','-NoCompileEditor','-NoAssetRegistryCacheWrite', ('-ExecutePythonScript="{0}"' -f $Validator), ('-abslog="{0}"' -f (Join-Path $run 'unreal_validation.log')))
    $proc = Start-Process -FilePath $Editor -ArgumentList $args -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $run 'stdout.log') -RedirectStandardError (Join-Path $run 'stderr.log') -PassThru
    $proc.WaitForExit(1800000) | Out-Null; $proc.Refresh()
    if ($proc.ExitCode -ne 0) { throw "Read-only coordinate validator exit code $($proc.ExitCode)" }
    $receipt = Get-ChildItem $Audit -Recurse -File -Filter 'fresh_read_only_validation_receipt_v002.json' | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if ($null -eq $receipt) { throw 'Read-only coordinate validation receipt missing' }
    $payload = Get-Content -Raw -LiteralPath $receipt.FullName | ConvertFrom-Json
    if ([string]$payload.status -cne $Pass -or [int]$payload.asset_count -ne 16 -or [int]$payload.authored_lod_count -ne 48) { throw 'Read-only coordinate validation receipt drift' }
    Write-Output "LINE_BOSS_VEHICLE_WIP_NATIVE_COORDINATE_RECOVERY_V002_PASS=$($receipt.FullName)"
} finally {
    [Environment]::SetEnvironmentVariable('LINEBOSS_VEHICLE_WIP_NATIVE_COORDINATE_RUN', $old, 'Process')
    Assert-NoEditor
}
