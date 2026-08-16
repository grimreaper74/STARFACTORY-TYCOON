[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V002_BASELINE_V003_ONCE')]
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
$Baseline = Join-Path $Root 'Scripts\body_shop_support_kit_native_unreal_import_baseline_v003.json'
$Freezer = Join-Path $Root 'Scripts\freeze_body_shop_support_kit_native_unreal_import_baseline_v003.py'
$Importer = Join-Path $Root 'Scripts\import_body_shop_support_kit_native_v002_lane_v003.py'
$Validator = Join-Path $Root 'Scripts\validate_body_shop_support_kit_native_v002_lane_v003.py'
$Destination = Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopSupportKitNative_v002'
$AuditRoot = Join-Path $Root 'Saved\Audits\BodyShop\SupportKitNative_v002\UnrealImportLane_v003'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_v003.json'
$ImportReceipt = Join-Path $RunRoot 'import_receipt_v003.json'
$ImportFailure = Join-Path $RunRoot 'import_failure_v003.json'
$ValidationReceipt = Join-Path $RunRoot 'fresh_load_validation_receipt_v003.json'
$ValidationFailure = Join-Path $RunRoot 'fresh_load_validation_failure_v003.json'
$RecoveryReceipt = Join-Path $RunRoot 'failed_v002_archive_quarantine_receipt_v003.json'

# Re-pinned after every intentional baseline/importer/validator/freezer change.
$ExpectedHashes = [ordered]@{
    baseline = 'A124CE80D77717C062CFFE5AFDD5058905957D29B8A8BB01979A4567149653A6'
    freezer = '249FAFC90068E56D28A6D472730AF885495D7435F4BFEAE82BA55FC88C705A0E'
    importer = '5F3C31C39A91C2A27C7EAB2A2D8E3EB264014076AB221EDA9EB28003B21E554A'
    validator = '10E8D3B11358540671E52AF56BA3F30FF24BDBB95453A5BE5CEF268A1E4DF606'
}
$ExpectedImportStatus = 'PASS__HASH_GUARDED_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V002_BASELINE_V003_UNREAL_INTAKE'
$ExpectedValidationStatus = 'PASS__INDEPENDENT_FRESH_PROCESS_LOAD_12_ASSETS_3_LODS_BODYSHOP_SUPPORT_KIT_NATIVE_V002_LANE_V003'
$RunRootEnvironmentName = 'LINEBOSS_BS_SUPPORT_KIT_NATIVE_V003_RUN_ROOT'
$AcknowledgementEnvironmentName = 'LINEBOSS_BS_SUPPORT_KIT_NATIVE_V003_ACK'
$ResultNames = @(
    'import_receipt_v003.json',
    'import_failure_v003.json',
    'fresh_load_validation_receipt_v003.json',
    'fresh_load_validation_failure_v003.json',
    'failed_v002_archive_quarantine_receipt_v003.json',
    'lane_summary_v003.json'
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

function Resolve-ProjectRelativePath([string]$Relative, [string]$Label) {
    if ([string]::IsNullOrWhiteSpace($Relative) -or [IO.Path]::IsPathRooted($Relative)) {
        throw "$Label must be a non-empty project-relative path: $Relative"
    }
    $Candidate = [IO.Path]::GetFullPath((Join-Path $Root ($Relative -replace '/', '\')))
    $RootPrefix = $Root.TrimEnd('\') + '\'
    if (-not $Candidate.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the project root: $Candidate"
    }
    return $Candidate
}

function Assert-PathInside([string]$Path, [string]$Parent, [string]$Label) {
    $FullPath = [IO.Path]::GetFullPath($Path)
    $FullParent = [IO.Path]::GetFullPath($Parent).TrimEnd('\')
    if (-not $FullPath.StartsWith($FullParent + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label is not inside its approved parent: path=$FullPath parent=$FullParent"
    }
}

function Get-InventoryRows([string]$RootPath, [string]$SourceBaseRelative, [object[]]$ExpectedRows, [string]$Label) {
    if (-not (Test-Path -LiteralPath $RootPath -PathType Container)) {
        throw "$Label root is missing: $RootPath"
    }
    $Expected = @{}
    foreach ($Row in @($ExpectedRows)) {
        $SourcePath = [string]$Row.path
        $Prefix = $SourceBaseRelative.TrimEnd('/') + '/'
        if (-not $SourcePath.StartsWith($Prefix, [StringComparison]::Ordinal)) {
            throw "$Label baseline row escapes its source prefix: $SourcePath"
        }
        $Suffix = $SourcePath.Substring($Prefix.Length)
        if ($Expected.ContainsKey($Suffix)) { throw "$Label duplicate path: $Suffix" }
        $Expected[$Suffix] = $Row
    }
    $ActualFiles = @(Get-ChildItem -LiteralPath $RootPath -Recurse -File -ErrorAction Stop)
    if ($ActualFiles.Count -ne $Expected.Count) {
        throw "$Label file-count drift: expected=$($Expected.Count) actual=$($ActualFiles.Count)"
    }
    $Rows = @()
    $RootPrefix = [IO.Path]::GetFullPath($RootPath).TrimEnd('\') + '\'
    foreach ($File in $ActualFiles) {
        $Full = [IO.Path]::GetFullPath($File.FullName)
        if (-not $Full.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "$Label inventory escaped root: $Full"
        }
        $Suffix = $Full.Substring($RootPrefix.Length).Replace('\', '/')
        if (-not $Expected.ContainsKey($Suffix)) { throw "$Label unexpected file: $Suffix" }
        $Wanted = $Expected[$Suffix]
        $Hash = Get-Sha256 $Full
        if ([int64]$File.Length -ne [int64]$Wanted.bytes -or $Hash -cne [string]$Wanted.sha256) {
            throw "$Label hash/size drift: $Suffix"
        }
        $Rows += [ordered]@{ suffix = $Suffix; bytes = [int64]$File.Length; sha256 = $Hash }
    }
    return @($Rows | Sort-Object suffix)
}

function Write-Utf8NoBomJson([string]$Path, [object]$Payload, [int]$Depth = 20) {
    if (Test-Path -LiteralPath $Path) { throw "Refusing to overwrite JSON evidence: $Path" }
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, ($Payload | ConvertTo-Json -Depth $Depth) + "`n", $Utf8NoBom)
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
        throw "One-shot lane v003 refuses every pre-existing v003 result (PASS or FAIL): $Details"
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

# All checks before RunRoot creation are read-only and cannot consume the failed v002 packages.
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

$BaselinePayload = Get-Content -Raw -LiteralPath $Baseline | ConvertFrom-Json
if ([string]$BaselinePayload.'$schema' -cne 'lineboss/bodyshop-support-kit-native-v002-unreal-import-baseline/v3' `
        -or [string]$BaselinePayload.status -cne 'FROZEN__BODYSHOP_SUPPORT_KIT_NATIVE_V002_UNREAL_IMPORT_BASELINE_V003') {
    throw 'Frozen baseline identity/status drift'
}
$RecoverySpec = $BaselinePayload.failed_v002_recovery
if ([string]$RecoverySpec.status -cne 'FROZEN__ARCHIVE_COPY_THEN_RECOVERABLE_QUARANTINE_MOVE_REQUIRED' `
        -or -not [bool]$RecoverySpec.copy_archive_before_move `
        -or -not [bool]$RecoverySpec.copy_failed_run_evidence_archive_before_move `
        -or -not [bool]$RecoverySpec.move_is_recoverable `
        -or [bool]$RecoverySpec.delete_authorized `
        -or [bool]$RecoverySpec.overwrite_authorized `
        -or [int]$RecoverySpec.expected_partial_package_count -ne 12) {
    throw 'Frozen failed-v002 recovery policy drift'
}
$FailedDestination = Resolve-ProjectRelativePath ([string]$RecoverySpec.failed_destination) 'Failed destination'
$FailedEvidenceRoot = Resolve-ProjectRelativePath ([string]$RecoverySpec.failed_run_evidence_root) 'Failed evidence root'
$RecoveryRoot = Resolve-ProjectRelativePath ([string]$RecoverySpec.recovery_root) 'Recovery root'
$ArchiveDestination = Resolve-ProjectRelativePath ([string]$RecoverySpec.archive_destination) 'Archive destination'
$EvidenceArchiveDestination = Resolve-ProjectRelativePath `
    ([string]$RecoverySpec.failed_run_evidence_archive_destination) 'Failed evidence archive destination'
$QuarantineDestination = Resolve-ProjectRelativePath ([string]$RecoverySpec.quarantine_destination) 'Quarantine destination'
$ApprovedRecoveryParent = Resolve-ProjectRelativePath 'Saved/Recovery/BodyShop' 'Approved recovery parent'
Assert-PathInside $RecoveryRoot $ApprovedRecoveryParent 'Recovery root'
Assert-PathInside $ArchiveDestination $RecoveryRoot 'Archive destination'
Assert-PathInside $EvidenceArchiveDestination $RecoveryRoot 'Failed evidence archive destination'
Assert-PathInside $QuarantineDestination $RecoveryRoot 'Quarantine destination'
if (Test-Path -LiteralPath $RecoveryRoot) {
    throw "One-shot recovery root already exists; overwrite/retry is forbidden: $RecoveryRoot"
}
$FailedRowsBefore = Get-InventoryRows $FailedDestination ([string]$RecoverySpec.failed_destination) `
    @($RecoverySpec.failed_partial_packages) 'Failed v002 partial namespace'
$FailedEvidenceBefore = Get-InventoryRows $FailedEvidenceRoot ([string]$RecoverySpec.failed_run_evidence_root) `
    @($RecoverySpec.failed_run_evidence) 'Failed v002 run evidence'

if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $AuditRoot | Out-Null
}
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Summary = [ordered]@{
        '$schema' = 'lineboss/audit/bodyshop-support-kit-native-v002-unreal-import-lane-summary/v3'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'IN_PROGRESS'
    acknowledgement = $Acknowledgement
    project = $Project
    run_root = $RunRoot
    destination = $Destination
    expected_hashes = $ExpectedHashes
    actual_hashes = $ActualHashes
    preflight = $null
    failed_v002_recovery = [ordered]@{
        status = 'PENDING'
        failed_destination = $FailedDestination
        failed_run_evidence_root = $FailedEvidenceRoot
        recovery_root = $RecoveryRoot
        archive_destination = $ArchiveDestination
        failed_run_evidence_archive_destination = $EvidenceArchiveDestination
        quarantine_destination = $QuarantineDestination
        initial_partial_package_count = @($FailedRowsBefore).Count
        initial_evidence_file_count = @($FailedEvidenceBefore).Count
        receipt = $null
    }
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
    if ($PreflightText -notmatch 'PASS__BODYSHOP_SUPPORT_KIT_NATIVE_V002_BASELINE_V003_MATCHES_SOURCE_AND_PROTECTED_FILES') {
        throw 'Offline immutable-baseline preflight PASS marker missing'
    }
    $Summary.preflight = $Preflight

    # Recovery is deliberately two-copy and ordered: first an independently
    # hash-verified archive copy, then a same-volume recoverable move into
    # quarantine.  No delete, overwrite, broad glob or unresolved target is used.
    New-Item -ItemType Directory -Path $RecoveryRoot | Out-Null
    $ArchiveParent = Join-Path $RecoveryRoot 'Archive'
    $QuarantineParent = Join-Path $RecoveryRoot 'Quarantine'
    New-Item -ItemType Directory -Path $ArchiveParent | Out-Null
    New-Item -ItemType Directory -Path $QuarantineParent | Out-Null
    New-Item -ItemType Directory -Path $ArchiveDestination | Out-Null
    foreach ($Row in @($RecoverySpec.failed_partial_packages)) {
        $SourceRelative = [string]$Row.path
        $Prefix = ([string]$RecoverySpec.failed_destination).TrimEnd('/') + '/'
        if (-not $SourceRelative.StartsWith($Prefix, [StringComparison]::Ordinal)) {
            throw "Recovery source row escapes failed destination: $SourceRelative"
        }
        $Suffix = $SourceRelative.Substring($Prefix.Length)
        $SourceFile = Join-Path $FailedDestination ($Suffix -replace '/', '\')
        $ArchiveFile = Join-Path $ArchiveDestination ($Suffix -replace '/', '\')
        $ArchiveDirectory = Split-Path -Parent $ArchiveFile
        Assert-PathInside $ArchiveFile $ArchiveDestination 'Archive file'
        if (-not (Test-Path -LiteralPath $ArchiveDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $ArchiveDirectory | Out-Null
        }
        if (Test-Path -LiteralPath $ArchiveFile) {
            throw "Refusing to overwrite archive file: $ArchiveFile"
        }
        Copy-Item -LiteralPath $SourceFile -Destination $ArchiveFile
        Assert-ExactHash $ArchiveFile ([string]$Row.sha256) 'Archived failed v002 package' | Out-Null
        if ([int64](Get-Item -LiteralPath $ArchiveFile).Length -ne [int64]$Row.bytes) {
            throw "Archived failed v002 package size drift: $ArchiveFile"
        }
    }
    $ArchiveRows = Get-InventoryRows $ArchiveDestination ([string]$RecoverySpec.failed_destination) `
        @($RecoverySpec.failed_partial_packages) 'Exact-hash archive copy'
    New-Item -ItemType Directory -Path $EvidenceArchiveDestination | Out-Null
    foreach ($Row in @($RecoverySpec.failed_run_evidence)) {
        $SourceRelative = [string]$Row.path
        $Prefix = ([string]$RecoverySpec.failed_run_evidence_root).TrimEnd('/') + '/'
        if (-not $SourceRelative.StartsWith($Prefix, [StringComparison]::Ordinal)) {
            throw "Recovery evidence row escapes failed evidence root: $SourceRelative"
        }
        $Suffix = $SourceRelative.Substring($Prefix.Length)
        $SourceFile = Join-Path $FailedEvidenceRoot ($Suffix -replace '/', '\')
        $ArchiveFile = Join-Path $EvidenceArchiveDestination ($Suffix -replace '/', '\')
        $ArchiveDirectory = Split-Path -Parent $ArchiveFile
        Assert-PathInside $ArchiveFile $EvidenceArchiveDestination 'Failed evidence archive file'
        if (-not (Test-Path -LiteralPath $ArchiveDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $ArchiveDirectory | Out-Null
        }
        if (Test-Path -LiteralPath $ArchiveFile) {
            throw "Refusing to overwrite failed evidence archive file: $ArchiveFile"
        }
        Copy-Item -LiteralPath $SourceFile -Destination $ArchiveFile
        Assert-ExactHash $ArchiveFile ([string]$Row.sha256) 'Archived failed v002 evidence' | Out-Null
        if ([int64](Get-Item -LiteralPath $ArchiveFile).Length -ne [int64]$Row.bytes) {
            throw "Archived failed v002 evidence size drift: $ArchiveFile"
        }
    }
    $EvidenceArchiveRows = Get-InventoryRows $EvidenceArchiveDestination `
        ([string]$RecoverySpec.failed_run_evidence_root) @($RecoverySpec.failed_run_evidence) `
        'Exact-hash failed-run evidence archive copy'
    $EvidenceAfterArchive = Get-InventoryRows $FailedEvidenceRoot ([string]$RecoverySpec.failed_run_evidence_root) `
        @($RecoverySpec.failed_run_evidence) 'Failed v002 evidence after archive copy'
    $FailedRowsBeforeMove = Get-InventoryRows $FailedDestination ([string]$RecoverySpec.failed_destination) `
        @($RecoverySpec.failed_partial_packages) 'Failed v002 namespace before quarantine move'
    if (Test-Path -LiteralPath $QuarantineDestination) {
        throw "Refusing to overwrite quarantine destination: $QuarantineDestination"
    }
    Assert-PathInside $QuarantineDestination $RecoveryRoot 'Quarantine move target'
    Move-Item -LiteralPath $FailedDestination -Destination $QuarantineDestination
    if (Test-Path -LiteralPath $FailedDestination) {
        throw "Failed v002 Content namespace still exists after quarantine move: $FailedDestination"
    }
    $QuarantineRows = Get-InventoryRows $QuarantineDestination ([string]$RecoverySpec.failed_destination) `
        @($RecoverySpec.failed_partial_packages) 'Recoverable quarantine copy'
    $EvidenceAfterMove = Get-InventoryRows $FailedEvidenceRoot ([string]$RecoverySpec.failed_run_evidence_root) `
        @($RecoverySpec.failed_run_evidence) 'Failed v002 evidence after quarantine move'
    $RecoveryRecord = [ordered]@{
        '$schema' = 'lineboss/audit/bodyshop-support-kit-native-v001-failed-v002-recovery/v3'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__FAILED_V002_PACKAGES_EXACT_HASH_ARCHIVED_AND_RECOVERABLY_QUARANTINED'
        baseline_sha256 = $ActualHashes.baseline
        failed_run_evidence_unchanged = $true
        failed_destination_absent_after_move = $true
        archive_created_before_quarantine_move = $true
        failed_run_evidence_archive_created_before_quarantine_move = $true
        delete_or_overwrite_performed = $false
        source_package_count = @($FailedRowsBeforeMove).Count
        archive_package_count = @($ArchiveRows).Count
        quarantine_package_count = @($QuarantineRows).Count
        failed_evidence_file_count = @($EvidenceAfterMove).Count
        archive_destination = $ArchiveDestination
        failed_run_evidence_archive_destination = $EvidenceArchiveDestination
        quarantine_destination = $QuarantineDestination
        archive_rows = $ArchiveRows
        failed_run_evidence_archive_rows = $EvidenceArchiveRows
        quarantine_rows = $QuarantineRows
        failed_evidence_rows = $EvidenceAfterMove
    }
    Write-Utf8NoBomJson $RecoveryReceipt $RecoveryRecord 24
    $Summary.failed_v002_recovery.status = $RecoveryRecord.status
    $Summary.failed_v002_recovery.receipt = [ordered]@{
        path = $RecoveryReceipt
        sha256 = Get-Sha256 $RecoveryReceipt
    }

    $env:LINEBOSS_BS_SUPPORT_KIT_NATIVE_V003_RUN_ROOT = $RunRoot
    $env:LINEBOSS_BS_SUPPORT_KIT_NATIVE_V003_ACK = $Acknowledgement
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
            -or [int]$Imported.source_fbx_count -ne 36 -or [int]$Imported.new_material_or_texture_assets -ne 0 `
            -or @($Imported.assets.PSObject.Properties).Count -ne 12 `
            -or -not [bool]$Imported.strict_per_asset_monotonic_triangles_verified `
            -or -not [bool]$Imported.exact_one_uv_channel_per_lod_verified) {
        throw 'Import receipt does not prove exact 12 meshes / 36 FBXs / no generated materials or textures'
    }
    $CVar = $Imported.interchange_fbx_legacy_custom_lod_guard
    if ([string]$CVar.name -cne 'Interchange.FeatureFlags.Import.FBX' `
            -or [int]$CVar.custom_lods_requested -ne 24 `
            -or @($CVar.custom_lods_imported).Count -ne 24 `
            -or -not [bool]$CVar.restore_attempted_in_finally `
            -or [int]$CVar.restored_value -ne [int]$CVar.previous_value) {
        throw 'Import receipt does not prove guarded legacy custom-LOD import and CVar restoration'
    }
    foreach ($AssetProperty in @($Imported.assets.PSObject.Properties)) {
        $Asset = $AssetProperty.Value
        $Screens = @($Asset.lod_screen_sizes | ForEach-Object { [double]$_ })
        $Lods = @($Asset.lods)
        $Triangles = @($Lods | ForEach-Object { [int]$_.triangles })
        if ($Screens.Count -ne 3 -or $Screens[0] -ne 1.0 -or $Screens[1] -ne 0.45 -or $Screens[2] -ne 0.18 `
                -or [bool]$Asset.lod_screen_size_auto_computed `
                -or [int]$Asset.simple_collision_count -ne 1 `
                -or [int]$Asset.convex_collision_count -ne 0 `
                -or [bool]$Asset.nanite_enabled `
                -or -not [bool]$Asset.strict_monotonic_triangles `
                -or -not [bool]$Asset.screen_size_persistence.global_final_phase_after_all_mesh_preparation `
                -or -not [bool]$Asset.screen_size_persistence.no_build_after_final_set `
                -or @($Asset.screen_size_persistence.passes).Count -ne 2 `
                -or $Lods.Count -ne 3 `
                -or $Triangles[0] -le $Triangles[1] -or $Triangles[1] -le $Triangles[2] -or $Triangles[2] -le 0 `
                -or @($Lods | Where-Object { [int]$_.uv_channels -ne 1 }).Count -ne 0) {
            throw "Import receipt LOD/UV/collision/Nanite contract drift: $($AssetProperty.Name)"
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
            -or @($Validated.assets.PSObject.Properties).Count -ne 12 `
            -or -not [bool]$Validated.target_package_hashes_unchanged_by_fresh_load `
            -or -not [bool]$Validated.source_config_saves_maps_and_existing_content_hashes_unchanged `
            -or -not [bool]$Validated.manual_lod_screen_sizes_persisted_after_fresh_process_load `
            -or -not [bool]$Validated.auto_compute_lod_screen_size_disabled_on_all_assets `
            -or -not [bool]$Validated.deterministic_material_bindings_persisted `
            -or -not [bool]$Validated.deterministic_box_collision_persisted `
            -or -not [bool]$Validated.floor_centred_pivots_and_dimensions_persisted `
            -or -not [bool]$Validated.strict_per_asset_monotonic_triangles_persisted `
            -or -not [bool]$Validated.exact_one_uv_channel_per_lod_persisted `
            -or -not [bool]$Validated.protected_press_v913_restored_press_body_map_config_source_saves_and_native_robot) {
        throw 'Fresh-load receipt does not prove the complete immutable 12-asset support-kit contract'
    }
    foreach ($AssetProperty in @($Validated.assets.PSObject.Properties)) {
        $Asset = $AssetProperty.Value
        $Lods = @($Asset.lods)
        $Triangles = @($Lods | ForEach-Object { [int]$_.triangles })
        if ($Lods.Count -ne 3 -or -not [bool]$Asset.strict_monotonic_triangles `
                -or $Triangles[0] -le $Triangles[1] -or $Triangles[1] -le $Triangles[2] -or $Triangles[2] -le 0 `
                -or @($Lods | Where-Object { [int]$_.uv_channels -ne 1 }).Count -ne 0 `
                -or [bool]$Asset.nanite_enabled) {
            throw "Fresh-load receipt LOD/UV/Nanite contract drift: $($AssetProperty.Name)"
        }
    }
    $Summary.validation_receipt = [ordered]@{
        path = $ValidationReceipt; sha256 = Get-Sha256 $ValidationReceipt; status = $Validated.status
    }
    $Summary.status = 'PASS__HASH_GUARDED_IMPORT_AND_INDEPENDENT_FRESH_LOAD_BODYSHOP_SUPPORT_KIT_NATIVE_V002_LANE_V003'
}
catch {
    $Summary.status = 'FAIL_CLOSED__BODYSHOP_SUPPORT_KIT_NATIVE_V002_UNREAL_IMPORT_LANE_V003'
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
    Write-Output "LINE_BOSS_BODYSHOP_SUPPORT_KIT_NATIVE_V002_LANE_V003_SUMMARY=$SummaryPath"
}
