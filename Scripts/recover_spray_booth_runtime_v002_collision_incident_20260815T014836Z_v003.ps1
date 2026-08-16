[CmdletBinding()]
param(
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Incident-bound one-shot recovery. It can consume only the exact partial
# namespace left by run 20260815T014836Z. It preserves two byte-identical
# package copies plus the original failed run before calling the normal fresh
# lane exactly once. It never deletes or overwrites a Content package.
$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Runner = Join-Path $Root 'Scripts\run_spray_booth_runtime_v002_validation.ps1'
$Importer = Join-Path $Root 'Scripts\import_spray_booth_runtime_v002.py'
$Validator = Join-Path $Root 'Scripts\validate_spray_booth_runtime_v002.py'
$Authority = Join-Path $Root 'SourceAssets\Candidate\PaintShop\SprayBoothRuntime_v002\Authority\unreal_lane_recovery_authority_v003.json'
$DiagnosticScript = Join-Path $Root 'Scripts\diagnose_spray_booth_runtime_v002_collision.py'
$DiagnosticLog = Join-Path $Root 'Saved\Logs\diagnose_spray_booth_runtime_v002_collision.log'
$ExtendedDiagnosticLog = Join-Path $Root 'Saved\Logs\diagnose_spray_booth_runtime_v002_collision_v002.log'
$DestinationDisk = Join-Path $Root 'Content\LineBoss\Candidates\PaintShop\SprayBoothRuntime_v002'
$FailedPackage = Join-Path $DestinationDisk 'SM_LB_PaintSprayBooth_Runtime_v002.uasset'
$FailedRun = Join-Path $Root 'Saved\Audits\PaintShop\SprayBoothRuntime_v002\Runs\20260815T014836Z'
$FailedImportLog = Join-Path $FailedRun 'import.log'
$ImportReceipt = Join-Path $Root 'Saved\Audits\PaintShop\SprayBoothRuntime_v002\import_v002.json'
$ValidationReceipt = Join-Path $Root 'Saved\Audits\PaintShop\SprayBoothRuntime_v002\validation_v002.json'
$RunsRoot = Join-Path $Root 'Saved\Audits\PaintShop\SprayBoothRuntime_v002\Runs'
$QuarantineRoot = Join-Path $Root 'Saved\Quarantine\PaintShop\SprayBoothRuntime_v002'
$ArchiveRoot = Join-Path $QuarantineRoot 'Incident_20260815T014836Z'
$ArchivedRun = Join-Path $ArchiveRoot 'FailedRunEvidence'
$ArchivedDiagnostics = Join-Path $ArchiveRoot 'DiagnosticEvidence'
$PackageByteArchive = Join-Path $ArchiveRoot 'PartialPackageByteArchive'
$ArchivedPackage = Join-Path $PackageByteArchive 'SM_LB_PaintSprayBooth_Runtime_v002__FAILED__B2EAC396E3C28575.uasset'
$QuarantinedParent = Join-Path $ArchiveRoot 'QuarantinedDestination'
$QuarantinedNamespace = Join-Path $QuarantinedParent 'SprayBoothRuntime_v002'
$QuarantinedPackage = Join-Path $QuarantinedNamespace 'SM_LB_PaintSprayBooth_Runtime_v002.uasset'
$PreRetryReceipt = Join-Path $ArchiveRoot 'incident_recovery_pre_retry_v003.json'
$RetrySummary = Join-Path $ArchiveRoot 'incident_recovery_retry_summary_v003.json'
$RecoveryFailure = Join-Path $ArchiveRoot 'incident_recovery_failure_v003.json'

$ExpectedFailedPackageLength = 112825
$ExpectedFailedPackageSha256 = 'B2EAC396E3C285750F10E2A57920C42D13FB80B1374DF3FB4AF537E581EEE0D8'
$ExpectedFailedLogLength = 653696
$ExpectedFailedLogSha256 = 'AA2181E79CA8C7AAB14D3A0B92CB6E608A326887D10C6F7F69AD74D880806898'
$ExpectedDiagnosticLogLength = 319681
$ExpectedDiagnosticLogSha256 = '9D7679D1CE949CBFC270B1F936E009442B99401DA5B5A45AF1F8B42B56A16C02'
$ExpectedExtendedDiagnosticLogLength = 320969
$ExpectedExtendedDiagnosticLogSha256 = 'E99A176FB01D8DACC91303FE0FE5183F7AB86C2D10235D3069F56A01DCCA78DF'
$ExpectedDiagnosticScriptLength = 2383
$ExpectedDiagnosticScriptSha256 = '6AD60E5F5254868A197B394BB64123BF584DF88C864B88FD70BE3FDBCD57509E'
$ExpectedAuthoritySha256 = '541A4F2DBD97A19106F932B39CF495A7FB7030371F7C7EDC18CE8D6CA4C73034'
$ExpectedImporterSha256 = 'B23FF792228CC5198178CE99C6C8BFFD322FD9720424329FDBD01485F28399EF'
$ExpectedValidatorSha256 = '2AC134AF9A91730186AEFA83F66B933FBFCD337BEBAE652F52BB124403962196'
$ExpectedRunnerSha256 = '432F6722293FA293A4CBEE6406CE984BD787C635A806AD697A04B5F95EB4CE8D'

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}

function Get-ProjectRelative([string]$Path) {
    $Full = [IO.Path]::GetFullPath($Path)
    $Prefix = $Root.TrimEnd('\') + '\'
    if (-not $Full.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escaped project root: $Full"
    }
    return $Full.Substring($Prefix.Length).Replace('\','/')
}

function Assert-StrictChild([string]$Path, [string]$Parent, [string]$Purpose) {
    $Full = [IO.Path]::GetFullPath($Path)
    $ParentFull = [IO.Path]::GetFullPath($Parent).TrimEnd('\')
    if (-not $Full.StartsWith($ParentFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Purpose escaped its exact parent: $Full"
    }
}

function Assert-ExactFile(
        [string]$Path, [long]$Length, [string]$Sha256, [string]$Purpose) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Purpose is missing: $Path"
    }
    $Item = Get-Item -LiteralPath $Path
    $ActualSha256 = Get-Sha256 $Path
    if ($Item.Length -ne $Length -or $ActualSha256 -cne $Sha256) {
        throw "$Purpose drifted: length=$($Item.Length) sha256=$ActualSha256"
    }
}

function Get-ProtectedSnapshot {
    $Snapshot = [ordered]@{}
    foreach ($Base in @(
            (Join-Path $Root 'Content'),
            (Join-Path $Root 'Config'),
            (Join-Path $Root 'Saved\SaveGames'))) {
        if (Test-Path -LiteralPath $Base -PathType Container) {
            foreach ($Item in @(Get-ChildItem -LiteralPath $Base -File -Recurse | Sort-Object FullName)) {
                if ($Item.FullName.StartsWith(
                        $DestinationDisk.TrimEnd('\') + '\',
                        [StringComparison]::OrdinalIgnoreCase)) {
                    continue
                }
                $Snapshot[(Get-ProjectRelative $Item.FullName)] = Get-Sha256 $Item.FullName
            }
        }
    }
    return $Snapshot
}

function Assert-SameSnapshot([object]$Before, [object]$After, [string]$Stage) {
    if (($Before | ConvertTo-Json -Depth 4 -Compress) -cne
            ($After | ConvertTo-Json -Depth 4 -Compress)) {
        throw "$Stage changed protected existing Content/Config/SaveGames"
    }
}

Assert-StrictChild $FailedPackage $DestinationDisk 'Exact failed package'
Assert-StrictChild $ArchiveRoot $QuarantineRoot 'Incident archive'
Assert-StrictChild $QuarantinedNamespace $ArchiveRoot 'Quarantined namespace'
Assert-StrictChild $ArchivedPackage $ArchiveRoot 'Byte archive package'

foreach ($Required in @(
        $Runner, $Importer, $Validator, $Authority, $DiagnosticScript,
        $DiagnosticLog, $ExtendedDiagnosticLog, $FailedImportLog, $FailedPackage)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) {
        throw "Incident recovery prerequisite is missing: $Required"
    }
}
if ((Get-Sha256 $Runner) -cne $ExpectedRunnerSha256) { throw 'Frozen normal runner hash drift' }
if ((Get-Sha256 $Importer) -cne $ExpectedImporterSha256) { throw 'Frozen importer hash drift' }
if ((Get-Sha256 $Validator) -cne $ExpectedValidatorSha256) { throw 'Frozen validator hash drift' }
if ((Get-Sha256 $Authority) -cne $ExpectedAuthoritySha256) { throw 'Frozen successor authority hash drift' }
Assert-ExactFile $DiagnosticScript $ExpectedDiagnosticScriptLength `
    $ExpectedDiagnosticScriptSha256 'Exact diagnostic script'
Assert-ExactFile $DiagnosticLog $ExpectedDiagnosticLogLength `
    $ExpectedDiagnosticLogSha256 'Exact first diagnostic log'
Assert-ExactFile $ExtendedDiagnosticLog $ExpectedExtendedDiagnosticLogLength `
    $ExpectedExtendedDiagnosticLogSha256 'Exact extended diagnostic log'
Assert-ExactFile $FailedImportLog $ExpectedFailedLogLength `
    $ExpectedFailedLogSha256 'Exact failed import log'
Assert-ExactFile $FailedPackage $ExpectedFailedPackageLength `
    $ExpectedFailedPackageSha256 'Exact partial package'

if (Test-Path -LiteralPath $ArchiveRoot) {
    throw "Incident archive already exists; recovery is one-use only: $ArchiveRoot"
}
foreach ($Receipt in @($ImportReceipt, $ValidationReceipt)) {
    if (Test-Path -LiteralPath $Receipt) {
        throw "Fresh-only stable receipt unexpectedly exists: $Receipt"
    }
}
$LiveUnreal = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -in @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool')
})
if ($LiveUnreal.Count -ne 0) {
    throw "Close active Unreal/build processes before recovery: $($LiveUnreal.ProcessName -join ', ')"
}

$DestinationItems = @(Get-ChildItem -LiteralPath $DestinationDisk -Force)
if ($DestinationItems.Count -ne 1 -or $DestinationItems[0].PSIsContainer -or
        $DestinationItems[0].FullName -cne [IO.Path]::GetFullPath($FailedPackage)) {
    throw 'Candidate destination is not the exact one-package failed incident state'
}
$FailedRunItems = @(Get-ChildItem -LiteralPath $FailedRun -Force)
if ($FailedRunItems.Count -ne 1 -or $FailedRunItems[0].PSIsContainer -or
        $FailedRunItems[0].FullName -cne [IO.Path]::GetFullPath($FailedImportLog)) {
    throw 'Failed run is not the exact one-log incident state'
}
if ([IO.Path]::GetPathRoot($DestinationDisk) -cne [IO.Path]::GetPathRoot($ArchiveRoot)) {
    throw 'Content namespace and quarantine are not on the same volume'
}

$Before = Get-ProtectedSnapshot
$RunNamesBefore = @(
    Get-ChildItem -LiteralPath $RunsRoot -Directory |
        Select-Object -ExpandProperty Name | Sort-Object
)
$Stage = 'PREFLIGHT_COMPLETE'
$NormalLaneInvocations = 0

try {
    $Stage = 'ARCHIVE_EXACT_INCIDENT'
    New-Item -ItemType Directory -Path $ArchivedRun | Out-Null
    New-Item -ItemType Directory -Path $ArchivedDiagnostics | Out-Null
    New-Item -ItemType Directory -Path $PackageByteArchive | Out-Null
    New-Item -ItemType Directory -Path $QuarantinedParent | Out-Null

    Copy-Item -LiteralPath $FailedImportLog -Destination (Join-Path $ArchivedRun 'import.log')
    Copy-Item -LiteralPath $DiagnosticScript -Destination `
        (Join-Path $ArchivedDiagnostics 'diagnose_spray_booth_runtime_v002_collision.py')
    Copy-Item -LiteralPath $DiagnosticLog -Destination `
        (Join-Path $ArchivedDiagnostics 'diagnose_spray_booth_runtime_v002_collision.log')
    Copy-Item -LiteralPath $ExtendedDiagnosticLog -Destination `
        (Join-Path $ArchivedDiagnostics 'diagnose_spray_booth_runtime_v002_collision_v002.log')
    Copy-Item -LiteralPath $FailedPackage -Destination $ArchivedPackage

    Assert-ExactFile (Join-Path $ArchivedRun 'import.log') $ExpectedFailedLogLength `
        $ExpectedFailedLogSha256 'Archived failed import log'
    Assert-ExactFile (Join-Path $ArchivedDiagnostics 'diagnose_spray_booth_runtime_v002_collision.py') `
        $ExpectedDiagnosticScriptLength $ExpectedDiagnosticScriptSha256 'Archived diagnostic script'
    Assert-ExactFile (Join-Path $ArchivedDiagnostics 'diagnose_spray_booth_runtime_v002_collision.log') `
        $ExpectedDiagnosticLogLength $ExpectedDiagnosticLogSha256 'Archived first diagnostic log'
    Assert-ExactFile (Join-Path $ArchivedDiagnostics 'diagnose_spray_booth_runtime_v002_collision_v002.log') `
        $ExpectedExtendedDiagnosticLogLength $ExpectedExtendedDiagnosticLogSha256 'Archived extended diagnostic log'
    Assert-ExactFile $ArchivedPackage $ExpectedFailedPackageLength `
        $ExpectedFailedPackageSha256 'Byte-archived partial package'

    # Re-prove the live sources immediately before the one authorized move.
    Assert-ExactFile $FailedImportLog $ExpectedFailedLogLength `
        $ExpectedFailedLogSha256 'Original failed import log before move'
    Assert-ExactFile $FailedPackage $ExpectedFailedPackageLength `
        $ExpectedFailedPackageSha256 'Partial package before move'

    $Stage = 'QUARANTINE_EXACT_DESTINATION'
    Move-Item -LiteralPath $DestinationDisk -Destination $QuarantinedNamespace
    if (Test-Path -LiteralPath $DestinationDisk) {
        throw 'Candidate destination still exists after guarded quarantine move'
    }
    Assert-ExactFile $QuarantinedPackage $ExpectedFailedPackageLength `
        $ExpectedFailedPackageSha256 'Quarantined partial package'
    Assert-ExactFile $ArchivedPackage $ExpectedFailedPackageLength `
        $ExpectedFailedPackageSha256 'Post-move byte-archived partial package'
    Assert-ExactFile $FailedImportLog $ExpectedFailedLogLength `
        $ExpectedFailedLogSha256 'Preserved original failed import log'
    Assert-SameSnapshot $Before (Get-ProtectedSnapshot) 'Incident archive and quarantine'

    $PreRetry = [ordered]@{
        '$schema' = 'lineboss/audit/paint/spray-booth-runtime-v002-collision-incident-recovery-v003/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'READY__FAILED_RUN_COPIED__PARTIAL_PACKAGE_BYTE_ARCHIVED_AND_QUARANTINED__FRESH_RETRY_NOT_STARTED'
        incident_run = '20260815T014836Z'
        failed_run_source = Get-ProjectRelative $FailedRun
        failed_run_copy = Get-ProjectRelative $ArchivedRun
        partial_package = [ordered]@{
            original_path = 'Content/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002/SM_LB_PaintSprayBooth_Runtime_v002.uasset'
            byte_archive_path = Get-ProjectRelative $ArchivedPackage
            quarantine_path = Get-ProjectRelative $QuarantinedPackage
            bytes = $ExpectedFailedPackageLength
            sha256 = $ExpectedFailedPackageSha256
        }
        failed_import_log = [ordered]@{
            source_path = Get-ProjectRelative $FailedImportLog
            archived_path = Get-ProjectRelative (Join-Path $ArchivedRun 'import.log')
            bytes = $ExpectedFailedLogLength
            sha256 = $ExpectedFailedLogSha256
        }
        importer_sha256 = $ExpectedImporterSha256
        validator_sha256 = $ExpectedValidatorSha256
        normal_runner_sha256 = $ExpectedRunnerSha256
        successor_authority_sha256 = $ExpectedAuthoritySha256
        normal_lane_invocation_limit = 1
        content_packages_deleted = 0
        automatic_cleanup = 'NOT_AUTHORIZED'
    }
    $PreRetry | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $PreRetryReceipt -Encoding utf8

    $Stage = 'NORMAL_FRESH_LANE'
    $NormalLaneInvocations++
    & $Runner -EngineRoot $EngineRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Normal spray-booth lane returned exit code $LASTEXITCODE"
    }
    if ($NormalLaneInvocations -ne 1) {
        throw "Normal lane invocation cardinality drift: $NormalLaneInvocations"
    }

    $Stage = 'POST_RETRY_VERIFICATION'
    Assert-SameSnapshot $Before (Get-ProtectedSnapshot) 'Fresh retry'
    Assert-ExactFile $QuarantinedPackage $ExpectedFailedPackageLength `
        $ExpectedFailedPackageSha256 'Post-retry quarantined partial package'
    Assert-ExactFile $ArchivedPackage $ExpectedFailedPackageLength `
        $ExpectedFailedPackageSha256 'Post-retry byte-archived partial package'
    Assert-ExactFile $FailedImportLog $ExpectedFailedLogLength `
        $ExpectedFailedLogSha256 'Post-retry original failed import log'
    foreach ($Receipt in @($ImportReceipt, $ValidationReceipt)) {
        if (-not (Test-Path -LiteralPath $Receipt -PathType Leaf)) {
            throw "Normal lane returned without stable receipt: $Receipt"
        }
    }
    $RunNamesAfter = @(
        Get-ChildItem -LiteralPath $RunsRoot -Directory |
            Select-Object -ExpandProperty Name | Sort-Object
    )
    $NewRunNames = @($RunNamesAfter | Where-Object { $_ -notin $RunNamesBefore })
    if ($NewRunNames.Count -ne 1) {
        throw "Expected exactly one new normal-lane run; found $($NewRunNames -join ', ')"
    }

    $Summary = [ordered]@{
        '$schema' = 'lineboss/audit/paint/spray-booth-runtime-v002-collision-incident-retry-summary-v003/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__FAILED_RUN_AND_PARTIAL_PACKAGE_PRESERVED__EXACTLY_ONE_FRESH_NORMAL_LANE_PASSED'
        incident_run = '20260815T014836Z'
        retry_run = $NewRunNames[0]
        normal_lane_invocations = $NormalLaneInvocations
        quarantined_partial_package_sha256 = Get-Sha256 $QuarantinedPackage
        byte_archived_partial_package_sha256 = Get-Sha256 $ArchivedPackage
        preserved_failed_import_log_sha256 = Get-Sha256 $FailedImportLog
        fresh_import_receipt_sha256 = Get-Sha256 $ImportReceipt
        fresh_validation_receipt_sha256 = Get-Sha256 $ValidationReceipt
        protected_existing_content_config_savegames_unchanged = $true
        content_packages_deleted = 0
    }
    $Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $RetrySummary -Encoding utf8
    Write-Host 'PASS: exact failed spray-booth output preserved and one fresh corrected lane passed.'
    Write-Host "Incident archive: $ArchiveRoot"
    Write-Host "Retry run: $($NewRunNames[0])"
}
catch {
    if (Test-Path -LiteralPath $ArchiveRoot -PathType Container) {
        $Failure = [ordered]@{
            '$schema' = 'lineboss/audit/paint/spray-booth-runtime-v002-collision-incident-recovery-failure-v003/v1'
            generated_utc = (Get-Date).ToUniversalTime().ToString('o')
            status = 'FAIL_CLOSED__INCIDENT_EVIDENCE_AND_ANY_QUARANTINE_OUTPUT_PRESERVED__NO_AUTOMATIC_CLEANUP'
            stage = $Stage
            error = $_.Exception.Message
            normal_lane_invocations = $NormalLaneInvocations
            archive_root = Get-ProjectRelative $ArchiveRoot
            original_failed_run_preserved = (Test-Path -LiteralPath $FailedImportLog -PathType Leaf)
            quarantined_package_present = (Test-Path -LiteralPath $QuarantinedPackage -PathType Leaf)
            byte_archive_package_present = (Test-Path -LiteralPath $ArchivedPackage -PathType Leaf)
            automatic_cleanup = 'NOT_PERFORMED'
        }
        if (-not (Test-Path -LiteralPath $RecoveryFailure)) {
            $Failure | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $RecoveryFailure -Encoding utf8
        }
    }
    throw
}
