[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('RECOVER_EXACT_EMPTY_V449_OWNED_NAMESPACE_AFTER_FAIL_CLOSED_ROLLBACK')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Destination = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Native\Press\DetailedPresentation_v001'
$FailedEvidence = Join-Path $Root 'Saved\Audits\OneFactory\DetailedPressPresentation_v001\PromotionLane_v001'
$BuildReceipt = Join-Path $Root 'Saved\Audits\OneFactory\DetailedPressPresentation_v001\v449_owned_promotion_build_v001.json'
$ValidationReceipt = Join-Path $Root 'Saved\Audits\OneFactory\DetailedPressPresentation_v001\v449_owned_promotion_fresh_load_validation_v001.json'
$RecoveryParent = Join-Path $Root 'Saved\Recovery\OneFactory\DetailedPressV449OwnedPromotion'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RecoveryRoot = Join-Path $RecoveryParent $Stamp
$EvidenceArchive = Join-Path $RecoveryRoot 'FailedRunEvidenceArchive'
$QuarantineParent = Join-Path $RecoveryRoot 'Quarantine'
$QuarantineDestination = Join-Path $QuarantineParent 'DetailedPresentation_v001'
$Receipt = Join-Path $RecoveryRoot 'recovery_receipt_v001.json'
$Python = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Contract = Join-Path $Root 'Scripts\one_factory_detailed_press_v449_promotion_contract.py'
$ContractOutput = Join-Path $RecoveryRoot 'post_recovery_exact_source_contract.stdout.log'
$ContractError = Join-Path $RecoveryRoot 'post_recovery_exact_source_contract.stderr.log'

$AllowedConcurrentSourceDrift = @(
    'Source/LineBossCarFactory/LBOneFactoryRuntimeCoordinator.h',
    'Source/LineBossCarFactory/LBOneFactoryRuntimeCoordinator.cpp',
    'Source/LineBossCarFactory/LBOneFactoryRuntimeCoordinatorTests.cpp',
    'Source/LineBossCarFactory/LBOneFactoryGameMode.h',
    'Source/LineBossCarFactory/LBOneFactoryGameMode.cpp',
    'Source/LineBossCarFactory/LBOneFactoryGameModeTests.cpp',
    'Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.h',
    'Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.cpp',
    'Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystemTests.cpp',
    'Source/LineBossCarFactory/LBOneFactoryOperationsSubsystem.h',
    'Source/LineBossCarFactory/LBOneFactoryOperationsSubsystem.cpp',
    'Source/LineBossCarFactory/LBOneFactoryOperationsSubsystemTests.cpp',
    'Source/LineBossCarFactory/LBOneFactorySaveSubsystem.h',
    'Source/LineBossCarFactory/LBOneFactorySaveSubsystem.cpp',
    'Source/LineBossCarFactory/LBOneFactorySaveSubsystemTests.cpp',
    'Source/LineBossCarFactory/LBControlRoomHUD.cpp'
)

$PressPresentationHashes = [ordered]@{
    'Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.h' = '293FE7E78DAAD0BA46D6379034B64D43A85C1106C4FD8D44A5075B5D7E43A63B'
    'Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp' = 'AC40D7AFCC00A285DCC6D9C35D2A007A52CE7C70C738512C917E421FCD6BA062'
    'Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActorTests.cpp' = 'F183BDFC11F446B01DC5E873D9EB4E4DD78E591EEC012820029FEECC5C99C538'
}

$ProtectedMapHashes = [ordered]@{
    'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap' = '5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
    'Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap' = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'
    'Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap' = '26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6'
}

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Get-Relative([string]$Path) {
    return [IO.Path]::GetRelativePath($Root, $Path).Replace('\','/')
}

function Get-InventoryRows([string[]]$Roots, [string]$ExcludedPrefix = '') {
    $Files = @()
    foreach ($InventoryRoot in $Roots) {
        if (Test-Path -LiteralPath $InventoryRoot -PathType Leaf) {
            $Files += Get-Item -LiteralPath $InventoryRoot
        }
        elseif (Test-Path -LiteralPath $InventoryRoot -PathType Container) {
            $Files += Get-ChildItem -LiteralPath $InventoryRoot -Recurse -File
        }
    }
    $Rows = foreach ($File in @($Files | Sort-Object FullName -Unique)) {
        if ($ExcludedPrefix -and $File.FullName.StartsWith(
                $ExcludedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        [ordered]@{
            path = Get-Relative $File.FullName
            size_bytes = [int64]$File.Length
            sha256 = Get-Sha256 $File.FullName
        }
    }
    return @($Rows)
}

function Write-Json([string]$Path, [object]$Payload, [int]$Depth = 10) {
    if (Test-Path -LiteralPath $Path) {
        throw "Refusing to overwrite recovery evidence: $Path"
    }
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText(
        $Path,
        ($Payload | ConvertTo-Json -Depth $Depth) + "`n",
        $Utf8NoBom
    )
}

function Get-RowSignature([object[]]$Rows) {
    return @($Rows | ForEach-Object {
        '{0}|{1}|{2}' -f $_.path, $_.size_bytes, $_.sha256
    })
}

function Get-SourceDrift([object[]]$Before, [object[]]$After) {
    $BeforeByPath = @{}
    $AfterByPath = @{}
    foreach ($Row in $Before) { $BeforeByPath[[string]$Row.path] = $Row }
    foreach ($Row in $After) { $AfterByPath[[string]$Row.path] = $Row }
    $Paths = @($BeforeByPath.Keys + $AfterByPath.Keys | Sort-Object -Unique)
    $Drift = foreach ($Path in $Paths) {
        $BeforeRow = $BeforeByPath[$Path]
        $AfterRow = $AfterByPath[$Path]
        $BeforeHash = if ($BeforeRow) { [string]$BeforeRow.sha256 } else { '' }
        $AfterHash = if ($AfterRow) { [string]$AfterRow.sha256 } else { '' }
        $BeforeSize = if ($BeforeRow) { [int64]$BeforeRow.size_bytes } else { -1 }
        $AfterSize = if ($AfterRow) { [int64]$AfterRow.size_bytes } else { -1 }
        if ($BeforeHash -cne $AfterHash -or $BeforeSize -ne $AfterSize) {
            [ordered]@{
                path = $Path
                before_sha256 = $BeforeHash
                after_sha256 = $AfterHash
                before_size_bytes = $BeforeSize
                after_size_bytes = $AfterSize
                authorized_concurrent_operations_drift = $AllowedConcurrentSourceDrift -ccontains $Path
            }
        }
    }
    return @($Drift)
}

function Assert-PinnedHashes([System.Collections.IDictionary]$Expected, [string]$Label) {
    $Rows = [ordered]@{}
    foreach ($Relative in $Expected.Keys) {
        $Actual = Get-Sha256 (Join-Path $Root ($Relative.Replace('/','\')))
        if ($Actual -cne [string]$Expected[$Relative]) {
            throw "$Label hash drift: $Relative expected=$($Expected[$Relative]) actual=$Actual"
        }
        $Rows[$Relative] = $Actual
    }
    return $Rows
}

function Assert-NoUnrealOrBuildProcesses {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -gt 0) {
        throw "Recovery requires no active Unreal/build process: $(($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', ')"
    }
}

if ((Resolve-Path -LiteralPath $Root).Path -cne $Root) {
    throw 'Exact project-root identity drift'
}
foreach ($Path in @($Python,$Contract,$FailedEvidence)) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "Recovery input missing: $Path" }
}
if (-not (Test-Path -LiteralPath $Destination -PathType Container)) {
    throw "Exact failed destination directory is missing: $Destination"
}
$ResolvedDestination = (Resolve-Path -LiteralPath $Destination).Path
if ($ResolvedDestination -cne $Destination) {
    throw "Failed destination identity drift: $ResolvedDestination"
}
if ((Test-Path -LiteralPath $BuildReceipt) -or (Test-Path -LiteralPath $ValidationReceipt)) {
    throw 'Recovery is only valid before any successful build/validation receipt exists'
}
if (Test-Path -LiteralPath $RecoveryRoot) {
    throw "Unique recovery root already exists: $RecoveryRoot"
}
Assert-NoUnrealOrBuildProcesses

New-Item -ItemType Directory -Path $RecoveryRoot | Out-Null
New-Item -ItemType Directory -Path $EvidenceArchive | Out-Null
$Summary = [ordered]@{
    '$schema' = 'cairnwell/one-factory/detailed-press/v449-failed-promotion-recovery/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'IN_PROGRESS'
    acknowledgement = $Acknowledgement
    failed_destination = $Destination
    quarantine_destination = $QuarantineDestination
    failed_run_evidence = $null
    partial_destination_before = $null
    quarantine_after = $null
    out_of_destination_immutable_before = $null
    out_of_destination_immutable_after = $null
    complete_source_before = $null
    complete_source_after = $null
    authorized_concurrent_source_drift = @()
    protected_map_hashes = $null
    press_presentation_source_hashes = $null
    post_recovery_contract = $null
    delete_performed = $false
    original_namespace_absent = $false
    error = $null
}

try {
    $FailedRows = @(Get-InventoryRows @($FailedEvidence))
    $FailedManifest = Join-Path $RecoveryRoot 'failed_run_evidence_manifest_v001.json'
    Write-Json $FailedManifest $FailedRows 6
    [int64]$FailedTotalBytes = 0
    foreach ($Row in $FailedRows) {
        $FailedTotalBytes += [int64]$Row['size_bytes']
        $Source = Join-Path $Root ([string]$Row.path).Replace('/','\')
        $RelativeToEvidence = [IO.Path]::GetRelativePath($FailedEvidence, $Source)
        $Copy = Join-Path $EvidenceArchive $RelativeToEvidence
        $CopyParent = Split-Path -Parent $Copy
        if (-not (Test-Path -LiteralPath $CopyParent -PathType Container)) {
            New-Item -ItemType Directory -Path $CopyParent | Out-Null
        }
        if (Test-Path -LiteralPath $Copy) { throw "Evidence archive overwrite: $Copy" }
        Copy-Item -LiteralPath $Source -Destination $Copy
        if ((Get-Sha256 $Copy) -cne [string]$Row.sha256) {
            throw "Failed-run evidence archive hash mismatch: $Copy"
        }
    }
    $Summary.failed_run_evidence = [ordered]@{
        source_root = $FailedEvidence
        archive_root = $EvidenceArchive
        file_count = $FailedRows.Count
        total_bytes = $FailedTotalBytes
        manifest = $FailedManifest
        manifest_sha256 = Get-Sha256 $FailedManifest
    }

    $PartialRows = @(Get-InventoryRows @($Destination))
    $PartialDirectories = @(Get-ChildItem -LiteralPath $Destination -Recurse -Directory |
        Sort-Object FullName | ForEach-Object {
            [IO.Path]::GetRelativePath($Destination, $_.FullName).Replace('\','/')
        })
    $PartialManifest = Join-Path $RecoveryRoot 'partial_destination_before_v001.json'
    Write-Json $PartialManifest ([ordered]@{
        root = $Destination
        file_count = $PartialRows.Count
        directories = $PartialDirectories
        files = $PartialRows
    }) 8
    $Summary.partial_destination_before = [ordered]@{
        file_count = $PartialRows.Count
        directory_count = $PartialDirectories.Count
        manifest = $PartialManifest
        manifest_sha256 = Get-Sha256 $PartialManifest
    }

    $SourceBefore = @(Get-InventoryRows @((Join-Path $Root 'Source')))
    $SourceBeforePath = Join-Path $RecoveryRoot 'complete_source_before_v001.json'
    Write-Json $SourceBeforePath $SourceBefore 6
    $Summary.complete_source_before = [ordered]@{
        file_count = $SourceBefore.Count
        manifest = $SourceBeforePath
        manifest_sha256 = Get-Sha256 $SourceBeforePath
    }

    $DestinationPrefix = $Destination + '\'
    $ImmutableRoots = @(
        (Join-Path $Root 'Content'),
        (Join-Path $Root 'Config'),
        (Join-Path $Root 'Saved\SaveGames'),
        (Join-Path $Root 'LineBossCarFactory.uproject')
    )
    $ImmutableBefore = @(Get-InventoryRows $ImmutableRoots $DestinationPrefix)
    foreach ($PressRelative in $PressPresentationHashes.Keys) {
        $PressPath = Join-Path $Root $PressRelative.Replace('/','\')
        $ImmutableBefore += [ordered]@{
            path = $PressRelative
            size_bytes = [int64](Get-Item -LiteralPath $PressPath).Length
            sha256 = Get-Sha256 $PressPath
        }
    }
    $ImmutableBefore = @($ImmutableBefore | Sort-Object path)
    $ImmutableBeforePath = Join-Path $RecoveryRoot 'out_of_destination_immutable_before_v001.json'
    Write-Json $ImmutableBeforePath $ImmutableBefore 6
    $Summary.out_of_destination_immutable_before = [ordered]@{
        file_count = $ImmutableBefore.Count
        manifest = $ImmutableBeforePath
        manifest_sha256 = Get-Sha256 $ImmutableBeforePath
    }
    $Summary.protected_map_hashes = Assert-PinnedHashes $ProtectedMapHashes 'Protected map'
    $Summary.press_presentation_source_hashes = Assert-PinnedHashes $PressPresentationHashes 'Press presentation Source'

    New-Item -ItemType Directory -Path $QuarantineParent | Out-Null
    if (Test-Path -LiteralPath $QuarantineDestination) {
        throw "Refusing to overwrite quarantine destination: $QuarantineDestination"
    }
    $ResolvedRecoveryParent = (Resolve-Path -LiteralPath $RecoveryParent).Path
    if (-not $QuarantineDestination.StartsWith(
            $ResolvedRecoveryParent + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Quarantine target escapes exact recovery parent: $QuarantineDestination"
    }
    Move-Item -LiteralPath $ResolvedDestination -Destination $QuarantineDestination
    if (Test-Path -LiteralPath $Destination) {
        throw 'Original failed destination still exists after recoverable move'
    }
    if (-not (Test-Path -LiteralPath $QuarantineDestination -PathType Container)) {
        throw 'Recoverable quarantine destination missing after move'
    }
    $QuarantineRows = @(Get-InventoryRows @($QuarantineDestination))
    if ($PartialRows.Count -ne $QuarantineRows.Count -or (
            $PartialRows.Count -gt 0 -and
            @(Compare-Object (Get-RowSignature $PartialRows)
                (Get-RowSignature $QuarantineRows)).Count -ne 0)) {
        throw 'Quarantined package inventory differs from failed destination'
    }
    $QuarantineDirectories = @(Get-ChildItem -LiteralPath $QuarantineDestination -Recurse -Directory |
        Sort-Object FullName | ForEach-Object {
            [IO.Path]::GetRelativePath($QuarantineDestination, $_.FullName).Replace('\','/')
        })
    if (@(Compare-Object $PartialDirectories $QuarantineDirectories).Count -ne 0) {
        throw 'Quarantined directory inventory differs from failed destination'
    }
    $Summary.quarantine_after = [ordered]@{
        file_count = $QuarantineRows.Count
        directories = $QuarantineDirectories
    }
    $Summary.original_namespace_absent = $true

    $ImmutableAfter = @(Get-InventoryRows $ImmutableRoots $DestinationPrefix)
    foreach ($PressRelative in $PressPresentationHashes.Keys) {
        $PressPath = Join-Path $Root $PressRelative.Replace('/','\')
        $ImmutableAfter += [ordered]@{
            path = $PressRelative
            size_bytes = [int64](Get-Item -LiteralPath $PressPath).Length
            sha256 = Get-Sha256 $PressPath
        }
    }
    $ImmutableAfter = @($ImmutableAfter | Sort-Object path)
    $ImmutableAfterPath = Join-Path $RecoveryRoot 'out_of_destination_immutable_after_v001.json'
    Write-Json $ImmutableAfterPath $ImmutableAfter 6
    $Summary.out_of_destination_immutable_after = [ordered]@{
        file_count = $ImmutableAfter.Count
        manifest = $ImmutableAfterPath
        manifest_sha256 = Get-Sha256 $ImmutableAfterPath
    }
    $ImmutableBeforeSignatures = @(Get-RowSignature -Rows $ImmutableBefore)
    $ImmutableAfterSignatures = @(Get-RowSignature -Rows $ImmutableAfter)
    if (@(Compare-Object -ReferenceObject $ImmutableBeforeSignatures `
            -DifferenceObject $ImmutableAfterSignatures).Count -ne 0) {
        throw 'Out-of-destination Content/Config/SaveGames/uproject/Press Source changed during recovery'
    }

    $SourceAfter = @(Get-InventoryRows @((Join-Path $Root 'Source')))
    $SourceAfterPath = Join-Path $RecoveryRoot 'complete_source_after_v001.json'
    Write-Json $SourceAfterPath $SourceAfter 6
    $Summary.complete_source_after = [ordered]@{
        file_count = $SourceAfter.Count
        manifest = $SourceAfterPath
        manifest_sha256 = Get-Sha256 $SourceAfterPath
    }
    $SourceDrift = @(Get-SourceDrift $SourceBefore $SourceAfter)
    $Unauthorized = @($SourceDrift | Where-Object {
        -not $_.authorized_concurrent_operations_drift
    })
    if ($Unauthorized.Count -gt 0) {
        throw "Unauthorized concurrent Source drift: $($Unauthorized.path -join ', ')"
    }
    $Summary.authorized_concurrent_source_drift = $SourceDrift
    $Summary.protected_map_hashes = Assert-PinnedHashes $ProtectedMapHashes 'Protected map after recovery'
    $Summary.press_presentation_source_hashes = Assert-PinnedHashes $PressPresentationHashes 'Press presentation Source after recovery'

    $Process = Start-Process -FilePath $Python -ArgumentList @(
        '-B',('"{0}"' -f $Contract),'--project-root',('"{0}"' -f $Root),
        '--require-destination-absent'
    ) -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $ContractOutput `
      -RedirectStandardError $ContractError -Wait -PassThru
    if ($Process.ExitCode -ne 0) {
        throw "Post-recovery exact source contract failed: exit=$($Process.ExitCode)"
    }
    $Summary.post_recovery_contract = [ordered]@{
        exit_code = [int]$Process.ExitCode
        stdout = $ContractOutput
        stdout_sha256 = Get-Sha256 $ContractOutput
        stderr = $ContractError
        stderr_sha256 = Get-Sha256 $ContractError
    }
    $Summary.status = 'PASS__FAILED_V449_OWNED_NAMESPACE_EXACTLY_INVENTORIED_AND_RECOVERABLY_QUARANTINED__ORIGINAL_ABSENT'
}
catch {
    $Summary.status = 'FAIL_CLOSED__DETAILED_PRESS_V449_FAILED_PROMOTION_RECOVERY_V001'
    $Summary.error = $_.Exception.Message
    throw
}
finally {
    $Summary.generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    Write-Json $Receipt $Summary 16
    Write-Output "LINE_BOSS_DETAILED_PRESS_V449_RECOVERY_RECEIPT=$Receipt"
}
