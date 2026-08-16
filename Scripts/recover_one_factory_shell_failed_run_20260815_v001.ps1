[CmdletBinding()]
param(
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# This is deliberately an incident-bound recovery, not a general map mover.
# It can consume only the exact failed output from run 20260815T005506Z and it
# invokes the frozen clean one-shot runner exactly once after preserving it.
$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Runner = Join-Path $Root 'Scripts\run_one_factory_shell_validation_v001.ps1'
$Builder = Join-Path $Root 'Scripts\create_one_factory_shell_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_one_factory_shell_v001.py'
$MapDirectory = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Maps'
$FailedMap = Join-Path $MapDirectory 'LB_MoorcrossWorks_OneFactory_v001.umap'
$FailedRun = Join-Path $Root 'Saved\Audits\OneFactory\v001\Runs\20260815T005506Z'
$CreateReceipt = Join-Path $Root 'Saved\Audits\OneFactory\v001\one_factory_shell_create_v001.json'
$ValidationReceipt = Join-Path $Root 'Saved\Audits\OneFactory\v001\one_factory_shell_validation_v001.json'
$QuarantineRoot = Join-Path $Root 'Saved\Quarantine\OneFactory\ShellV001'
$ArchiveRoot = Join-Path $QuarantineRoot 'Incident_20260815T005506Z'
$ArchivedRun = Join-Path $ArchiveRoot 'FailedRunEvidence'
$ArchivedMapDirectory = Join-Path $ArchiveRoot 'FailedDestinationMap'
$ArchivedMap = Join-Path $ArchivedMapDirectory 'LB_MoorcrossWorks_OneFactory_v001__FAILED__0E461BC18927B369.umap'
$PreRetryReceipt = Join-Path $ArchiveRoot 'incident_recovery_pre_retry_v001.json'
$RetrySummary = Join-Path $ArchiveRoot 'incident_recovery_retry_summary_v001.json'

$ExpectedFailedMapSha256 = '0E461BC18927B369C112BC11E36F91542F1686C4B18D3E5EBF6C0DE788BD7AC2'
$ExpectedFailedMapLength = 272679
$ExpectedBuilderSha256 = '591126B4567500EF928B9E21F825A513689714AFF7A8C5D1B441F9E92A3F1844'
$ExpectedValidatorSha256 = '072B1C58C672965BEF15CD2023D409C90FFF63937B797BBB115A2AFDB3F51D31'
$ExpectedRunnerSha256 = '0ACB872D14D9F8CDCD300986735D53FA94380B2E0371137C33A20F78B8251C4E'
$ExpectedFailedRunFiles = [ordered]@{
    'editor_build.log' = [ordered]@{
        length = 1052
        sha256 = '20C3082F4F0EAFC638C3BEE02BA9DEB1F837B2758963207C19230A1161684025'
    }
    'shell_create.log' = [ordered]@{
        length = 342196
        sha256 = '2CDC949B47D3A2615EAD791146D878B4E1F53071324F6602731CF7BDDC25C05D'
    }
}

$CriticalProtected = [ordered]@{
    'Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap' = '26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6'
    'Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap' = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'
    'Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap' = '8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F'
    'Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap' = '2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069'
}

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}

function Get-ProjectRelative([string]$Path) {
    $Full = [IO.Path]::GetFullPath($Path)
    $RootPrefix = $Root.TrimEnd('\') + '\'
    if (-not $Full.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside project root: $Full"
    }
    return $Full.Substring($RootPrefix.Length).Replace('\','/')
}

function Assert-StrictChild([string]$Path, [string]$Parent, [string]$Purpose) {
    $Full = [IO.Path]::GetFullPath($Path)
    $ParentFull = [IO.Path]::GetFullPath($Parent).TrimEnd('\')
    if (-not $Full.StartsWith($ParentFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Purpose escaped its exact parent: $Full is not below $ParentFull"
    }
}

function Assert-ExactFile([string]$Path, [long]$Length, [string]$Sha256, [string]$Purpose) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Purpose is missing: $Path"
    }
    $ActualLength = (Get-Item -LiteralPath $Path).Length
    $ActualSha256 = Get-Sha256 $Path
    if ($ActualLength -ne $Length -or $ActualSha256 -cne $Sha256) {
        throw "$Purpose drifted: length=$ActualLength sha256=$ActualSha256"
    }
}

function Get-ProtectedSnapshot {
    $Paths = New-Object 'System.Collections.Generic.List[string]'
    foreach ($Relative in $CriticalProtected.Keys) {
        $Paths.Add((Join-Path $Root $Relative.Replace('/','\')))
    }
    $ConfigRoot = Join-Path $Root 'Config'
    if (-not (Test-Path -LiteralPath $ConfigRoot -PathType Container)) {
        throw "Protected Config directory is missing: $ConfigRoot"
    }
    foreach ($Item in @(Get-ChildItem -LiteralPath $ConfigRoot -File -Recurse | Sort-Object FullName)) {
        $Paths.Add($Item.FullName)
    }
    $SaveGamesRoot = Join-Path $Root 'Saved\SaveGames'
    if (Test-Path -LiteralPath $SaveGamesRoot -PathType Container) {
        foreach ($Item in @(Get-ChildItem -LiteralPath $SaveGamesRoot -File -Recurse | Sort-Object FullName)) {
            $Paths.Add($Item.FullName)
        }
    }
    $Snapshot = [ordered]@{}
    foreach ($Path in @($Paths | Sort-Object -Unique)) {
        $Snapshot[(Get-ProjectRelative $Path)] = Get-Sha256 $Path
    }
    foreach ($Relative in $CriticalProtected.Keys) {
        if ([string]$Snapshot[$Relative] -cne [string]$CriticalProtected[$Relative]) {
            throw "Protected anchor hash drift: $Relative = $($Snapshot[$Relative])"
        }
    }
    return $Snapshot
}

function Assert-SameSnapshot([object]$Before, [object]$After, [string]$Stage) {
    if (($Before | ConvertTo-Json -Depth 4 -Compress) -cne
            ($After | ConvertTo-Json -Depth 4 -Compress)) {
        throw "$Stage changed protected Press/Body/Paint/Config/SaveGames files"
    }
}

Assert-StrictChild $FailedMap $MapDirectory 'Failed destination map'
Assert-StrictChild $ArchiveRoot $QuarantineRoot 'Incident archive'
Assert-StrictChild $ArchivedMap $ArchiveRoot 'Archived failed map'
Assert-StrictChild $ArchivedRun $ArchiveRoot 'Archived failed run'

foreach ($Required in @($Runner, $Builder, $Validator)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) {
        throw "Recovery prerequisite is missing: $Required"
    }
}
if ((Get-Sha256 $Builder) -cne $ExpectedBuilderSha256) {
    throw 'Incident recovery refused drifted One Factory builder'
}
if ((Get-Sha256 $Validator) -cne $ExpectedValidatorSha256) {
    throw 'Incident recovery refused drifted One Factory validator'
}
if ((Get-Sha256 $Runner) -cne $ExpectedRunnerSha256) {
    throw 'Incident recovery refused drifted One Factory runner'
}
if (Test-Path -LiteralPath $ArchiveRoot) {
    throw "Incident archive already exists; recovery is one-use only: $ArchiveRoot"
}
if (Test-Path -LiteralPath $CreateReceipt) {
    throw "Unexpected creation receipt exists: $CreateReceipt"
}
if (Test-Path -LiteralPath $ValidationReceipt) {
    throw "Unexpected validation receipt exists: $ValidationReceipt"
}

$LiveUnreal = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -in @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool')
})
if ($LiveUnreal.Count -ne 0) {
    throw "Close active Unreal/build processes before incident recovery: $($LiveUnreal.ProcessName -join ', ')"
}

$MapDirectoryItems = @(Get-ChildItem -LiteralPath $MapDirectory)
if ($MapDirectoryItems.Count -ne 1 -or
        $MapDirectoryItems[0].FullName -cne [IO.Path]::GetFullPath($FailedMap) -or
        $MapDirectoryItems[0].PSIsContainer) {
    throw 'Destination Maps directory is not the exact one-file failed incident state'
}
Assert-ExactFile $FailedMap $ExpectedFailedMapLength $ExpectedFailedMapSha256 'Exact failed map'

if (-not (Test-Path -LiteralPath $FailedRun -PathType Container)) {
    throw "Exact failed run is missing: $FailedRun"
}
$FailedRunItems = @(Get-ChildItem -LiteralPath $FailedRun)
if ($FailedRunItems.Count -ne $ExpectedFailedRunFiles.Count -or
        @($FailedRunItems | Where-Object { $_.PSIsContainer }).Count -ne 0 -or
        (@($FailedRunItems.Name | Sort-Object) -join '|') -cne
        (@($ExpectedFailedRunFiles.Keys | Sort-Object) -join '|')) {
    throw 'Failed run evidence is not the exact two-file incident state'
}
foreach ($Name in $ExpectedFailedRunFiles.Keys) {
    $Expected = $ExpectedFailedRunFiles[$Name]
    Assert-ExactFile (Join-Path $FailedRun $Name) ([long]$Expected.length) `
        ([string]$Expected.sha256) "Failed run evidence $Name"
}

$Before = Get-ProtectedSnapshot
$RunNamesBefore = @(
    Get-ChildItem -LiteralPath (Split-Path $FailedRun -Parent) -Directory |
        Select-Object -ExpandProperty Name | Sort-Object
)

New-Item -ItemType Directory -Path $ArchivedRun | Out-Null
New-Item -ItemType Directory -Path $ArchivedMapDirectory | Out-Null
foreach ($Name in $ExpectedFailedRunFiles.Keys) {
    Copy-Item -LiteralPath (Join-Path $FailedRun $Name) -Destination (Join-Path $ArchivedRun $Name)
    $Expected = $ExpectedFailedRunFiles[$Name]
    Assert-ExactFile (Join-Path $ArchivedRun $Name) ([long]$Expected.length) `
        ([string]$Expected.sha256) "Archived failed run evidence $Name"
}

# The exact failed destination is moved, never deleted.  If the retry fails,
# this preserved original remains available under Saved for diagnosis/recovery.
Move-Item -LiteralPath $FailedMap -Destination $ArchivedMap
if (Test-Path -LiteralPath $FailedMap) {
    throw 'Failed destination still exists after the guarded move'
}
Assert-ExactFile $ArchivedMap $ExpectedFailedMapLength $ExpectedFailedMapSha256 'Archived failed map'
foreach ($Name in $ExpectedFailedRunFiles.Keys) {
    $Expected = $ExpectedFailedRunFiles[$Name]
    Assert-ExactFile (Join-Path $FailedRun $Name) ([long]$Expected.length) `
        ([string]$Expected.sha256) "Original failed run evidence $Name"
}
Assert-SameSnapshot $Before (Get-ProtectedSnapshot) 'Incident preservation and map move'

$PreRetry = [ordered]@{
    '$schema' = 'lineboss/audit/one-factory/shell-incident-recovery-v001/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'READY__FAILED_RUN_COPIED__FAILED_DESTINATION_MOVED__RETRY_NOT_STARTED'
    incident_run = '20260815T005506Z'
    failed_map = [ordered]@{
        original_path = 'Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap'
        archived_path = Get-ProjectRelative $ArchivedMap
        length = $ExpectedFailedMapLength
        sha256 = $ExpectedFailedMapSha256
    }
    failed_run_source = Get-ProjectRelative $FailedRun
    failed_run_archive = Get-ProjectRelative $ArchivedRun
    failed_run_files = $ExpectedFailedRunFiles
    builder_sha256 = $ExpectedBuilderSha256
    validator_sha256 = $ExpectedValidatorSha256
    runner_sha256 = $ExpectedRunnerSha256
    protected_hashes = $Before
    retry_invocation_limit = 1
}
$PreRetry | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $PreRetryReceipt -Encoding utf8

# Exactly one clean one-shot invocation.  This recovery script is rendered
# unusable by the archive-exists guard before this call is reached a second time.
& $Runner -EngineRoot $EngineRoot
if ($LASTEXITCODE -ne 0) {
    throw "Frozen One Factory retry returned exit code $LASTEXITCODE"
}

$After = Get-ProtectedSnapshot
Assert-SameSnapshot $Before $After 'Incident-bound clean retry'
Assert-ExactFile $ArchivedMap $ExpectedFailedMapLength $ExpectedFailedMapSha256 'Post-retry archived failed map'
$RunNamesAfter = @(
    Get-ChildItem -LiteralPath (Split-Path $FailedRun -Parent) -Directory |
        Select-Object -ExpandProperty Name | Sort-Object
)
$NewRunNames = @($RunNamesAfter | Where-Object { $_ -notin $RunNamesBefore })
if ($NewRunNames.Count -ne 1) {
    throw "Expected exactly one new retry run directory; found $($NewRunNames -join ', ')"
}
if (-not (Test-Path -LiteralPath $FailedMap -PathType Leaf) -or
        -not (Test-Path -LiteralPath $CreateReceipt -PathType Leaf) -or
        -not (Test-Path -LiteralPath $ValidationReceipt -PathType Leaf)) {
    throw 'Clean retry returned without the map and both stable receipts'
}

$Summary = [ordered]@{
    '$schema' = 'lineboss/audit/one-factory/shell-incident-retry-summary-v001/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'PASS__FAILED_OUTPUT_PRESERVED__EXACTLY_ONE_CLEAN_RETRY_PASSED'
    archived_failed_map = [ordered]@{
        path = Get-ProjectRelative $ArchivedMap
        length = $ExpectedFailedMapLength
        sha256 = $ExpectedFailedMapSha256
    }
    preserved_failed_run_source = Get-ProjectRelative $FailedRun
    preserved_failed_run_copy = Get-ProjectRelative $ArchivedRun
    retry_run = $NewRunNames[0]
    retry_map_sha256 = Get-Sha256 $FailedMap
    create_receipt_sha256 = Get-Sha256 $CreateReceipt
    validation_receipt_sha256 = Get-Sha256 $ValidationReceipt
    protected_hashes = $After
}
$Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $RetrySummary -Encoding utf8
Write-Host 'PASS: failed One Factory output preserved and exactly one clean retry passed.'
Write-Host "Incident archive: $ArchiveRoot"
Write-Host "Retry run: $($NewRunNames[0])"
