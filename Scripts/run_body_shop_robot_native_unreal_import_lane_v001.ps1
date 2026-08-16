[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('ARCHIVE_TWO_FAILED_RUNS_MOVE_INVALID_NAMESPACE_AND_CLEAN_IMPORT_HIGH_ELBOW_MONOTONIC_V001_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Engine = 'C:\Program Files\Epic Games\UE_5.8'
$Editor = Join-Path $Engine 'Engine\Binaries\Win64\UnrealEditor.exe'
$Python = Join-Path $Engine 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Baseline = Join-Path $Root 'Scripts\body_shop_robot_native_unreal_import_baseline_v001.json'
$Freezer = Join-Path $Root 'Scripts\freeze_body_shop_robot_native_unreal_import_baseline_v001.py'
$DispositionContract = Join-Path $Root 'Scripts\body_shop_robot_native_unreal_recovery_contract_v001.json'
$DispositionFreezer = Join-Path $Root 'Scripts\freeze_body_shop_robot_native_unreal_recovery_v001.py'
$Archiver = Join-Path $Root 'Scripts\archive_body_shop_robot_native_failed_import_v001.py'
$Importer = Join-Path $Root 'Scripts\import_body_shop_robot_native_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_body_shop_robot_native_v001.py'
$Destination = Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopRobotNative_v001'
$AuditRoot = Join-Path $Root 'Saved\Audits\BodyShop\RobotNative_v001\UnrealImportLane'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_v001.json'
$ImportReceipt = Join-Path $RunRoot 'import_receipt_v001.json'
$ImportFailure = Join-Path $RunRoot 'import_failure_v001.json'
$ArchiveReceipt = Join-Path $RunRoot 'pre_clean_import_disposition_receipt_v001.json'
$ArchiveFailure = Join-Path $RunRoot 'pre_clean_import_disposition_failure_v001.json'
$ValidationReceipt = Join-Path $RunRoot 'fresh_load_validation_receipt_v001.json'
$ValidationFailure = Join-Path $RunRoot 'fresh_load_validation_failure_v001.json'

# Re-pinned after every intentional script or protected-baseline change.
$ExpectedHashes = [ordered]@{
    baseline = 'D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31'
    freezer = '6EF853183079B95EF64DF46E4E7B629273F7F5D4800C2C4EA7360A7AC3EB8CBB'
    disposition_contract = 'E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3'
    disposition_freezer = 'C3A6A96BE2DB1BAC864291F7A36149F1E3171D454A8A0274BFD3477DBF98165C'
    archiver = '5F37A062A7A9EFDF25E856710622C6434543F27890C719CEB04491991C94EC19'
    importer = 'A44FB37410D409BFF7A3DE16E3A069F3A343F1510CAEC52B87CA3010EB02DF2D'
    validator = '6E16B96BDE306380EF6CD600337E7C30F6D8B3BDF5381FE50B3E050689AC559C'
}
$ExpectedArchiveStatus = 'PASS__TWO_FAILED_RUNS_AND_INVALID_NAMESPACE_ARCHIVED_BYTE_FOR_BYTE__INVALID_NAMESPACE_ATOMICALLY_MOVED__CONTENT_PATH_ABSENT'
$ExpectedImportStatus = 'PASS__INCIDENT_ARCHIVED_AND_INVALID_NAMESPACE_MOVED__FRESH_8_ASSET_3_LOD_HIGH_ELBOW_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001_IMPORT'
$ExpectedValidationStatus = 'PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001'
$RunRootEnvironmentName = 'LINEBOSS_BS_ROBOT_NATIVE_RUN_ROOT'
$DispositionModeEnvironmentName = 'LINEBOSS_BS_ROBOT_NATIVE_DISPOSITION_MODE'

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Assert-ExactHash([string]$Path, [string]$Expected, [string]$Label) {
    $Actual = Get-Sha256 $Path
    if ($Actual -cne $Expected) {
        throw "$Label hash drift: expected=$Expected actual=$Actual path=$Path"
    }
    return $Actual
}

function Assert-NoActiveUnrealOrBuildProcess {
    $Names = @('UnrealEditor', 'UnrealEditor-Cmd', 'UnrealBuildTool', 'AutomationTool', 'RunUAT', 'ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -gt 0) {
        $Details = ($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', '
        throw "Refusing the isolated lane while Unreal/build processes are active: $Details"
    }
}

function Read-Receipt([string]$Path, [string]$ExpectedStatus, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label receipt missing: $Path"
    }
    $Payload = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ([string]$Payload.status -cne $ExpectedStatus) {
        throw "$Label receipt status drift: $($Payload.status)"
    }
    return $Payload
}

function Assert-NoPriorPassReceipt {
    if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { return }
    foreach ($Path in Get-ChildItem -LiteralPath $AuditRoot -Recurse -File -Filter 'import_receipt_v001.json' -ErrorAction SilentlyContinue) {
        try {
            $Payload = Get-Content -Raw -LiteralPath $Path.FullName | ConvertFrom-Json
            if ([string]$Payload.status -like 'PASS__*') {
                throw "One-shot v001 lane already completed successfully: $($Path.FullName)"
            }
        } catch [System.Management.Automation.RuntimeException] {
            throw
        } catch {
            # An unreadable non-PASS historical receipt is evidence but does not
            # expand write scope; the UE importer will still fail closed if the
            # destination is not pristine.
        }
    }
}

function Invoke-GuardedProcess(
    [string]$Executable,
    [string[]]$Arguments,
    [string]$Stdout,
    [string]$Stderr,
    [int]$TimeoutSeconds,
    [string]$Label
) {
    $Process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $Root `
        -WindowStyle Hidden -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru
    # Windows PowerShell 5.1 may discard ExitCode after a timed WaitForExit
    # unless the native process handle is materialized immediately.
    $null = $Process.Handle
    $Exited = $Process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $Exited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw "$Label timed out after $TimeoutSeconds seconds; process $($Process.Id) was stopped"
    }
    # Flush asynchronous redirected stream handlers before reading logs.
    $Process.WaitForExit()
    $ExitCode = $Process.ExitCode
    if ($null -eq $ExitCode) {
        throw "$Label completed but Windows PowerShell did not retain its exit code"
    }
    return [ordered]@{ process_id = $Process.Id; exit_code = [int]$ExitCode }
}

New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null
$Summary = [ordered]@{
    '$schema' = 'lineboss/audit/bodyshop-robot-native-v001-unreal-import-lane-summary/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'IN_PROGRESS'
    acknowledgement = $Acknowledgement
    project = $Project
    run_root = $RunRoot
    destination = $Destination
    expected_hashes = $ExpectedHashes
    actual_hashes = [ordered]@{}
    preflight = $null
    disposition_preflight = $null
    archive_process = $null
    archive_receipt = $null
    import_process = $null
    validation_process = $null
    import_receipt = $null
    validation_receipt = $null
    no_ubt_invoked = $true
    error = $null
}

try {
    if ((Resolve-Path -LiteralPath $Root).Path -cne $Root) { throw "Exact project-root identity drift: $Root" }
    foreach ($Path in @($Project, $Editor, $Python, $Baseline, $Freezer, $DispositionContract, `
            $DispositionFreezer, $Archiver, $Importer, $Validator)) {
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required lane input missing: $Path" }
    }
    if (-not (Test-Path -LiteralPath $Destination -PathType Container)) {
        throw "Exact invalid namespace is missing before its authorized archive-and-move disposition: $Destination"
    }
    Assert-NoPriorPassReceipt
    Assert-NoActiveUnrealOrBuildProcess

    $Summary.actual_hashes = [ordered]@{
        baseline = Assert-ExactHash $Baseline $ExpectedHashes.baseline 'Frozen baseline'
        freezer = Assert-ExactHash $Freezer $ExpectedHashes.freezer 'Offline baseline verifier'
        disposition_contract = Assert-ExactHash $DispositionContract $ExpectedHashes.disposition_contract 'Frozen clean disposition contract'
        disposition_freezer = Assert-ExactHash $DispositionFreezer $ExpectedHashes.disposition_freezer 'Offline clean disposition verifier'
        archiver = Assert-ExactHash $Archiver $ExpectedHashes.archiver 'Offline archive-and-move disposition tool'
        importer = Assert-ExactHash $Importer $ExpectedHashes.importer 'Unreal clean fresh importer'
        validator = Assert-ExactHash $Validator $ExpectedHashes.validator 'Fresh-load validator'
    }

    $PreflightStdout = Join-Path $RunRoot 'offline_preflight.stdout.log'
    $PreflightStderr = Join-Path $RunRoot 'offline_preflight.stderr.log'
    $PreflightArguments = @((('"{0}"' -f $Freezer)), '--verify-existing')
    $Preflight = Invoke-GuardedProcess $Python $PreflightArguments `
        $PreflightStdout $PreflightStderr 120 'Offline immutable-baseline preflight'
    if ([int]$Preflight.exit_code -ne 0) {
        throw "Offline immutable-baseline preflight failed with exit code $($Preflight.exit_code)"
    }
    $PreflightText = Get-Content -Raw -LiteralPath $PreflightStdout
    if ($PreflightText -notmatch 'PASS__BODYSHOP_ROBOT_NATIVE_V001_EXISTING_BASELINE_MATCHES_SOURCE_AND_PROTECTED_FILES') {
        throw 'Offline immutable-baseline preflight PASS marker missing'
    }
    $Summary.preflight = $Preflight

    $DispositionPreflightStdout = Join-Path $RunRoot 'offline_disposition_preflight.stdout.log'
    $DispositionPreflightStderr = Join-Path $RunRoot 'offline_disposition_preflight.stderr.log'
    $DispositionPreflightArguments = @((('"{0}"' -f $DispositionFreezer)), '--verify-existing')
    $DispositionPreflight = Invoke-GuardedProcess $Python $DispositionPreflightArguments `
        $DispositionPreflightStdout $DispositionPreflightStderr 120 'Offline incident-bound disposition preflight'
    if ([int]$DispositionPreflight.exit_code -ne 0) {
        throw "Offline incident-bound disposition preflight failed with exit code $($DispositionPreflight.exit_code)"
    }
    $DispositionPreflightText = Get-Content -Raw -LiteralPath $DispositionPreflightStdout
    if ($DispositionPreflightText -notmatch 'PASS__TWO_FAILED_RUNS_AND_INVALID_NAMESPACE_MATCH_CLEAN_DISPOSITION_CONTRACT') {
        throw 'Offline incident-bound disposition preflight PASS marker missing'
    }
    $Summary.disposition_preflight = $DispositionPreflight

    $env:LINEBOSS_BS_ROBOT_NATIVE_RUN_ROOT = $RunRoot
    $env:LINEBOSS_BS_ROBOT_NATIVE_DISPOSITION_MODE = $Acknowledgement
    $ArchiveStdout = Join-Path $RunRoot 'pre_clean_import_disposition.stdout.log'
    $ArchiveStderr = Join-Path $RunRoot 'pre_clean_import_disposition.stderr.log'
    $ArchiveArguments = @((('"{0}"' -f $Archiver)))
    $ArchiveProcess = Invoke-GuardedProcess $Python $ArchiveArguments `
        $ArchiveStdout $ArchiveStderr 300 'Offline failed-run archive and invalid-namespace move'
    $Summary.archive_process = $ArchiveProcess
    if ([int]$ArchiveProcess.exit_code -ne 0) {
        throw "Offline archive-and-move disposition failed with exit code $($ArchiveProcess.exit_code)"
    }
    if (Test-Path -LiteralPath $ArchiveFailure -PathType Leaf) {
        throw "Offline archive-and-move disposition emitted a failure receipt: $ArchiveFailure"
    }
    $Archived = Read-Receipt $ArchiveReceipt $ExpectedArchiveStatus 'Offline archive-and-move disposition'
    if ([int]$Archived.process_id -ne [int]$ArchiveProcess.process_id `
            -or [int]$Archived.failed_run_archive_count -ne 34 `
            -or [int]$Archived.invalid_namespace_archive_count -ne 8 `
            -or [int]$Archived.recoverably_moved_package_count -ne 8 `
            -or -not [bool]$Archived.namespace_move_completed `
            -or -not [bool]$Archived.content_namespace_absent `
            -or [int]$Archived.content_packages_deleted -ne 0 `
            -or [int]$Archived.content_files_written -ne 0) {
        throw 'Offline disposition receipt does not prove both failed runs archived and the exact namespace recoverably moved'
    }
    if (Test-Path -LiteralPath $Destination) {
        throw "Invalid Content namespace remains after the authorized atomic move: $Destination"
    }
    $Summary.archive_receipt = [ordered]@{ path = $ArchiveReceipt; sha256 = Get-Sha256 $ArchiveReceipt; status = $Archived.status }

    Assert-NoActiveUnrealOrBuildProcess
    $ImportStdout = Join-Path $RunRoot 'unreal_import.stdout.log'
    $ImportStderr = Join-Path $RunRoot 'unreal_import.stderr.log'
    $ImportLog = Join-Path $RunRoot 'unreal_import.log'
    $ImportArguments = @(
        ('"{0}"' -f $Project),
        '-Unattended', '-NoSplash', '-NoSound', '-NullRHI', '-NoCompile', '-NoCompileEditor',
        '-NoLoadStartupPackages', '-NoRestoreOpenAssetTabs',
        ('-ExecutePythonScript="{0}"' -f $Importer),
        ('-abslog="{0}"' -f $ImportLog)
    )
    $ImportProcess = Invoke-GuardedProcess $Editor $ImportArguments $ImportStdout $ImportStderr 1200 'Unreal incident-bound clean import'
    $Summary.import_process = $ImportProcess
    if ([int]$ImportProcess.exit_code -ne 0) {
        throw "Unreal incident-bound clean import exited with code $($ImportProcess.exit_code)"
    }
    if (Test-Path -LiteralPath $ImportFailure -PathType Leaf) {
        throw "Guarded import emitted a failure receipt: $ImportFailure"
    }
    $Imported = Read-Receipt $ImportReceipt $ExpectedImportStatus 'Guarded import'
    if ([int]$Imported.process_id -ne [int]$ImportProcess.process_id) {
        throw 'Import receipt process ID does not match the launched editor process'
    }
    if ([int]$Imported.asset_count -ne 8 -or [int]$Imported.lod_count_per_asset -ne 3 -or [int]$Imported.source_fbx_count -ne 24) {
        throw 'Import receipt does not prove the exact 8 assets / 3 LODs / 24 FBXs contract'
    }
    if ([int]$Imported.clean_import_proof.failed_run_count -ne 2 `
            -or -not [bool]$Imported.clean_import_proof.both_failed_runs_hash_verified `
            -or [int]$Imported.clean_import_proof.invalid_package_count_archived_and_moved -ne 8 `
            -or -not [bool]$Imported.clean_import_proof.content_namespace_absent_before_unreal_mutation `
            -or [int]$Imported.clean_import_proof.fresh_lod0_packages_created -ne 8 `
            -or [bool]$Imported.clean_import_proof.replace_existing `
            -or [bool]$Imported.clean_import_proof.reuse_existing_packages `
            -or [int]$Imported.clean_import_proof.existing_lods_reimported -ne 0 `
            -or [int]$Imported.clean_import_proof.missing_lods_appended -ne 16 `
            -or -not [bool]$Imported.clean_import_proof.strict_per_asset_triangle_monotonicity `
            -or -not [bool]$Imported.clean_import_proof.one_uv_per_asset_lod `
            -or [int]$Imported.clean_import_proof.screen_size_persistence_passes -ne 2) {
        throw 'Import receipt lacks exact archive/move/fresh/monotonic/UV/screen proof'
    }
    $CVar = $Imported.clean_import_proof.interchange_fbx_cvar
    if ([string]$CVar.name -cne 'Interchange.FeatureFlags.Import.FBX' `
            -or [int]$CVar.disabled_value -ne 0 `
            -or [int]$CVar.restored_value -ne [int]$CVar.previous_value `
            -or -not [bool]$CVar.restore_attempted_in_finally `
            -or -not [bool]$CVar.set_false_only_around_custom_lod_imports `
            -or @($CVar.custom_lods_imported).Count -ne 16) {
        throw 'Import receipt does not prove scoped Interchange FBX disable/restore semantics'
    }
    foreach ($AssetProperty in @($Imported.assets.PSObject.Properties)) {
        $Asset = $AssetProperty.Value
        $Screens = @($Asset.lod_screen_sizes | ForEach-Object { [double]$_ })
        if ($Screens.Count -ne 3 -or $Screens[0] -ne 1.0 -or $Screens[1] -ne 0.55 -or $Screens[2] -ne 0.25 `
                -or [bool]$Asset.lod_screen_size_auto_computed `
                -or @($Asset.existing_lods_reimported).Count -ne 0 `
                -or -not [bool]$Asset.lod0_created_fresh `
                -or -not [bool]$Asset.strict_triangle_monotonicity `
                -or @($Asset.lods | Where-Object { [int]$_.uv_channels -ne 1 }).Count -ne 0) {
            throw "Import receipt fresh/screen/monotonic/UV proof drift: $($AssetProperty.Name)"
        }
    }
    if ([string]$Imported.active_body_shop_binding_after.status -cne 'PASS__ACTIVE_BODYSHOP_BINDINGS_USE_ONLY_NATIVE_V001_ROBOT_AND_OPEN_CGUN' `
            -or @($Imported.active_body_shop_binding_after.forbidden_matches).Count -ne 0) {
        throw 'Import receipt does not reject old WeldRobotRuntime_v001 paths from active Body Shop bindings'
    }
    $Summary.import_receipt = [ordered]@{ path = $ImportReceipt; sha256 = Get-Sha256 $ImportReceipt; status = $Imported.status }

    Assert-NoActiveUnrealOrBuildProcess
    $ValidationStdout = Join-Path $RunRoot 'fresh_load_validation.stdout.log'
    $ValidationStderr = Join-Path $RunRoot 'fresh_load_validation.stderr.log'
    $ValidationLog = Join-Path $RunRoot 'fresh_load_validation.log'
    $ValidationArguments = @(
        ('"{0}"' -f $Project),
        '-Unattended', '-NoSplash', '-NoSound', '-NullRHI', '-NoCompile', '-NoCompileEditor',
        '-NoLoadStartupPackages', '-NoRestoreOpenAssetTabs',
        ('-ExecutePythonScript="{0}"' -f $Validator),
        ('-abslog="{0}"' -f $ValidationLog)
    )
    $ValidationProcess = Invoke-GuardedProcess $Editor $ValidationArguments $ValidationStdout $ValidationStderr 900 'Independent fresh-load validation'
    $Summary.validation_process = $ValidationProcess
    if ([int]$ValidationProcess.exit_code -ne 0) {
        throw "Independent fresh-load validation exited with code $($ValidationProcess.exit_code)"
    }
    if (Test-Path -LiteralPath $ValidationFailure -PathType Leaf) {
        throw "Fresh-load validator emitted a failure receipt: $ValidationFailure"
    }
    $Validated = Read-Receipt $ValidationReceipt $ExpectedValidationStatus 'Fresh-load validation'
    if ([int]$Validated.process_id -ne [int]$ValidationProcess.process_id) {
        throw 'Validation receipt process ID does not match the launched editor process'
    }
    if ([int]$Validated.fresh_process_proof.import_process_id -eq [int]$Validated.fresh_process_proof.validation_process_id `
            -or -not [bool]$Validated.fresh_process_proof.distinct) {
        throw 'Validation receipt does not prove a process distinct from the importer'
    }
    if ([int]$Validated.asset_count -ne 8 -or [int]$Validated.lod_count_per_asset -ne 3 `
            -or -not [bool]$Validated.target_package_hashes_unchanged_by_fresh_load `
            -or -not [bool]$Validated.config_and_existing_promoted_asset_hashes_unchanged `
            -or -not [bool]$Validated.manual_lod_screen_sizes_persisted_after_fresh_process_load `
            -or -not [bool]$Validated.auto_compute_lod_screen_size_disabled_on_all_assets `
            -or -not [bool]$Validated.strict_per_asset_triangle_monotonicity `
            -or -not [bool]$Validated.exactly_one_uv_channel_on_all_24_lods `
            -or -not [bool]$Validated.fresh_import_no_overwrite_or_reuse_proven `
            -or -not [bool]$Validated.interchange_fbx_cvar_restored_before_validator_process) {
        throw 'Fresh-load receipt does not prove the complete immutable 8-asset/3-LOD gate'
    }
    if ([string]$Validated.active_body_shop_binding_after.status -cne 'PASS__ACTIVE_BODYSHOP_BINDINGS_USE_ONLY_NATIVE_V001_ROBOT_AND_OPEN_CGUN' `
            -or @($Validated.active_body_shop_binding_after.forbidden_matches).Count -ne 0) {
        throw 'Fresh-load receipt does not reject old WeldRobotRuntime_v001 paths from active Body Shop bindings'
    }
    $Summary.validation_receipt = [ordered]@{ path = $ValidationReceipt; sha256 = Get-Sha256 $ValidationReceipt; status = $Validated.status }
    $Summary.status = 'PASS__INCIDENT_ARCHIVED_NAMESPACE_MOVED_CLEAN_IMPORT_AND_INDEPENDENT_FRESH_LOAD_BODYSHOP_ROBOT_NATIVE_V001'
}
catch {
    $Summary.status = 'FAIL_CLOSED__BODYSHOP_ROBOT_NATIVE_V001_INCIDENT_BOUND_CLEAN_IMPORT_LANE'
    $Summary.error = $_.Exception.Message
    throw
}
finally {
    $Summary.generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($SummaryPath, ($Summary | ConvertTo-Json -Depth 16) + "`n", $Utf8NoBom)
    if (Test-Path -LiteralPath "Env:\$RunRootEnvironmentName") {
        Remove-Item -LiteralPath "Env:\$RunRootEnvironmentName"
    }
    if (Test-Path -LiteralPath "Env:\$DispositionModeEnvironmentName") {
        Remove-Item -LiteralPath "Env:\$DispositionModeEnvironmentName"
    }
    Write-Output "LINE_BOSS_BODYSHOP_ROBOT_NATIVE_V001_LANE_SUMMARY=$SummaryPath"
}
