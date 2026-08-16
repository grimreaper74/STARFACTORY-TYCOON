[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_ONCE')]
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
$Baseline = Join-Path $Root 'Scripts\body_shop_support_kit_native_unreal_import_baseline_v001.json'
$Freezer = Join-Path $Root 'Scripts\freeze_body_shop_support_kit_native_unreal_import_baseline_v001.py'
$Importer = Join-Path $Root 'Scripts\import_body_shop_support_kit_native_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_body_shop_support_kit_native_v001.py'
$Destination = Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopSupportKitNative_v001'
$AuditRoot = Join-Path $Root 'Saved\Audits\BodyShop\SupportKitNative_v001\UnrealImportLane'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_v001.json'
$ImportReceipt = Join-Path $RunRoot 'import_receipt_v001.json'
$ImportFailure = Join-Path $RunRoot 'import_failure_v001.json'
$ValidationReceipt = Join-Path $RunRoot 'fresh_load_validation_receipt_v001.json'
$ValidationFailure = Join-Path $RunRoot 'fresh_load_validation_failure_v001.json'

# Re-pinned after every intentional baseline/importer/validator/freezer change.
$ExpectedHashes = [ordered]@{
    baseline = '0000000000000000000000000000000000000000000000000000000000000000'
    freezer = '0000000000000000000000000000000000000000000000000000000000000000'
    importer = '0000000000000000000000000000000000000000000000000000000000000000'
    validator = '0000000000000000000000000000000000000000000000000000000000000000'
}
$ExpectedImportStatus = 'PASS__HASH_GUARDED_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_UNREAL_INTAKE'
$ExpectedValidationStatus = 'PASS__INDEPENDENT_FRESH_PROCESS_LOAD_12_ASSETS_3_LODS_BODYSHOP_SUPPORT_KIT_NATIVE_V001'
$RunRootEnvironmentName = 'LINEBOSS_BS_SUPPORT_KIT_NATIVE_RUN_ROOT'
$AcknowledgementEnvironmentName = 'LINEBOSS_BS_SUPPORT_KIT_NATIVE_ACK'
$ResultNames = @(
    'import_receipt_v001.json',
    'import_failure_v001.json',
    'fresh_load_validation_receipt_v001.json',
    'fresh_load_validation_failure_v001.json',
    'lane_summary_v001.json'
)

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

function Assert-NoPriorLaneResult {
    if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { return }
    $Found = @(
        Get-ChildItem -LiteralPath $AuditRoot -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $ResultNames -contains $_.Name }
    )
    if ($Found.Count -gt 0) {
        $Details = ($Found | ForEach-Object { $_.FullName }) -join '; '
        throw "One-shot v001 lane refuses every pre-existing result (PASS or FAIL): $Details"
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
    # Windows PowerShell 5.1 can lose ExitCode after redirected/timed waits unless
    # the native process handle is materialized while the process is live.
    $null = $Process.Handle
    $Exited = $Process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $Exited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw "$Label timed out after $TimeoutSeconds seconds; process $($Process.Id) was stopped"
    }
    # Flush redirected stream handlers, then refresh the retained process object.
    $Process.WaitForExit()
    $Process.Refresh()
    $ExitCode = $Process.ExitCode
    if ($null -eq $ExitCode) {
        throw "$Label completed but Windows PowerShell 5.1 did not retain its exit code"
    }
    return [ordered]@{ process_id = $Process.Id; exit_code = [int]$ExitCode }
}

# All checks before RunRoot creation are read-only and cannot consume v001.
if ((Resolve-Path -LiteralPath $Root).Path -cne $Root) { throw "Exact project-root identity drift: $Root" }
foreach ($Path in @($Project, $Editor, $Python, $Baseline, $Freezer, $Importer, $Validator)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required lane input missing: $Path" }
}
if (Test-Path -LiteralPath $Destination) {
    throw "Isolated support-kit destination already exists; overwrite/retry is forbidden: $Destination"
}
Assert-NoPriorLaneResult
Assert-NoActiveUnrealOrBuildProcess

$ActualHashes = [ordered]@{
    baseline = Assert-ExactHash $Baseline $ExpectedHashes.baseline 'Frozen baseline'
    freezer = Assert-ExactHash $Freezer $ExpectedHashes.freezer 'Offline baseline verifier'
    importer = Assert-ExactHash $Importer $ExpectedHashes.importer 'Unreal importer'
    validator = Assert-ExactHash $Validator $ExpectedHashes.validator 'Fresh-load validator'
}

New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null
$Summary = [ordered]@{
    '$schema' = 'lineboss/audit/bodyshop-support-kit-native-v001-unreal-import-lane-summary/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'IN_PROGRESS'
    acknowledgement = $Acknowledgement
    project = $Project
    run_root = $RunRoot
    destination = $Destination
    expected_hashes = $ExpectedHashes
    actual_hashes = $ActualHashes
    preflight = $null
    import_process = $null
    validation_process = $null
    import_receipt = $null
    validation_receipt = $null
    no_ubt_invoked = $true
    error = $null
}

try {
    $PreflightStdout = Join-Path $RunRoot 'offline_preflight.stdout.log'
    $PreflightStderr = Join-Path $RunRoot 'offline_preflight.stderr.log'
    $PreflightArguments = @((('"{0}"' -f $Freezer)), '--verify-existing')
    $Preflight = Invoke-GuardedProcess $Python $PreflightArguments `
        $PreflightStdout $PreflightStderr 900 'Offline immutable-baseline preflight'
    if ([int]$Preflight.exit_code -ne 0) {
        throw "Offline immutable-baseline preflight failed with exit code $($Preflight.exit_code)"
    }
    $PreflightText = Get-Content -Raw -LiteralPath $PreflightStdout
    if ($PreflightText -notmatch 'PASS__BODYSHOP_SUPPORT_KIT_NATIVE_V001_EXISTING_BASELINE_MATCHES_SOURCE_AND_PROTECTED_FILES') {
        throw 'Offline immutable-baseline preflight PASS marker missing'
    }
    $Summary.preflight = $Preflight

    $env:LINEBOSS_BS_SUPPORT_KIT_NATIVE_RUN_ROOT = $RunRoot
    $env:LINEBOSS_BS_SUPPORT_KIT_NATIVE_ACK = $Acknowledgement
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
    $ImportProcess = Invoke-GuardedProcess $Editor $ImportArguments $ImportStdout $ImportStderr 1800 'Unreal guarded support-kit import'
    $Summary.import_process = $ImportProcess
    if ([int]$ImportProcess.exit_code -ne 0) {
        throw "Unreal guarded support-kit import exited with code $($ImportProcess.exit_code)"
    }
    if (Test-Path -LiteralPath $ImportFailure -PathType Leaf) {
        throw "Guarded import emitted a failure receipt: $ImportFailure"
    }
    $Imported = Read-Receipt $ImportReceipt $ExpectedImportStatus 'Guarded import'
    if ([int]$Imported.process_id -ne [int]$ImportProcess.process_id) {
        throw 'Import receipt process ID does not match the launched editor process'
    }
    if ([int]$Imported.asset_count -ne 12 -or [int]$Imported.lod_count_per_asset -ne 3 `
            -or [int]$Imported.source_fbx_count -ne 36 -or [int]$Imported.new_material_or_texture_assets -ne 0) {
        throw 'Import receipt does not prove exact 12 meshes / 36 FBXs / no generated materials or textures'
    }
    foreach ($AssetProperty in @($Imported.assets.PSObject.Properties)) {
        $Asset = $AssetProperty.Value
        $Screens = @($Asset.lod_screen_sizes | ForEach-Object { [double]$_ })
        if ($Screens.Count -ne 3 -or $Screens[0] -ne 1.0 -or $Screens[1] -ne 0.45 -or $Screens[2] -ne 0.18 `
                -or [bool]$Asset.lod_screen_size_auto_computed `
                -or [int]$Asset.simple_collision_count -ne 1 `
                -or [int]$Asset.convex_collision_count -ne 0) {
            throw "Import receipt LOD/collision contract drift: $($AssetProperty.Name)"
        }
    }
    $Summary.import_receipt = [ordered]@{
        path = $ImportReceipt; sha256 = Get-Sha256 $ImportReceipt; status = $Imported.status
    }

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
    $ValidationProcess = Invoke-GuardedProcess $Editor $ValidationArguments `
        $ValidationStdout $ValidationStderr 1800 'Independent fresh-load validation'
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
    if ([int]$Validated.asset_count -ne 12 -or [int]$Validated.lod_count_per_asset -ne 3 `
            -or -not [bool]$Validated.target_package_hashes_unchanged_by_fresh_load `
            -or -not [bool]$Validated.source_config_saves_maps_and_existing_content_hashes_unchanged `
            -or -not [bool]$Validated.manual_lod_screen_sizes_persisted_after_fresh_process_load `
            -or -not [bool]$Validated.auto_compute_lod_screen_size_disabled_on_all_assets `
            -or -not [bool]$Validated.deterministic_material_bindings_persisted `
            -or -not [bool]$Validated.deterministic_box_collision_persisted `
            -or -not [bool]$Validated.floor_centred_pivots_and_dimensions_persisted) {
        throw 'Fresh-load receipt does not prove the complete immutable 12-asset support-kit contract'
    }
    $Summary.validation_receipt = [ordered]@{
        path = $ValidationReceipt; sha256 = Get-Sha256 $ValidationReceipt; status = $Validated.status
    }
    $Summary.status = 'PASS__HASH_GUARDED_IMPORT_AND_INDEPENDENT_FRESH_LOAD_BODYSHOP_SUPPORT_KIT_NATIVE_V001'
}
catch {
    $Summary.status = 'FAIL_CLOSED__BODYSHOP_SUPPORT_KIT_NATIVE_V001_UNREAL_IMPORT_LANE'
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
    if (Test-Path -LiteralPath "Env:\$AcknowledgementEnvironmentName") {
        Remove-Item -LiteralPath "Env:\$AcknowledgementEnvironmentName"
    }
    Write-Output "LINE_BOSS_BODYSHOP_SUPPORT_KIT_NATIVE_V001_LANE_SUMMARY=$SummaryPath"
}
