[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('FINALIZE_EXACT_V449_RECOVERY_20260815_FROM_PRESERVED_MANIFESTS')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$RecoveryRoot = Join-Path $Root 'Saved\Recovery\OneFactory\DetailedPressV449OwnedPromotion\20260815T065345Z-8cba4b66'
$FailedReceipt = Join-Path $RecoveryRoot 'recovery_receipt_v001.json'
$BeforeManifest = Join-Path $RecoveryRoot 'out_of_destination_immutable_before_v001.json'
$AfterManifest = Join-Path $RecoveryRoot 'out_of_destination_immutable_after_v001.json'
$SourceBeforeManifest = Join-Path $RecoveryRoot 'complete_source_before_v001.json'
$SourceFinalManifest = Join-Path $RecoveryRoot 'complete_source_final_v001.json'
$FinalReceipt = Join-Path $RecoveryRoot 'recovery_finalization_receipt_v001.json'
$Destination = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Native\Press\DetailedPresentation_v001'
$Quarantine = Join-Path $RecoveryRoot 'Quarantine\DetailedPresentation_v001'
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
        throw "Required finalization file missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Get-SourceRows {
    $Rows = foreach ($File in @(Get-ChildItem -LiteralPath (Join-Path $Root 'Source') -Recurse -File |
            Sort-Object FullName)) {
        [ordered]@{
            path = [IO.Path]::GetRelativePath($Root, $File.FullName).Replace('\','/')
            size_bytes = [int64]$File.Length
            sha256 = Get-Sha256 $File.FullName
        }
    }
    return @($Rows)
}

function Get-SourceDrift([object[]]$Before, [object[]]$After) {
    $BeforeByPath = @{}
    $AfterByPath = @{}
    foreach ($Row in $Before) { $BeforeByPath[[string]$Row.path] = $Row }
    foreach ($Row in $After) { $AfterByPath[[string]$Row.path] = $Row }
    $Drift = foreach ($Path in @($BeforeByPath.Keys + $AfterByPath.Keys | Sort-Object -Unique)) {
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

function Assert-Pinned([System.Collections.IDictionary]$Expected, [string]$Label) {
    $Rows = [ordered]@{}
    foreach ($Relative in $Expected.Keys) {
        $Actual = Get-Sha256 (Join-Path $Root $Relative.Replace('/','\'))
        if ($Actual -cne [string]$Expected[$Relative]) {
            throw "$Label hash drift: $Relative expected=$($Expected[$Relative]) actual=$Actual"
        }
        $Rows[$Relative] = $Actual
    }
    return $Rows
}

function Write-Json([string]$Path, [object]$Payload, [int]$Depth = 12) {
    if (Test-Path -LiteralPath $Path) { throw "Finalization evidence exists: $Path" }
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, ($Payload | ConvertTo-Json -Depth $Depth) + "`n", $Utf8NoBom)
}

foreach ($Path in @($RecoveryRoot,$FailedReceipt,$BeforeManifest,$AfterManifest,$SourceBeforeManifest,$Python,$Contract)) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "Finalization input missing: $Path" }
}
if (Test-Path -LiteralPath $Destination) { throw 'Original failed namespace unexpectedly reappeared' }
if (-not (Test-Path -LiteralPath $Quarantine -PathType Container)) { throw 'Exact quarantine missing' }
if (@(Get-ChildItem -LiteralPath $Quarantine -Recurse -File).Count -ne 0) {
    throw 'Quarantine no longer proves the exact empty post-rollback namespace'
}
$QuarantineDirectories = @(Get-ChildItem -LiteralPath $Quarantine -Recurse -Directory |
    ForEach-Object { [IO.Path]::GetRelativePath($Quarantine, $_.FullName).Replace('\','/') })
if ($QuarantineDirectories.Count -ne 1 -or $QuarantineDirectories[0] -cne 'Materials') {
    throw 'Quarantine directory inventory drifted from exact empty namespace'
}

$Failed = Get-Content -Raw -LiteralPath $FailedReceipt | ConvertFrom-Json
if ([string]$Failed.status -cne 'FAIL_CLOSED__DETAILED_PRESS_V449_FAILED_PROMOTION_RECOVERY_V001' `
        -or -not [bool]$Failed.original_namespace_absent `
        -or [int]$Failed.partial_destination_before.file_count -ne 0 `
        -or [int]$Failed.partial_destination_before.directory_count -ne 1) {
    throw 'Preserved failed recovery receipt no longer identifies the exact moved empty namespace'
}
$BeforeHash = Get-Sha256 $BeforeManifest
$AfterHash = Get-Sha256 $AfterManifest
if ($BeforeHash -cne '2B1F553CEA8A0CE64CD2ECCF8FC0EDF6C6D30839E8D672B9159B14D9F6B68B92' `
        -or $AfterHash -cne $BeforeHash `
        -or [int]$Failed.out_of_destination_immutable_before.file_count -ne 15352 `
        -or [int]$Failed.out_of_destination_immutable_after.file_count -ne 15352) {
    throw 'Full out-of-destination immutable before/after manifests are not byte-identical'
}

$SourceBefore = @(Get-Content -Raw -LiteralPath $SourceBeforeManifest | ConvertFrom-Json)
$SourceFinal = @(Get-SourceRows)
Write-Json $SourceFinalManifest $SourceFinal 6
$SourceDrift = @(Get-SourceDrift $SourceBefore $SourceFinal)
$Unauthorized = @($SourceDrift | Where-Object { -not $_.authorized_concurrent_operations_drift })
if ($Unauthorized.Count -gt 0) {
    throw "Unauthorized Source drift since recovery start: $($Unauthorized.path -join ', ')"
}

$Protected = Assert-Pinned $ProtectedMapHashes 'Protected map'
$PressSource = Assert-Pinned $PressPresentationHashes 'Press presentation Source'
$Process = Start-Process -FilePath $Python -ArgumentList @(
    '-B',('"{0}"' -f $Contract),'--project-root',('"{0}"' -f $Root),
    '--require-destination-absent'
) -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $ContractOutput `
  -RedirectStandardError $ContractError -Wait -PassThru
if ($Process.ExitCode -ne 0) {
    throw "Post-recovery exact source contract failed: exit=$($Process.ExitCode)"
}

$Payload = [ordered]@{
    '$schema' = 'cairnwell/one-factory/detailed-press/v449-recovery-finalization/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'PASS__EXACT_EMPTY_FAILED_NAMESPACE_RECOVERABLY_QUARANTINED__15352_OUT_OF_DESTINATION_FILES_BYTE_IDENTICAL__SOURCE_DRIFT_ALLOWLISTED'
    acknowledgement = $Acknowledgement
    failed_recovery_receipt = $FailedReceipt
    failed_recovery_receipt_sha256 = Get-Sha256 $FailedReceipt
    original_namespace_absent = $true
    quarantine = $Quarantine
    quarantine_file_count = 0
    quarantine_directories = $QuarantineDirectories
    out_of_destination_before_manifest = $BeforeManifest
    out_of_destination_after_manifest = $AfterManifest
    out_of_destination_manifest_sha256 = $BeforeHash
    out_of_destination_file_count = 15352
    complete_source_before_manifest = $SourceBeforeManifest
    complete_source_before_manifest_sha256 = Get-Sha256 $SourceBeforeManifest
    complete_source_final_manifest = $SourceFinalManifest
    complete_source_final_manifest_sha256 = Get-Sha256 $SourceFinalManifest
    complete_source_final_file_count = $SourceFinal.Count
    authorized_concurrent_source_drift = $SourceDrift
    protected_map_hashes = $Protected
    press_presentation_source_hashes = $PressSource
    post_recovery_contract_stdout = $ContractOutput
    post_recovery_contract_stdout_sha256 = Get-Sha256 $ContractOutput
    post_recovery_contract_stderr_sha256 = Get-Sha256 $ContractError
    delete_performed = $false
    ue_or_ubt_invoked = $false
}
Write-Json $FinalReceipt $Payload 16
Write-Output "LINE_BOSS_DETAILED_PRESS_V449_RECOVERY_FINALIZATION=$FinalReceipt"
