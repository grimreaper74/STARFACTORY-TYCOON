[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V012_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Engine = 'C:\Program Files\Epic Games\UE_5.8'
$Editor = Join-Path $Engine 'Engine\Binaries\Win64\UnrealEditor.exe'
$Python = Join-Path $Engine 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$EngineEntry = '/Engine/Maps/Entry'
$MaplessStartupOverride = '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:LoadLevelAtStartup=None'
$Contract = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_import_contract.json'
$ContractSidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_import_contract.sha256'
$Baseline = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_import_baseline.json'
$BaselineSidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_import_baseline.sha256'
$V009Contract = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v009_contract.json'
$V009Sidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v009_contract.sha256'
$V010Contract = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v010_contract.json'
$V010Sidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v010_contract.sha256'
$V011Contract = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v011_contract.json'
$V011Sidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v011_contract.sha256'
$RecoveryContract = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v012_contract.json'
$RecoverySidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v012_contract.sha256'
$RecoveryTool = Join-Path $Root 'Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v012.py'
$LogRetryHelper = Join-Path $Root 'Scripts\cairnwell_2040_runtime_log_retry_v003.ps1'
$Validator = Join-Path $Root 'Scripts\validate_cairnwell_2040_runtime_recovery_v012.py'
$Destination = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Vehicles\Cairnwell2040Runtime_v001'
$AuditRoot = Join-Path $Root 'Saved\Audits\OneFactory\Vehicles\Cairnwell2040Runtime_v001\UnrealImportLane_v001'
$RecoveryAuditRoot = Join-Path $AuditRoot 'Recovery_v012'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $RecoveryAuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_recovery_v012.json'
$ValidationReceipt = Join-Path $RunRoot 'fresh_process_validation_receipt_recovery_v012.json'
$ValidationFailure = Join-Path $RunRoot 'fresh_process_validation_failure_recovery_v012.json'
$ValidationStatus = 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD_OF_V009_PASS_IMPORT__EXACT_PERSISTED_DEPENDENCIES__11_PACKAGE_HASHES_UNCHANGED'
$SummaryPass = 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_GUARDED_VALIDATION_ONLY_OF_V009_PASS_IMPORT'
$RunEnvironment = 'LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_RUN_ROOT'
$AckEnvironment = 'LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_ACK'
$SkipUbtEnvironment = 'UE_SKIP_UBT_SDK_SETUP'
$OldRunEnvironment = [Environment]::GetEnvironmentVariable($RunEnvironment, 'Process')
$OldAckEnvironment = [Environment]::GetEnvironmentVariable($AckEnvironment, 'Process')
$OldSkipUbtEnvironment = [Environment]::GetEnvironmentVariable($SkipUbtEnvironment, 'Process')

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required validation-recovery file missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Assert-Sidecar([string]$Payload, [string]$Sidecar, [string]$Label) {
    $Actual = Get-Sha256 $Payload
    if (-not (Test-Path -LiteralPath $Sidecar -PathType Leaf)) {
        throw "$Label sidecar missing: $Sidecar"
    }
    $Expected = ((Get-Content -Raw -LiteralPath $Sidecar).Trim() -split '\s+')[0].ToUpperInvariant()
    if ($Actual -cne $Expected) {
        throw "$Label sidecar mismatch: expected=$Expected actual=$Actual"
    }
    return $Actual
}

function Assert-NoProcesses {
    $Names = @(
        'UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT',
        'ShaderCompileWorker','CrashReportClient','CrashReportClientEditor'
    )
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -gt 0) {
        $Details = ($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', '
        throw "Refusing isolated validation recovery while Unreal/build processes are active: $Details"
    }
    $UbtCommandLines = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        $Command = [string]$_.CommandLine
        $Command -and (
            ($Command -match [Regex]::Escape('UnrealBuildTool.dll') -and
                $Command -match [Regex]::Escape('C:\Program Files\Epic Games\UE_5.8')) -or
            ($Command -match [Regex]::Escape('-Mode=ValidatePlatforms') -and
                ($Command -match [Regex]::Escape('LineBossCarFactory.uproject') -or
                 $Command -match [Regex]::Escape('AutoSDKInfo.txt')))
        )
    })
    if ($UbtCommandLines.Count -gt 0) {
        $Details = ($UbtCommandLines | ForEach-Object { "$($_.Name):$($_.ProcessId):$($_.CommandLine)" }) -join ', '
        throw "Refusing validation recovery while exact UBT command line is active: $Details"
    }
}

function Invoke-RecoveryVerify(
        [string]$Mode, [string]$PassMarker, [string]$Label, [string]$VerifiedRunRoot = '') {
    $Arguments = @($RecoveryTool, $Mode)
    if ($VerifiedRunRoot) {
        $Arguments += @('--run-root', $VerifiedRunRoot)
    }
    $Output = (& $Python @Arguments 2>&1) -join "`n"
    if ($LASTEXITCODE -ne 0 -or $Output -notmatch [Regex]::Escape($PassMarker)) {
        throw "$Label failed: $Output"
    }
    return $Output
}

function Write-Utf8Json([string]$Path, [object]$Payload) {
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, ($Payload | ConvertTo-Json -Depth 40) + "`n", $Utf8NoBom)
}

. $LogRetryHelper

function Invoke-GuardedValidator {
    $LogPath = Join-Path $RunRoot 'fresh_process_validation_recovery_v012.log'
    $StdoutPath = Join-Path $RunRoot 'fresh_process_validation_recovery_v012.stdout.log'
    $StderrPath = Join-Path $RunRoot 'fresh_process_validation_recovery_v012.stderr.log'
    $Arguments = @(
        ('"{0}"' -f $Project),
        $EngineEntry,
        '-Unattended', '-nop4', '-NoSplash', '-NoSound', '-NullRHI',
        '-NoCompile', '-NoCompileEditor', '-NoAutoSave', '-NoSaveOnExit',
        '-NoLoadStartupPackages', '-NoRestoreOpenAssetTabs',
        '-NoAssetRegistryCacheWrite',
        $MaplessStartupOverride, '-stdout', '-FullStdOutLogOutput',
        ('-ExecutePythonScript="{0}"' -f $Validator),
        ('-abslog="{0}"' -f $LogPath)
    )
    $Process = Start-Process -FilePath $Editor -ArgumentList $Arguments -WorkingDirectory $Root `
        -WindowStyle Hidden -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath -PassThru
    $null = $Process.Handle
    $Exited = $Process.WaitForExit(3600 * 1000)
    if (-not $Exited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw 'Cairnwell v012 read-only validator timed out after 3600 seconds'
    }
    $Process.WaitForExit()
    $Process.Refresh()
    if ($null -eq $Process.ExitCode) {
        throw 'Cairnwell v012 read-only validator lost its process exit code'
    }
    $LogEvidence = Get-LBFileEvidenceWithBoundedReadRetry `
        -Path $LogPath -Label 'v012 validator abslog' -TimeoutMilliseconds 15000
    $StdoutEvidence = Get-LBFileEvidenceWithBoundedReadRetry `
        -Path $StdoutPath -Label 'v012 validator redirected stdout' -TimeoutMilliseconds 15000
    $StderrEvidence = Get-LBFileEvidenceWithBoundedReadRetry `
        -Path $StderrPath -Label 'v012 validator redirected stderr' -TimeoutMilliseconds 15000
    $Combined = @($LogEvidence.text, $StdoutEvidence.text, $StderrEvidence.text) -join "`n"
    $FatalPatterns = @(
        'Fatal error:', 'Assertion failed:', 'Unhandled Exception:', 'appError called',
        'Ensure condition failed', 'ModeManager', 'ModeManagerInteractiveToolsContext',
        'Object is not packaged: ModeManagerInteractiveToolsContext None',
        'Launching UnrealBuildTool', 'UnrealBuildTool', 'Build.bat',
        '-Mode=ValidatePlatforms', 'AutoSDKInfo.txt', 'UBT AutoSDK ReturnCode',
        'Asset registry cache written as', 'deleted (orphaned',
        'CleanupOrphanedCacheFiles (PostWrite)'
    )
    $FoundFatal = @($FatalPatterns | Where-Object { $Combined -match [Regex]::Escape($_) })
    if ([int]$Process.ExitCode -ne 0 -or $FoundFatal.Count -gt 0) {
        throw "V012 validator failed strict exit/log/zero-UBT gate: exit=$($Process.ExitCode) fatal=$($FoundFatal -join ',')"
    }
    return [ordered]@{
        process_id = $Process.Id
        exit_code = [int]$Process.ExitCode
        fatal_or_build_tool_log_patterns = @()
        log_sha256 = $LogEvidence.sha256
        stdout_sha256 = $StdoutEvidence.sha256
        stderr_sha256 = $StderrEvidence.sha256
        redirected_log_read_open_retry = [ordered]@{
            log_attempts = $LogEvidence.read_open_attempts
            stdout_attempts = $StdoutEvidence.read_open_attempts
            stderr_attempts = $StderrEvidence.read_open_attempts
            bounded_timeout_milliseconds = 15000
        }
    }
}

foreach ($Path in @(
        $Project,$Editor,$Python,$Contract,$ContractSidecar,$Baseline,$BaselineSidecar,
        $V009Contract,$V009Sidecar,$V010Contract,$V010Sidecar,$V011Contract,$V011Sidecar,
        $RecoveryContract,$RecoverySidecar,$RecoveryTool,$LogRetryHelper,$Validator)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required prepared v012 validation input missing: $Path"
    }
}
if (Test-Path -LiteralPath (Join-Path $AuditRoot 'Recovery_v010')) {
    throw 'Stale recovery v010 must remain unexecuted and absent'
}
if (-not (Test-Path -LiteralPath (Join-Path $AuditRoot 'Recovery_v011') -PathType Container)) {
    throw 'Consumed recovery v011 failure evidence root is absent'
}
if (Test-Path -LiteralPath $RecoveryAuditRoot) {
    throw "Recovery v012 is one-use and a result root already exists: $RecoveryAuditRoot"
}
if (-not (Test-Path -LiteralPath $Destination -PathType Container)) {
    throw 'V009 completed destination is absent; validation-only recovery cannot proceed'
}
Assert-NoProcesses
$ContractHash = Assert-Sidecar $Contract $ContractSidecar 'Original frozen contract'
$BaselineHash = Assert-Sidecar $Baseline $BaselineSidecar 'Original frozen baseline'
$V009Hash = Assert-Sidecar $V009Contract $V009Sidecar 'Executed recovery v009 contract'
$V010Hash = Assert-Sidecar $V010Contract $V010Sidecar 'Stale unexecuted recovery v010 contract'
$V011Hash = Assert-Sidecar $V011Contract $V011Sidecar 'Consumed failed recovery v011 contract'
$RecoveryHash = Assert-Sidecar $RecoveryContract $RecoverySidecar 'Validation-only recovery v012 contract'
$RecoveryPayload = Get-Content -Raw -LiteralPath $RecoveryContract | ConvertFrom-Json
if ([string]$RecoveryPayload.'$schema' -cne 'lineboss/cairnwell-2040-runtime-v001/recovery-contract/v12' `
        -or [string]$RecoveryPayload.status -cne 'FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V012__READY_FOR_ONE_SHOT_VALIDATION_ONLY_OF_V009_PASS_IMPORT' `
        -or [string]$RecoveryPayload.acknowledgement -cne $Acknowledgement `
        -or [string]$RecoveryPayload.original_authorities.contract.sha256 -cne $ContractHash `
        -or [string]$RecoveryPayload.original_authorities.baseline.sha256 -cne $BaselineHash `
        -or [string]$RecoveryPayload.stale_unexecuted_v010.contract.sha256 -cne $V010Hash `
        -or [string]$RecoveryPayload.stale_unexecuted_v010.sidecar.sha256 -cne '0FAA9591022AB275E88BE0DFBDD201BC39FA2BDB69200AA4C345DFBED5ED1C5A' `
        -or -not [bool]$RecoveryPayload.stale_unexecuted_v010.recovery_v010_result_root_absent `
        -or [string]$RecoveryPayload.completed_v009_import.import_receipt.sha256 -cne 'F11952FD07E9B573E0882059C49DF474E166CAE9B25F2F677023260ACAA413A6' `
        -or [string]$RecoveryPayload.completed_v009_import.summary.sha256 -cne '10025897FA49CDFFB94B37C78B082E0D43391E2062BC15BC426BF52C0E6E9265' `
        -or [string]$RecoveryPayload.completed_v009_import.quarantine_receipt.sha256 -cne 'AB17DB911591102E0EB01D0F3DEC56DE03DB51FCE05157739A642E4E796FD587' `
        -or [string]$RecoveryPayload.failed_v011_validation.run_id -cne '20260815T154711Z-18d3ce40' `
        -or [string]$RecoveryPayload.failed_v011_validation.failure_receipt.sha256 -cne '92594B9EED92D7FF1DEBC6210FE2956E5FD84B46B108D71EAC05C7617FA0CAB4' `
        -or [int]$RecoveryPayload.failed_v011_validation.run_snapshot.file_count -ne 5 `
        -or [int]$RecoveryPayload.corrected_fresh_dependency_authority.exact_corrected_field_count -ne 6 `
        -or [string]$RecoveryPayload.corrected_fresh_dependency_authority.fresh_assets_canonical_sha256 -cne '7E8A56991C48F8AEC017C0B4308E220729388A076ABC17C731F70405243B985B' `
        -or [string]$RecoveryPayload.asset_registry_cache_write_suppression.required_command_line_flag -cne '-NoAssetRegistryCacheWrite' `
        -or [int]$RecoveryPayload.asset_registry_cache_write_suppression.exact_pre_validation_snapshot.file_count -ne 2 `
        -or [string]$RecoveryPayload.vehicle_model_identity.model_id -cne 'CAIRNWELL_2040' `
        -or [string]$RecoveryPayload.vehicle_model_identity.production_recipe_id -cne 'CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001' `
        -or [string]$RecoveryPayload.vehicle_model_identity.current_geometry_authority_id -cne 'Cairnwell2040Runtime_v001_V009ImportedGeometry' `
        -or [bool]$RecoveryPayload.vehicle_model_identity.final_release_visual_lock_claimed `
        -or [string]$RecoveryPayload.ubt_startup_suppression.skip_environment_variable -cne $SkipUbtEnvironment `
        -or [string]$RecoveryPayload.ubt_startup_suppression.skip_value -cne '1' `
        -or -not [bool]$RecoveryPayload.policy.validation_only_recovery `
        -or -not [bool]$RecoveryPayload.policy.v010_pair_is_immutable_stale_unexecuted_evidence `
        -or [bool]$RecoveryPayload.policy.v010_execution_authorized `
        -or [bool]$RecoveryPayload.policy.quarantine_move_authorized `
        -or [bool]$RecoveryPayload.policy.delete_copy_import_reimport_save_authorized `
        -or [bool]$RecoveryPayload.policy.importer_process_authorized `
        -or -not [bool]$RecoveryPayload.policy.exactly_one_read_only_validator_process_required `
        -or -not [bool]$RecoveryPayload.policy.exact_six_persisted_dependency_lists_required `
        -or -not [bool]$RecoveryPayload.policy.no_asset_registry_cache_write_flag_required `
        -or -not [bool]$RecoveryPayload.policy.intermediate_cached_asset_registry_exact_invariance_required `
        -or -not [bool]$RecoveryPayload.policy.vehicle_model_identity_decoupled_from_asset_paths `
        -or -not [bool]$RecoveryPayload.policy.development_model_not_final_art `
        -or -not [bool]$RecoveryPayload.policy.powershell_5_1_compatible_runner_required `
        -or -not [bool]$RecoveryPayload.policy.exact_final_summary_and_receipt_key_sets_required `
        -or -not [bool]$RecoveryPayload.policy.ubt_validate_platforms_must_be_suppressed) {
    throw 'Incident-bound v012 validation contract identity/safety drift'
}
if ($V009Hash -cne 'BBDACD06A499240F8FA07D3CECFE661FD6B0C204DD834DB31CDC5B41D3204DAC') {
    throw 'Executed v009 recovery contract hash drift'
}
if ($V010Hash -cne 'CBE1DA417B4009F188E9D35D13402AEA1C7D0CAB9A3EED041ED57F20DA4ADF45') {
    throw 'Stale unexecuted v010 recovery contract hash drift'
}
if ($V011Hash -cne '09A223675EC26F93F85EA2BE8B97568014AA9073681094C46EE04BDADC18719F') {
    throw 'Consumed failed v011 recovery contract hash drift'
}
$PreflightVerify = Invoke-RecoveryVerify '--verify-pre-validation' `
    'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_PRE_VALIDATION_REVERIFIED' `
    'V012 pre-validation protected/source/v009/q6/package/v010 reverify'
Assert-NoProcesses

New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Summary = [ordered]@{
    '$schema' = 'lineboss/audit/cairnwell-2040-runtime-v001/recovery-v012/validation-only-lane-summary/v12'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'IN_PROGRESS'
    acknowledgement = $Acknowledgement
    run_root = $RunRoot
    destination = $Destination
    contract_sha256 = $ContractHash
    baseline_sha256 = $BaselineHash
    v009_recovery_contract_sha256 = $V009Hash
    v010_recovery_contract_sha256 = $V010Hash
    v011_recovery_contract_sha256 = $V011Hash
    recovery_contract_sha256 = $RecoveryHash
    v009_run_id = '20260815T141819Z-435fcd56'
    v011_run_id = '20260815T154711Z-18d3ce40'
    v009_import_receipt_sha256 = 'F11952FD07E9B573E0882059C49DF474E166CAE9B25F2F677023260ACAA413A6'
    v009_wrapper_failure_summary_sha256 = '10025897FA49CDFFB94B37C78B082E0D43391E2062BC15BC426BF52C0E6E9265'
    v011_failure_receipt_sha256 = '92594B9EED92D7FF1DEBC6210FE2956E5FD84B46B108D71EAC05C7617FA0CAB4'
    preflight_reverify = $PreflightVerify
    post_exit_reverify = $null
    validation_process = $null
    validation_receipt = $null
    post_exit_package_sha256 = $null
    editor_process_count = 0
    import_process_count = 0
    content_move_count = 0
    no_build_tool_invoked = $false
    exact_ubt_command_line_matches = 0
    environment_restoration_verified = $false
    strict_exit_zero_no_fatal_and_no_ubt_log_required = $true
    error = $null
}

$CaughtError = $null
$RestoreErrors = @()
try {
    [Environment]::SetEnvironmentVariable($RunEnvironment, $RunRoot, 'Process')
    [Environment]::SetEnvironmentVariable($AckEnvironment, $Acknowledgement, 'Process')
    [Environment]::SetEnvironmentVariable($SkipUbtEnvironment, '1', 'Process')
    if ([Environment]::GetEnvironmentVariable($SkipUbtEnvironment, 'Process') -cne '1') {
        throw 'Failed to set exact UE_SKIP_UBT_SDK_SETUP=1 process guard'
    }
    $Summary.validation_process = Invoke-GuardedValidator
    $Summary.editor_process_count = 1
    if (Test-Path -LiteralPath $ValidationFailure) {
        throw 'V012 read-only validator emitted a failure receipt despite strict exit gate'
    }
    if (-not (Test-Path -LiteralPath $ValidationReceipt -PathType Leaf)) {
        throw 'V012 read-only validator PASS receipt is absent'
    }
    Assert-NoProcesses
    $Summary.post_exit_reverify = Invoke-RecoveryVerify '--verify-post-validation' `
        'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_POST_VALIDATION_REVERIFIED' `
        'V012 post-exit exact receipt/log/package/source/protected reverify' $RunRoot
    $Summary.validation_receipt = [ordered]@{
        path = $ValidationReceipt
        sha256 = Get-Sha256 $ValidationReceipt
        status = $ValidationStatus
    }
    $Summary.post_exit_package_sha256 = $RecoveryPayload.completed_v009_import.package_sha256
}
catch {
    $CaughtError = $_
}
finally {
    $RestoreRows = @(
        [pscustomobject]@{ Name = $RunEnvironment; Value = $OldRunEnvironment },
        [pscustomobject]@{ Name = $AckEnvironment; Value = $OldAckEnvironment },
        [pscustomobject]@{ Name = $SkipUbtEnvironment; Value = $OldSkipUbtEnvironment }
    )
    foreach ($Row in $RestoreRows) {
        try {
            [Environment]::SetEnvironmentVariable($Row.Name, $Row.Value, 'Process')
        }
        catch {
            $RestoreErrors += "$($Row.Name):$($_.Exception.Message)"
        }
    }
}

$RunRestored = [Environment]::GetEnvironmentVariable($RunEnvironment, 'Process') -ceq $OldRunEnvironment
$AckRestored = [Environment]::GetEnvironmentVariable($AckEnvironment, 'Process') -ceq $OldAckEnvironment
$SkipUbtRestored = [Environment]::GetEnvironmentVariable($SkipUbtEnvironment, 'Process') -ceq $OldSkipUbtEnvironment
$Summary.environment_restoration_verified = [bool](
    $RestoreErrors.Count -eq 0 -and $RunRestored -and $AckRestored -and $SkipUbtRestored)
if (-not $Summary.environment_restoration_verified -and $null -eq $CaughtError) {
    $CaughtError = "V012 environment restoration failed: $($RestoreErrors -join ',')"
}
try {
    Assert-NoProcesses
}
catch {
    if ($null -eq $CaughtError) {
        $CaughtError = $_
    }
    else {
        $CaughtError = "$CaughtError; post-restoration process gate: $($_.Exception.Message)"
    }
}
if ($null -ne $CaughtError) {
    $Summary.status = 'FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_VALIDATION_ONLY_LANE'
    $Summary.error = [string]$CaughtError
    $Summary.generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    Write-Utf8Json $SummaryPath $Summary
    throw $CaughtError
}

$Summary.no_build_tool_invoked = $true
$Summary.status = $SummaryPass
$Summary.error = $null
$Summary.generated_utc = (Get-Date).ToUniversalTime().ToString('o')
Write-Utf8Json $SummaryPath $Summary
try {
    $FinalVerify = Invoke-RecoveryVerify '--verify-final' `
        'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_FINAL_FIVE_FILE_REVERIFIED' `
        'V012 final exact five-file/summary/receipt/process/log/package reverify' $RunRoot
    Assert-NoProcesses
}
catch {
    $Summary.status = 'FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_VALIDATION_ONLY_LANE'
    $Summary.error = $_.Exception.Message
    $Summary.generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    Write-Utf8Json $SummaryPath $Summary
    throw
}
Write-Output 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_VALIDATION_ONLY_LANE'
Write-Output "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_SUMMARY=$SummaryPath"
