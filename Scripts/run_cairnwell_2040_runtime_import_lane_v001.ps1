[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE')]
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
$EngineEntry = '/Engine/Maps/Entry'
$MaplessStartupOverride = '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:LoadLevelAtStartup=None'
$Contract = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_import_contract.json'
$ContractSidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_import_contract.sha256'
$Baseline = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_import_baseline.json'
$BaselineSidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_import_baseline.sha256'
$RecoveryContract = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v009_contract.json'
$RecoverySidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v009_contract.sha256'
$RecoveryTool = Join-Path $Root 'Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v009.py'
$LogRetryHelper = Join-Path $Root 'Scripts\cairnwell_2040_runtime_log_retry_v003.ps1'
$Common = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001.py'
$Importer = Join-Path $Root 'Scripts\import_cairnwell_2040_runtime_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_cairnwell_2040_runtime_fresh_process_v001.py'
$Destination = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Vehicles\Cairnwell2040Runtime_v001'
$Quarantine = Join-Path $Root 'Saved\Quarantine\OneFactory\Vehicles\Cairnwell2040Runtime_v001\Incident_20260815T124823Z-67c989ee_v006'
$AuditRoot = Join-Path $Root 'Saved\Audits\OneFactory\Vehicles\Cairnwell2040Runtime_v001\UnrealImportLane_v001'
$RecoveryAuditRoot = Join-Path $AuditRoot 'Recovery_v009'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $RecoveryAuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_recovery_v009.json'
$QuarantineReceipt = Join-Path $RunRoot 'quarantine_receipt_v009.json'
$ImportReceipt = Join-Path $RunRoot 'import_receipt_recovery_v009.json'
$ImportFailure = Join-Path $RunRoot 'import_failure_recovery_v009.json'
$ValidationReceipt = Join-Path $RunRoot 'fresh_process_validation_receipt_recovery_v009.json'
$ValidationFailure = Join-Path $RunRoot 'fresh_process_validation_failure_recovery_v009.json'
$ImportStatus = 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_FRESH_IMPORT__4_MESHES__12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE'
$ValidationStatus = 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED'
$SummaryPass = 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_GUARDED_IMPORT_AND_DISTINCT_READ_ONLY_RELOAD'
$RunEnvironment = 'LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_RUN_ROOT'
$AckEnvironment = 'LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_ACK'
$OldRunEnvironment = [Environment]::GetEnvironmentVariable($RunEnvironment, 'Process')
$OldAckEnvironment = [Environment]::GetEnvironmentVariable($AckEnvironment, 'Process')

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required recovery file missing: $Path"
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
        throw "Refusing isolated recovery while Unreal/build processes are active: $Details"
    }
}

function Assert-ExactChildPath([string]$Candidate, [string]$Parent, [string]$Label) {
    $CandidateFull = [IO.Path]::GetFullPath($Candidate).TrimEnd('\')
    $ParentFull = [IO.Path]::GetFullPath($Parent).TrimEnd('\')
    if (-not $CandidateFull.StartsWith($ParentFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes its exact parent: $CandidateFull"
    }
}

function Invoke-RecoveryVerify([string]$Mode, [string]$PassMarker, [string]$Label) {
    $Output = (& $Python $RecoveryTool $Mode 2>&1) -join "`n"
    if ($LASTEXITCODE -ne 0 -or $Output -notmatch [Regex]::Escape($PassMarker)) {
        throw "$Label failed: $Output"
    }
    return $Output
}

function Write-Utf8Json([string]$Path, [object]$Payload) {
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, ($Payload | ConvertTo-Json -Depth 40) + "`n", $Utf8NoBom)
}

function Invoke-GuardedEditor(
        [string]$Script, [string]$Label, [string]$LogName,
        [string]$StdoutName, [string]$StderrName) {
    $LogPath = Join-Path $RunRoot $LogName
    $StdoutPath = Join-Path $RunRoot $StdoutName
    $StderrPath = Join-Path $RunRoot $StderrName
    $Arguments = @(
        ('"{0}"' -f $Project),
        $EngineEntry,
        '-Unattended', '-nop4', '-NoSplash', '-NoSound', '-NullRHI',
        '-NoCompile', '-NoCompileEditor', '-NoAutoSave', '-NoSaveOnExit',
        '-NoLoadStartupPackages', '-NoRestoreOpenAssetTabs',
        $MaplessStartupOverride, '-stdout', '-FullStdOutLogOutput',
        ('-ExecutePythonScript="{0}"' -f $Script),
        ('-abslog="{0}"' -f $LogPath)
    )
    $Process = Start-Process -FilePath $Editor -ArgumentList $Arguments -WorkingDirectory $Root `
        -WindowStyle Hidden -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath -PassThru
    $null = $Process.Handle
    $Exited = $Process.WaitForExit(3600 * 1000)
    if (-not $Exited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw "$Label timed out after 3600 seconds"
    }
    $Process.WaitForExit()
    $Process.Refresh()
    if ($null -eq $Process.ExitCode) { throw "$Label lost its process exit code" }
    $LogEvidence = Get-LBFileEvidenceWithBoundedReadRetry `
        -Path $LogPath -Label "$Label abslog" -TimeoutMilliseconds 15000
    $StdoutEvidence = Get-LBFileEvidenceWithBoundedReadRetry `
        -Path $StdoutPath -Label "$Label redirected stdout" -TimeoutMilliseconds 15000
    $StderrEvidence = Get-LBFileEvidenceWithBoundedReadRetry `
        -Path $StderrPath -Label "$Label redirected stderr" -TimeoutMilliseconds 15000
    $Combined = @($LogEvidence.text, $StdoutEvidence.text, $StderrEvidence.text)
    $FatalPatterns = @(
        'Fatal error:', 'Assertion failed:', 'Unhandled Exception:', 'appError called',
        'Ensure condition failed', 'ModeManager', 'ModeManagerInteractiveToolsContext',
        'Object is not packaged: ModeManagerInteractiveToolsContext None'
    )
    $FoundFatal = @($FatalPatterns | Where-Object { ($Combined -join "`n") -match [Regex]::Escape($_) })
    if ([int]$Process.ExitCode -ne 0 -or $FoundFatal.Count -gt 0) {
        throw "$Label failed strict exit/log gate: exit=$($Process.ExitCode) fatal=$($FoundFatal -join ',')"
    }
    return [ordered]@{
        process_id = $Process.Id
        exit_code = [int]$Process.ExitCode
        fatal_log_patterns = @()
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

function Read-Receipt(
        [string]$Path, [string]$ExpectedSchema, [string]$ExpectedStatus, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label receipt missing: $Path"
    }
    $Payload = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ([string]$Payload.'$schema' -cne $ExpectedSchema `
            -or [string]$Payload.status -cne $ExpectedStatus) {
        throw "$Label receipt schema/status drift"
    }
    return $Payload
}

function Assert-IncidentBinding([object]$Payload, [string]$Label) {
    if ([string]$Payload.recovery_contract_sha256 -cne $RecoveryHash `
            -or [string]$Payload.v001_failed_run_id -cne '20260815T094919Z-7dfb3c0a' `
            -or [string]$Payload.v001_import_failure_sha256 -cne '05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D' `
            -or [string]$Payload.v002_failed_run_id -cne '20260815T103132Z-3fc39714' `
            -or [string]$Payload.v002_import_failure_sha256 -cne '86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1' `
            -or [string]$Payload.v003_failed_run_id -cne '20260815T105958Z-79a98abc' `
            -or [string]$Payload.v003_import_failure_sha256 -cne '3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C' `
            -or [string]$Payload.v004_failed_run_id -cne '20260815T112446Z-4e34bb5c' `
            -or [string]$Payload.v004_import_failure_sha256 -cne 'D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF' `
            -or [string]$Payload.v005_failed_run_id -cne '20260815T115847Z-92ea69dd' `
            -or [string]$Payload.v005_import_failure_sha256 -cne '435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB' `
            -or [string]$Payload.v006_failed_run_id -cne '20260815T124823Z-67c989ee' `
            -or [string]$Payload.v006_import_failure_sha256 -cne 'A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06' `
            -or [string]$Payload.incident_chain_sha256 -cne [string]$RecoveryPayload.incident_chain.binding_sha256 `
            -or [string]$Payload.quarantine_receipt.sha256 -cne $QuarantineReceiptHash) {
        throw "$Label incident/quarantine binding drift"
    }
}

function Get-PostExitPackageHashes([object]$ExpectedPackages, [object]$ReferenceHashes) {
    $Expected = @($ExpectedPackages)
    if ($Expected.Count -ne 11 -or @($ReferenceHashes.PSObject.Properties).Count -ne 11) {
        throw 'Post-exit package closure is not exactly eleven packages'
    }
    $ExpectedDiskPaths = @($Expected | ForEach-Object {
        Join-Path (Join-Path $Root 'Content') (([string]$_).Substring(6).Replace('/', '\') + '.uasset')
    } | ForEach-Object { [IO.Path]::GetFullPath($_) } | Sort-Object)
    $ActualDiskPaths = @(Get-ChildItem -LiteralPath $Destination -Recurse -File | ForEach-Object {
        [IO.Path]::GetFullPath($_.FullName)
    } | Sort-Object)
    if ($ActualDiskPaths.Count -ne 11 `
            -or ($ActualDiskPaths -join "`n") -cne ($ExpectedDiskPaths -join "`n")) {
        throw 'Post-exit namespace all-file closure is not the exact eleven uassets'
    }
    $Hashes = [ordered]@{}
    foreach ($PackageNameValue in $Expected) {
        $PackageName = [string]$PackageNameValue
        $RelativeAsset = $PackageName.Substring(6).Replace('/', '\') + '.uasset'
        $DiskPath = Join-Path (Join-Path $Root 'Content') $RelativeAsset
        $ActualHash = Get-Sha256 $DiskPath
        $Reference = @($ReferenceHashes.PSObject.Properties | Where-Object { $_.Name -ceq $PackageName })
        if ($Reference.Count -ne 1 -or $ActualHash -cne [string]$Reference[0].Value) {
            throw "Post-exit package hash drift: $PackageName"
        }
        $Hashes[$PackageName] = $ActualHash
    }
    return [pscustomobject]$Hashes
}

if ((Resolve-Path -LiteralPath $Root).Path -cne $Root) { throw 'Exact project-root identity drift' }
Assert-ExactChildPath $Destination (Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Vehicles') 'Destination'
Assert-ExactChildPath $Quarantine (Join-Path $Root 'Saved\Quarantine\OneFactory\Vehicles\Cairnwell2040Runtime_v001') 'Quarantine'
Assert-ExactChildPath $RunRoot $RecoveryAuditRoot 'Recovery run root'
foreach ($Path in @(
        $Project,$Editor,$Python,$Contract,$ContractSidecar,$Baseline,$BaselineSidecar,
        $RecoveryContract,$RecoverySidecar,$RecoveryTool,$LogRetryHelper,
        $Common,$Importer,$Validator)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required prepared recovery input missing: $Path"
    }
}
. $LogRetryHelper
if (Test-Path -LiteralPath $RecoveryAuditRoot) {
    throw "Recovery v009 is one-use and a result root already exists: $RecoveryAuditRoot"
}
if (Test-Path -LiteralPath $Quarantine) {
    throw "Recovery v009 quarantine already exists: $Quarantine"
}
Assert-NoProcesses
$ContractHash = Assert-Sidecar $Contract $ContractSidecar 'Original frozen contract'
$BaselineHash = Assert-Sidecar $Baseline $BaselineSidecar 'Original frozen baseline'
$RecoveryHash = Assert-Sidecar $RecoveryContract $RecoverySidecar 'Incident-chained recovery v009 contract'
$RecoveryPayload = Get-Content -Raw -LiteralPath $RecoveryContract | ConvertFrom-Json
$BaselinePayload = Get-Content -Raw -LiteralPath $Baseline | ConvertFrom-Json
if ([string]$RecoveryPayload.'$schema' -cne 'lineboss/cairnwell-2040-runtime-v001/recovery-contract/v9' `
        -or [string]$RecoveryPayload.status -cne 'FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V009__READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT' `
        -or [string]$RecoveryPayload.acknowledgement -cne $Acknowledgement `
        -or [string]$RecoveryPayload.original_authorities.contract.sha256 -cne $ContractHash `
        -or [string]$RecoveryPayload.original_authorities.baseline.sha256 -cne $BaselineHash `
        -or [string]$RecoveryPayload.incident_chain.v001.failed_run_id -cne '20260815T094919Z-7dfb3c0a' `
        -or [string]$RecoveryPayload.incident_chain.v001.import_failure.sha256 -cne '05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D' `
        -or [string]$RecoveryPayload.incident_chain.v002.failed_run_id -cne '20260815T103132Z-3fc39714' `
        -or [string]$RecoveryPayload.incident_chain.v002.import_failure.sha256 -cne '86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1' `
        -or [string]$RecoveryPayload.incident_chain.v003.failed_run_id -cne '20260815T105958Z-79a98abc' `
        -or [string]$RecoveryPayload.incident_chain.v003.import_failure.sha256 -cne '3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C' `
        -or [string]$RecoveryPayload.incident_chain.v004.failed_run_id -cne '20260815T112446Z-4e34bb5c' `
        -or [string]$RecoveryPayload.incident_chain.v004.import_failure.sha256 -cne 'D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF' `
        -or [string]$RecoveryPayload.incident_chain.v005.failed_run_id -cne '20260815T115847Z-92ea69dd' `
        -or [string]$RecoveryPayload.incident_chain.v005.import_failure.sha256 -cne '435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB' `
        -or [string]$RecoveryPayload.incident_chain.v006.failed_run_id -cne '20260815T124823Z-67c989ee' `
        -or [string]$RecoveryPayload.incident_chain.v006.import_failure.sha256 -cne 'A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06' `
        -or [string]$RecoveryPayload.quarantine.operation -cne 'MOVE_DIRECTORY_ONLY__NO_DELETE' `
        -or [bool]$RecoveryPayload.policy.unreal_launch_authorized_by_freeze `
        -or -not [bool]$RecoveryPayload.policy.strict_editor_exit_code_zero_required `
        -or -not [bool]$RecoveryPayload.policy.source_fbx_bounds_must_remain_unmodified `
        -or -not [bool]$RecoveryPayload.policy.runtime_bounds_tolerance_must_remain_0_25_cm `
        -or -not [bool]$RecoveryPayload.policy.exact_ue_enum_identity_required `
        -or -not [bool]$RecoveryPayload.policy.enum_string_suffix_comparisons_forbidden `
        -or -not [bool]$RecoveryPayload.policy.unnamed_material_input_canonicalization_required `
        -or -not [bool]$RecoveryPayload.policy.raw_none_input_names_forbidden_in_graph_evidence `
        -or -not [bool]$RecoveryPayload.policy.exact_prior_all_file_closures_required `
        -or -not [bool]$RecoveryPayload.policy.stale_v007_pair_must_remain_byte_exact `
        -or -not [bool]$RecoveryPayload.policy.stale_v008_pair_must_remain_byte_exact `
        -or -not [bool]$RecoveryPayload.policy.no_write_full_candidate_payload_preflight_required `
        -or [string]$RecoveryPayload.stale_preliminary_v007.status -cne 'STALE__UNEXECUTED_V007_PRELIMINARY__SUPERSEDED_BY_V008_EXACT_CLOSURE' `
        -or [string]$RecoveryPayload.stale_preliminary_v007.contract.sha256 -cne '7271F549ADF301C078636C408B49C5998CE8882A07FB999EF730CB0B97F7698F' `
        -or [string]$RecoveryPayload.stale_preliminary_v007.sidecar.sha256 -cne 'ECC793B9319E935EC29762420421292828B7ADF7C0DBBC93022C3154298F8508' `
        -or -not [bool]$RecoveryPayload.stale_preliminary_v007.recovery_v007_result_root_absent_at_freeze `
        -or -not [bool]$RecoveryPayload.stale_preliminary_v007.v006_quarantine_absent_at_freeze `
        -or [string]$RecoveryPayload.stale_preliminary_v008.status -cne 'STALE__UNEXECUTED_V008_PRELIMINARY__SUPERSEDED_BY_V009_FULL_NO_WRITE_PAYLOAD_PREFLIGHT' `
        -or [string]$RecoveryPayload.stale_preliminary_v008.contract.sha256 -cne '6E8E2D0E6D40A16CFF1AF5BEF31A00498C51DEADADF6CE0901D537285E5E49BD' `
        -or [string]$RecoveryPayload.stale_preliminary_v008.sidecar.sha256 -cne 'D082F35B000CEC489991F8F481AACA78580CCB1326356F468612C4C99CBA054F' `
        -or -not [bool]$RecoveryPayload.stale_preliminary_v008.recovery_v008_result_root_absent_at_freeze `
        -or -not [bool]$RecoveryPayload.stale_preliminary_v008.v006_quarantine_absent_at_freeze `
        -or [bool]$RecoveryPayload.policy.post_receipt_fatal_or_crash_accepted) {
    throw 'Incident-bound recovery contract identity/safety drift'
}
$PreflightVerify = Invoke-RecoveryVerify '--verify-pre-quarantine' `
    'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_PRE_QUARANTINE_REVERIFIED' `
    'Recovery pre-quarantine protected/source/incident/partial reverify'
Assert-NoProcesses

New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Summary = [ordered]@{
    '$schema' = 'lineboss/audit/cairnwell-2040-runtime-v001/recovery-v009/import-lane-summary/v9'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'IN_PROGRESS'
    acknowledgement = $Acknowledgement
    run_root = $RunRoot
    destination = $Destination
    quarantine = $Quarantine
    contract_sha256 = $ContractHash
    baseline_sha256 = $BaselineHash
    recovery_contract_sha256 = $RecoveryHash
    v001_failed_run_id = '20260815T094919Z-7dfb3c0a'
    v001_import_failure_sha256 = '05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D'
    v002_failed_run_id = '20260815T103132Z-3fc39714'
    v002_import_failure_sha256 = '86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1'
    v003_failed_run_id = '20260815T105958Z-79a98abc'
    v003_import_failure_sha256 = '3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C'
    v004_failed_run_id = '20260815T112446Z-4e34bb5c'
    v004_import_failure_sha256 = 'D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF'
    v005_failed_run_id = '20260815T115847Z-92ea69dd'
    v005_import_failure_sha256 = '435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB'
    v006_failed_run_id = '20260815T124823Z-67c989ee'
    v006_import_failure_sha256 = 'A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06'
    incident_chain_sha256 = [string]$RecoveryPayload.incident_chain.binding_sha256
    preflight_reverify = $PreflightVerify
    post_quarantine_reverify = $null
    post_exit_reverify = $null
    quarantine_receipt = $null
    import_process = $null
    validation_process = $null
    import_receipt = $null
    validation_receipt = $null
    post_exit_package_sha256 = $null
    editor_process_count = 0
    no_build_tool_invoked = $true
    strict_exit_zero_and_no_fatal_log_required = $true
    recovery = 'No rerun or automatic cleanup; archive evidence and require a newly reviewed recovery after failure.'
    error = $null
}

try {
    [Environment]::SetEnvironmentVariable($RunEnvironment, $RunRoot, 'Process')
    [Environment]::SetEnvironmentVariable($AckEnvironment, $Acknowledgement, 'Process')

    $QuarantineParent = Split-Path -Parent $Quarantine
    if (-not (Test-Path -LiteralPath $QuarantineParent -PathType Container)) {
        New-Item -ItemType Directory -Path $QuarantineParent | Out-Null
    }
    if (-not (Test-Path -LiteralPath $Destination -PathType Container) `
            -or (Test-Path -LiteralPath $Quarantine)) {
        throw 'Exact source/quarantine precondition drift immediately before move'
    }
    Move-Item -LiteralPath $Destination -Destination $Quarantine
    if ((Test-Path -LiteralPath $Destination) `
            -or -not (Test-Path -LiteralPath $Quarantine -PathType Container)) {
        throw 'Recoverable whole-directory quarantine move did not complete exactly'
    }
    $Summary.post_quarantine_reverify = Invoke-RecoveryVerify '--verify-post-quarantine' `
        'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_POST_QUARANTINE_REVERIFIED' `
        'Recovery post-quarantine hash/closure reverify'
    $QuarantinePayload = [ordered]@{
        '$schema' = 'lineboss/audit/cairnwell-2040-runtime-v001/recovery-v009/quarantine/v9'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_PARTIALS_QUARANTINED'
        recovery_contract_sha256 = $RecoveryHash
        v001_failed_run_id = '20260815T094919Z-7dfb3c0a'
        v001_import_failure_sha256 = '05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D'
        v002_failed_run_id = '20260815T103132Z-3fc39714'
        v002_import_failure_sha256 = '86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1'
        v003_failed_run_id = '20260815T105958Z-79a98abc'
        v003_import_failure_sha256 = '3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C'
        v004_failed_run_id = '20260815T112446Z-4e34bb5c'
        v004_import_failure_sha256 = 'D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF'
        v005_failed_run_id = '20260815T115847Z-92ea69dd'
        v005_import_failure_sha256 = '435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB'
        v006_failed_run_id = '20260815T124823Z-67c989ee'
        v006_import_failure_sha256 = 'A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06'
        incident_chain_sha256 = [string]$RecoveryPayload.incident_chain.binding_sha256
        operation = 'MOVE_DIRECTORY_ONLY__NO_DELETE'
        source_destination_absent_after_move = $true
        quarantined_partial_packages = $RecoveryPayload.partial_packages
    }
    Write-Utf8Json $QuarantineReceipt $QuarantinePayload
    $QuarantineReceiptHash = Get-Sha256 $QuarantineReceipt
    $Summary.quarantine_receipt = [ordered]@{
        path = $QuarantineReceipt
        sha256 = $QuarantineReceiptHash
        status = $QuarantinePayload.status
    }

    $Summary.import_process = Invoke-GuardedEditor $Importer 'Cairnwell recovery import' `
        'unreal_import_recovery_v009.log' 'unreal_import_recovery_v009.stdout.log' `
        'unreal_import_recovery_v009.stderr.log'
    $Summary.editor_process_count++
    if (Test-Path -LiteralPath $ImportFailure) {
        throw 'Recovery importer emitted a failure receipt despite strict process exit gate'
    }
    $Imported = Read-Receipt $ImportReceipt `
        'lineboss/audit/cairnwell-2040-runtime-v001/recovery-v009/unreal-import/v9' `
        $ImportStatus 'Cairnwell recovery import'
    Assert-IncidentBinding $Imported 'Cairnwell recovery import receipt'
    if ([int]$Imported.process_id -ne [int]$Summary.import_process.process_id `
            -or [int]$Imported.mesh_count -ne 4 `
            -or [int]$Imported.authored_lod_count -ne 12 `
            -or [int]$Imported.texture_count -ne 3 `
            -or [int]$Imported.material_count -ne 4 `
            -or [int]$Imported.package_count -ne 11 `
            -or @($Imported.package_sha256.PSObject.Properties).Count -ne 11 `
            -or [string]$Imported.editor_bootstrap_world -cne '/Engine/Maps/Entry.Entry' `
            -or @($Imported.project_maps_loaded_or_saved).Count -ne 0) {
        throw 'Recovery import receipt does not prove the exact 4/12/3/4/11 contract'
    }
    $Summary.import_receipt = [ordered]@{
        path = $ImportReceipt; sha256 = Get-Sha256 $ImportReceipt; status = $Imported.status
    }

    Assert-NoProcesses
    $Summary.validation_process = Invoke-GuardedEditor $Validator `
        'Cairnwell recovery independent read-only validator' `
        'fresh_process_validation_recovery_v009.log' `
        'fresh_process_validation_recovery_v009.stdout.log' `
        'fresh_process_validation_recovery_v009.stderr.log'
    $Summary.editor_process_count++
    if (Test-Path -LiteralPath $ValidationFailure) {
        throw 'Recovery validator emitted a failure receipt despite strict process exit gate'
    }
    $Validated = Read-Receipt $ValidationReceipt `
        'lineboss/audit/cairnwell-2040-runtime-v001/recovery-v009/fresh-process-validation/v9' `
        $ValidationStatus 'Cairnwell recovery fresh-process validator'
    Assert-IncidentBinding $Validated 'Cairnwell recovery validation receipt'
    if ([int]$Validated.process_id -ne [int]$Summary.validation_process.process_id `
            -or [int]$Validated.import_process_id -ne [int]$Imported.process_id `
            -or [int]$Validated.validator_process_id -eq [int]$Imported.process_id `
            -or -not [bool]$Validated.distinct_process_verified `
            -or [int]$Validated.package_count -ne 11 `
            -or -not [bool]$Validated.all_package_hashes_unchanged `
            -or -not [bool]$Validated.persisted_asset_registry_dependency_closure_verified `
            -or [int]$Validated.asset_mutation_count -ne 0) {
        throw 'Recovery fresh-process receipt does not prove distinct immutable validation'
    }
    $ImportPackages = $Imported.package_sha256 | ConvertTo-Json -Compress
    $BeforePackages = $Validated.package_sha256_before_loads | ConvertTo-Json -Compress
    $AfterPackages = $Validated.package_sha256_after_loads | ConvertTo-Json -Compress
    if ($ImportPackages -cne $BeforePackages -or $BeforePackages -cne $AfterPackages) {
        throw 'Package hash closure differs across recovery import and fresh validation'
    }
    $Summary.validation_receipt = [ordered]@{
        path = $ValidationReceipt; sha256 = Get-Sha256 $ValidationReceipt; status = $Validated.status
    }
    if ([int]$Summary.editor_process_count -ne 2) {
        throw 'Recovery lane did not use exactly two sequential editor processes'
    }
    Assert-NoProcesses
    $Summary.post_exit_reverify = Invoke-RecoveryVerify '--verify-post-import' `
        'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_POST_IMPORT_REVERIFIED' `
        'Post-exit recovery source/protected/lane/incident/quarantine reverify'
    $PostExitPackages = Get-PostExitPackageHashes `
        $BaselinePayload.destination.expected_package_paths $Imported.package_sha256
    if (($PostExitPackages | ConvertTo-Json -Compress) -cne $ImportPackages) {
        throw 'Post-exit package hashes differ from the recovery import receipt'
    }
    $Summary.post_exit_package_sha256 = $PostExitPackages
    $Summary.status = $SummaryPass
}
catch {
    $Summary.status = 'FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_UNREAL_IMPORT_LANE'
    $Summary.error = $_.Exception.Message
    throw
}
finally {
    $Summary.generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    Write-Utf8Json $SummaryPath $Summary
    [Environment]::SetEnvironmentVariable($RunEnvironment, $OldRunEnvironment, 'Process')
    [Environment]::SetEnvironmentVariable($AckEnvironment, $OldAckEnvironment, 'Process')
    Write-Output "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_SUMMARY=$SummaryPath"
}
