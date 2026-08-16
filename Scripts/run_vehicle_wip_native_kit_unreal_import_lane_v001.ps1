[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('IMPORT_FROZEN_VEHICLE_WIP_NATIVE_KIT_V001_BASELINE_V001_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$Python = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Contract = Join-Path $Root 'Scripts\vehicle_wip_native_kit_unreal_import_contract_v001.json'
$Baseline = Join-Path $Root 'Scripts\vehicle_wip_native_kit_unreal_import_baseline_v001.json'
$BaselineSidecar = Join-Path $Root 'Scripts\vehicle_wip_native_kit_unreal_import_baseline_v001.sha256'
$Freezer = Join-Path $Root 'Scripts\prepare_vehicle_wip_native_kit_unreal_import_baseline_v001.py'
$Common = Join-Path $Root 'Scripts\vehicle_wip_native_kit_unreal_runtime_v001.py'
$Importer = Join-Path $Root 'Scripts\import_vehicle_wip_native_kit_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_vehicle_wip_native_kit_v001.py'
$Destination = Join-Path $Root 'Content\LineBoss\Native\Vehicles\Cairnwell2040\VehicleWIPNativeKit_v001'
$AuditRoot = Join-Path $Root 'Saved\Audits\Vehicles\Cairnwell2040\VehicleWIPNativeKit_v001\UnrealImportLane_v001'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_v001.json'
$ImportReceipt = Join-Path $RunRoot 'import_receipt_v001.json'
$ImportFailure = Join-Path $RunRoot 'import_failure_v001.json'
$ValidationReceipt = Join-Path $RunRoot 'fresh_load_validation_receipt_v001.json'
$ValidationFailure = Join-Path $RunRoot 'fresh_load_validation_failure_v001.json'
$ContractSha256 = '87D9FD32964CC0AD0F4AA52CC6F27A0E23BFDA23A18B2F714E6E2807CCA9684D'
$ImportStatus = 'PASS__HASH_GUARDED_FRESH_IMPORT__16_NATIVE_VEHICLE_ROLES__48_AUTHORED_LODS__V001'
$ValidationStatus = 'PASS__INDEPENDENT_FRESH_PROCESS_RELOAD__16_NATIVE_VEHICLE_ROLES__48_AUTHORED_LODS__V001'
$RunEnvironment = 'LINEBOSS_VEHICLE_WIP_NATIVE_V001_RUN_ROOT'
$AckEnvironment = 'LINEBOSS_VEHICLE_WIP_NATIVE_V001_ACK'
$ResultNames = @('import_receipt_v001.json','import_failure_v001.json',
    'fresh_load_validation_receipt_v001.json','fresh_load_validation_failure_v001.json','lane_summary_v001.json')

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required file missing: $Path" }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Assert-NoProcesses {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -gt 0) {
        throw "Refusing isolated import while Unreal/build processes are active: $(($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', ')"
    }
}

function Assert-NoPriorResults {
    if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { return }
    $Found = @(Get-ChildItem -LiteralPath $AuditRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $ResultNames -contains $_.Name })
    if ($Found.Count -gt 0) { throw "One-shot lane refuses every pre-existing v001 result: $($Found.FullName -join '; ')" }
}

function Invoke-GuardedProcess([string]$Executable,[string[]]$Arguments,[string]$Stdout,[string]$Stderr,[int]$TimeoutSeconds,[string]$Label) {
    $Process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $Root `
        -WindowStyle Hidden -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru
    $null = $Process.Handle
    $Exited = $Process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $Exited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw "$Label timed out after $TimeoutSeconds seconds"
    }
    $Process.WaitForExit()
    $Process.Refresh()
    $ExitCode = $Process.ExitCode
    if ($null -eq $ExitCode) { throw "$Label lost ExitCode under Windows PowerShell" }
    return [ordered]@{ process_id = $Process.Id; exit_code = [int]$ExitCode }
}

function Read-Receipt([string]$Path,[string]$ExpectedStatus,[string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "$Label receipt missing: $Path" }
    $Payload = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ([string]$Payload.status -cne $ExpectedStatus) { throw "$Label receipt status drift: $($Payload.status)" }
    return $Payload
}

if ((Resolve-Path -LiteralPath $Root).Path -cne $Root) { throw 'Exact project-root identity drift' }
foreach ($Path in @($Project,$Editor,$Python,$Contract,$Baseline,$BaselineSidecar,$Freezer,$Common,$Importer,$Validator)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required lane input missing: $Path" }
}
if ((Get-Sha256 $Contract) -cne $ContractSha256) { throw 'Static clean-room source contract hash drift' }
if (Test-Path -LiteralPath $Destination) { throw "Target native namespace exists; overwrite/reimport forbidden: $Destination" }
Assert-NoPriorResults
Assert-NoProcesses

$SidecarHash = ((Get-Content -LiteralPath $BaselineSidecar -Raw).Trim() -split '\s+')[0].ToUpperInvariant()
$ActualBaselineHash = Get-Sha256 $Baseline
if ($SidecarHash -cne $ActualBaselineHash) { throw 'Frozen whole-project baseline sidecar mismatch' }
$BaselinePayload = Get-Content -Raw -LiteralPath $Baseline | ConvertFrom-Json
if ([string]$BaselinePayload.'$schema' -cne 'lineboss/vehicle-wip-native-kit-v001/unreal-import-baseline/v1' `
        -or [string]$BaselinePayload.status -cne 'FROZEN__VEHICLE_WIP_NATIVE_KIT_V001_UNREAL_IMPORT_BASELINE_V001' `
        -or [int]$BaselinePayload.destination.expected_asset_count -ne 16 `
        -or [int]$BaselinePayload.destination.expected_lod_count_per_asset -ne 3 `
        -or [int]$BaselinePayload.destination.expected_source_fbx_count -ne 48 `
        -or [bool]$BaselinePayload.policy.overwrite_reimport_delete_authorized) {
    throw 'Frozen baseline identity/safety drift'
}
foreach ($Row in @($BaselinePayload.lane.files)) {
    $Path = Join-Path $Root ([string]$Row.path).Replace('/','\')
    if ((Get-Sha256 $Path) -cne [string]$Row.sha256) { throw "Prepared lane hash drift: $($Row.path)" }
}
$BaselineVerifyOutput = (& $Python $Freezer --verify-only 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0 -or $BaselineVerifyOutput -notmatch 'PASS__FULL_SOURCE_AND_PROTECTED_BASELINE_REVERIFY') {
    throw "Full offline source/protected baseline reverify failed: $BaselineVerifyOutput"
}

if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { New-Item -ItemType Directory -Path $AuditRoot | Out-Null }
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Summary = [ordered]@{
    '$schema' = 'lineboss/audit/vehicle-wip-native-kit-v001/import-lane-summary/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'IN_PROGRESS'
    acknowledgement = $Acknowledgement
    project = $Project
    destination = $Destination
    run_root = $RunRoot
    contract_sha256 = $ContractSha256
    baseline_sha256 = $ActualBaselineHash
    offline_baseline_reverify = $BaselineVerifyOutput
    import_process = $null
    validation_process = $null
    import_receipt = $null
    validation_receipt = $null
    recovery = 'No automatic cleanup: any partial packages/evidence remain for explicit review.'
}
try {
    Set-Item -LiteralPath "Env:\$RunEnvironment" -Value $RunRoot
    Set-Item -LiteralPath "Env:\$AckEnvironment" -Value $Acknowledgement
    $ImportArgs = @(
        ('"{0}"' -f $Project), '-Unattended','-NoSplash','-NoSound','-NullRHI','-NoCompile','-NoCompileEditor',
        '-NoLoadStartupPackages','-NoRestoreOpenAssetTabs', ('-ExecutePythonScript="{0}"' -f $Importer),
        ('-abslog="{0}"' -f (Join-Path $RunRoot 'unreal_import.log'))
    )
    $Summary.import_process = Invoke-GuardedProcess $Editor $ImportArgs (Join-Path $RunRoot 'unreal_import.stdout.log') `
        (Join-Path $RunRoot 'unreal_import.stderr.log') 1800 'Vehicle-WIP native-kit import'
    if ([int]$Summary.import_process.exit_code -ne 0 -or (Test-Path -LiteralPath $ImportFailure)) {
        throw "Import failed or emitted failure receipt: exit=$($Summary.import_process.exit_code)"
    }
    $Imported = Read-Receipt $ImportReceipt $ImportStatus 'Import'
    if ([int]$Imported.process_id -ne [int]$Summary.import_process.process_id `
            -or [int]$Imported.asset_count -ne 16 -or [int]$Imported.source_fbx_count -ne 48 `
            -or [int]$Imported.custom_lods_appended -ne 32 `
            -or @($Imported.assets.PSObject.Properties).Count -ne 16 `
            -or -not [bool]$Imported.zero_collision_all_moving_wip_verified `
            -or -not [bool]$Imported.nanite_off_all_assets) {
        throw 'Import receipt complete 16-role/48-LOD contract drift'
    }
    $Guard = $Imported.interchange_fbx_legacy_custom_lod_guard
    if (-not [bool]$Guard.restore_attempted_in_finally -or [int]$Guard.restored_value -ne [int]$Guard.previous_value) {
        throw 'Import receipt lacks legacy FBX custom-LOD CVar restoration proof'
    }
    $Summary.import_receipt = [ordered]@{ path=$ImportReceipt; sha256=Get-Sha256 $ImportReceipt; status=$Imported.status }
    Assert-NoProcesses
    $ValidationArgs = @(
        ('"{0}"' -f $Project), '-Unattended','-NoSplash','-NoSound','-NullRHI','-NoCompile','-NoCompileEditor',
        '-NoLoadStartupPackages','-NoRestoreOpenAssetTabs', ('-ExecutePythonScript="{0}"' -f $Validator),
        ('-abslog="{0}"' -f (Join-Path $RunRoot 'fresh_load_validation.log'))
    )
    $Summary.validation_process = Invoke-GuardedProcess $Editor $ValidationArgs `
        (Join-Path $RunRoot 'fresh_load_validation.stdout.log') `
        (Join-Path $RunRoot 'fresh_load_validation.stderr.log') 1800 'Independent vehicle-WIP native reload validation'
    if ([int]$Summary.validation_process.exit_code -ne 0 -or (Test-Path -LiteralPath $ValidationFailure)) {
        throw "Fresh validator failed or emitted failure receipt: exit=$($Summary.validation_process.exit_code)"
    }
    $Validated = Read-Receipt $ValidationReceipt $ValidationStatus 'Fresh validator'
    if ([int]$Validated.process_id -ne [int]$Summary.validation_process.process_id `
            -or -not [bool]$Validated.fresh_process_proof.distinct `
            -or [int]$Validated.asset_count -ne 16 `
            -or -not [bool]$Validated.target_package_hashes_unchanged_by_fresh_load `
            -or -not [bool]$Validated.complete_source_content_config_maps_saves_and_lane_unchanged `
            -or -not [bool]$Validated.source_manifest_geometry_roundtrip_provenance_and_freeze_reverified `
            -or -not [bool]$Validated.zero_collision_all_moving_wip_persisted `
            -or -not [bool]$Validated.nanite_off_all_assets) {
        throw 'Fresh validator receipt complete immutable contract drift'
    }
    $Summary.validation_receipt = [ordered]@{ path=$ValidationReceipt; sha256=Get-Sha256 $ValidationReceipt; status=$Validated.status }
    $Summary.status = 'PASS__ONE_SHOT_FRESH_IMPORT_AND_INDEPENDENT_RELOAD__VEHICLE_WIP_NATIVE_KIT_V001'
}
catch {
    $Summary.status = 'FAIL_CLOSED__VEHICLE_WIP_NATIVE_KIT_V001_UNREAL_IMPORT_LANE'
    $Summary.error = $_.Exception.Message
    throw
}
finally {
    $Summary.generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($SummaryPath, ($Summary | ConvertTo-Json -Depth 30) + "`n", $Encoding)
    if (Test-Path -LiteralPath "Env:\$RunEnvironment") { Remove-Item -LiteralPath "Env:\$RunEnvironment" }
    if (Test-Path -LiteralPath "Env:\$AckEnvironment") { Remove-Item -LiteralPath "Env:\$AckEnvironment" }
    Write-Output "LINE_BOSS_VEHICLE_WIP_NATIVE_KIT_V001_LANE_SUMMARY=$SummaryPath"
}
