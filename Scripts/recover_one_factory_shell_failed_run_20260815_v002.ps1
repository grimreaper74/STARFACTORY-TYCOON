[CmdletBinding()]
param(
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Incident v002 can consume only the exact second failed output.  It also
# proves that incident v001 was already preserved and consumed before invoking
# the newly frozen clean runner exactly once.
$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Runner = Join-Path $Root 'Scripts\run_one_factory_shell_validation_v001.ps1'
$Builder = Join-Path $Root 'Scripts\create_one_factory_shell_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_one_factory_shell_v001.py'
$HistoricalRecovery = Join-Path $Root 'Scripts\recover_one_factory_shell_failed_run_20260815_v001.ps1'
$MapDirectory = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Maps'
$FailedMap = Join-Path $MapDirectory 'LB_MoorcrossWorks_OneFactory_v001.umap'
$RunsRoot = Join-Path $Root 'Saved\Audits\OneFactory\v001\Runs'
$FailedRun = Join-Path $RunsRoot '20260815T011006Z'
$CreateReceipt = Join-Path $Root 'Saved\Audits\OneFactory\v001\one_factory_shell_create_v001.json'
$ValidationReceipt = Join-Path $Root 'Saved\Audits\OneFactory\v001\one_factory_shell_validation_v001.json'
$QuarantineRoot = Join-Path $Root 'Saved\Quarantine\OneFactory\ShellV001'
$PriorArchive = Join-Path $QuarantineRoot 'Incident_20260815T005506Z'
$ArchiveRoot = Join-Path $QuarantineRoot 'Incident_20260815T011006Z'
$ArchivedRun = Join-Path $ArchiveRoot 'FailedRunEvidence'
$ArchivedMapDirectory = Join-Path $ArchiveRoot 'FailedDestinationMap'
$ArchivedMap = Join-Path $ArchivedMapDirectory 'LB_MoorcrossWorks_OneFactory_v001__FAILED__44E082B43719CA8B.umap'
$PreRetryReceipt = Join-Path $ArchiveRoot 'incident_recovery_pre_retry_v002.json'
$RetrySummary = Join-Path $ArchiveRoot 'incident_recovery_retry_summary_v002.json'

$ExpectedFailedMapSha256 = '44E082B43719CA8B44E453ACBC9BF9BF018572102DABAA26D2EDF93E9B6A5B52'
$ExpectedFailedMapLength = 272679
$ExpectedBuilderSha256 = '4EE0A437A9BCC3A5431C39B2D27BB05067FA74F1A6A586B5C2DF05E412131728'
$ExpectedValidatorSha256 = '2043ED396DFD366CB857F208A38054EE9CCE4906A04EA53C4ABD86ADF1CB5E61'
$ExpectedRunnerSha256 = '1A19CF7E4FE1DDB1F150CD3AC96382D8AA2FEB097C3FDC20E184A739855DDF5F'
$ExpectedHistoricalRecoverySha256 = '654EC6892C474D9934B196C6C2DED0A3508802AECF7CB55497D92AC5C932CB46'
$ExpectedFailedRunFiles = [ordered]@{
    'editor_build.log' = [ordered]@{
        length = 22518
        sha256 = 'DBCFEEB71A0F587BECA8BAE5B68DE0593BD4C21AE987CDE5D7615A83876681EA'
    }
    'shell_create.log' = [ordered]@{
        length = 684810
        sha256 = 'A9FA2E2967355964C823A5BCA24F085C73624C5A3FE4C25B3D8328DAB02A254A'
    }
}
$ExpectedPriorArchiveFiles = [ordered]@{
    'incident_recovery_pre_retry_v001.json' = [ordered]@{
        length = 3859
        sha256 = '903179DAA517624577A6A6AFF014100B9E4459811D2B9E7FE6E095E5FD4A718F'
    }
    'FailedDestinationMap/LB_MoorcrossWorks_OneFactory_v001__FAILED__0E461BC18927B369.umap' = [ordered]@{
        length = 272679
        sha256 = '0E461BC18927B369C112BC11E36F91542F1686C4B18D3E5EBF6C0DE788BD7AC2'
    }
    'FailedRunEvidence/editor_build.log' = [ordered]@{
        length = 1052
        sha256 = '20C3082F4F0EAFC638C3BEE02BA9DEB1F837B2758963207C19230A1161684025'
    }
    'FailedRunEvidence/shell_create.log' = [ordered]@{
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
    $Prefix = $Root.TrimEnd('\') + '\'
    if (-not $Full.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside project root: $Full"
    }
    return $Full.Substring($Prefix.Length).Replace('\','/')
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
    $Item = Get-Item -LiteralPath $Path
    $ActualSha256 = Get-Sha256 $Path
    if ($Item.Length -ne $Length -or $ActualSha256 -cne $Sha256) {
        throw "$Purpose drifted: length=$($Item.Length) sha256=$ActualSha256"
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

Assert-StrictChild $FailedMap $MapDirectory 'Second failed destination map'
Assert-StrictChild $PriorArchive $QuarantineRoot 'Prior incident archive'
Assert-StrictChild $ArchiveRoot $QuarantineRoot 'Second incident archive'
Assert-StrictChild $ArchivedMap $ArchiveRoot 'Archived second failed map'
Assert-StrictChild $ArchivedRun $ArchiveRoot 'Archived second failed run'

foreach ($Required in @($Runner, $Builder, $Validator, $HistoricalRecovery)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) {
        throw "Recovery prerequisite is missing: $Required"
    }
}
if ((Get-Sha256 $Builder) -cne $ExpectedBuilderSha256) {
    throw 'Incident v002 refused drifted One Factory builder'
}
if ((Get-Sha256 $Validator) -cne $ExpectedValidatorSha256) {
    throw 'Incident v002 refused drifted One Factory validator'
}
if ((Get-Sha256 $Runner) -cne $ExpectedRunnerSha256) {
    throw 'Incident v002 refused drifted One Factory runner'
}
if ((Get-Sha256 $HistoricalRecovery) -cne $ExpectedHistoricalRecoverySha256) {
    throw 'Incident v002 refused drifted historical v001 recovery evidence'
}
if (Test-Path -LiteralPath $ArchiveRoot) {
    throw "Second incident archive already exists; recovery is one-use only: $ArchiveRoot"
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
    throw "Close active Unreal/build processes before incident v002 recovery: $($LiveUnreal.ProcessName -join ', ')"
}

if (-not (Test-Path -LiteralPath $PriorArchive -PathType Container)) {
    throw 'Prior incident archive is missing; v001 recovery was not preserved'
}
$PriorFiles = @(Get-ChildItem -LiteralPath $PriorArchive -File -Recurse)
$PriorDirectories = @(Get-ChildItem -LiteralPath $PriorArchive -Directory -Recurse)
$PriorRelative = @($PriorFiles | ForEach-Object {
    $_.FullName.Substring($PriorArchive.TrimEnd('\').Length + 1).Replace('\','/')
} | Sort-Object)
$PriorDirectoryRelative = @($PriorDirectories | ForEach-Object {
    $_.FullName.Substring($PriorArchive.TrimEnd('\').Length + 1).Replace('\','/')
} | Sort-Object)
if ($PriorDirectories.Count -ne 2 -or
        ($PriorDirectoryRelative -join '|') -cne
        'FailedDestinationMap|FailedRunEvidence' -or
        $PriorFiles.Count -ne $ExpectedPriorArchiveFiles.Count -or
        ($PriorRelative -join '|') -cne
        (@($ExpectedPriorArchiveFiles.Keys | Sort-Object) -join '|')) {
    throw 'Prior v001 incident archive inventory drifted or contains a retry summary'
}
foreach ($Relative in $ExpectedPriorArchiveFiles.Keys) {
    $Expected = $ExpectedPriorArchiveFiles[$Relative]
    Assert-ExactFile (Join-Path $PriorArchive $Relative.Replace('/','\')) `
        ([long]$Expected.length) ([string]$Expected.sha256) "Prior archive $Relative"
}

$MapDirectoryItems = @(Get-ChildItem -LiteralPath $MapDirectory)
if ($MapDirectoryItems.Count -ne 1 -or
        $MapDirectoryItems[0].FullName -cne [IO.Path]::GetFullPath($FailedMap) -or
        $MapDirectoryItems[0].PSIsContainer) {
    throw 'Destination Maps directory is not the exact one-file attempt-two state'
}
Assert-ExactFile $FailedMap $ExpectedFailedMapLength $ExpectedFailedMapSha256 'Exact second failed map'

if (-not (Test-Path -LiteralPath $FailedRun -PathType Container)) {
    throw "Exact second failed run is missing: $FailedRun"
}
$FailedRunItems = @(Get-ChildItem -LiteralPath $FailedRun)
if ($FailedRunItems.Count -ne $ExpectedFailedRunFiles.Count -or
        @($FailedRunItems | Where-Object { $_.PSIsContainer }).Count -ne 0 -or
        (@($FailedRunItems.Name | Sort-Object) -join '|') -cne
        (@($ExpectedFailedRunFiles.Keys | Sort-Object) -join '|')) {
    throw 'Second failed run evidence is not the exact two-file incident state'
}
foreach ($Name in $ExpectedFailedRunFiles.Keys) {
    $Expected = $ExpectedFailedRunFiles[$Name]
    Assert-ExactFile (Join-Path $FailedRun $Name) ([long]$Expected.length) `
        ([string]$Expected.sha256) "Second failed run evidence $Name"
}

$Before = Get-ProtectedSnapshot
$RunNamesBefore = @(
    Get-ChildItem -LiteralPath $RunsRoot -Directory |
        Select-Object -ExpandProperty Name | Sort-Object
)

New-Item -ItemType Directory -Path $ArchivedRun | Out-Null
New-Item -ItemType Directory -Path $ArchivedMapDirectory | Out-Null
foreach ($Name in $ExpectedFailedRunFiles.Keys) {
    Copy-Item -LiteralPath (Join-Path $FailedRun $Name) -Destination (Join-Path $ArchivedRun $Name)
    $Expected = $ExpectedFailedRunFiles[$Name]
    Assert-ExactFile (Join-Path $ArchivedRun $Name) ([long]$Expected.length) `
        ([string]$Expected.sha256) "Archived second failed run evidence $Name"
}

Move-Item -LiteralPath $FailedMap -Destination $ArchivedMap
if (Test-Path -LiteralPath $FailedMap) {
    throw 'Second failed destination still exists after the guarded move'
}
Assert-ExactFile $ArchivedMap $ExpectedFailedMapLength $ExpectedFailedMapSha256 'Archived second failed map'
foreach ($Name in $ExpectedFailedRunFiles.Keys) {
    $Expected = $ExpectedFailedRunFiles[$Name]
    Assert-ExactFile (Join-Path $FailedRun $Name) ([long]$Expected.length) `
        ([string]$Expected.sha256) "Original second failed run evidence $Name"
}
Assert-SameSnapshot $Before (Get-ProtectedSnapshot) 'Incident v002 preservation and map move'

$PreRetry = [ordered]@{
    '$schema' = 'lineboss/audit/one-factory/shell-incident-recovery-v002/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'READY__PRIOR_INCIDENT_VERIFIED__SECOND_FAILED_RUN_COPIED__SECOND_DESTINATION_MOVED__RETRY_NOT_STARTED'
    incident_run = '20260815T011006Z'
    prior_incident_archive = Get-ProjectRelative $PriorArchive
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

& $Runner -EngineRoot $EngineRoot
if ($LASTEXITCODE -ne 0) {
    throw "Frozen One Factory retry returned exit code $LASTEXITCODE"
}

$After = Get-ProtectedSnapshot
Assert-SameSnapshot $Before $After 'Incident v002 clean retry'
Assert-ExactFile $ArchivedMap $ExpectedFailedMapLength $ExpectedFailedMapSha256 'Post-retry archived second failed map'
$RunNamesAfter = @(
    Get-ChildItem -LiteralPath $RunsRoot -Directory |
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
    '$schema' = 'lineboss/audit/one-factory/shell-incident-retry-summary-v002/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'PASS__PRIOR_INCIDENT_PRESERVED__SECOND_FAILED_OUTPUT_PRESERVED__EXACTLY_ONE_CLEAN_RETRY_PASSED'
    prior_incident_archive = Get-ProjectRelative $PriorArchive
    archived_second_failed_map = [ordered]@{
        path = Get-ProjectRelative $ArchivedMap
        length = $ExpectedFailedMapLength
        sha256 = $ExpectedFailedMapSha256
    }
    preserved_second_failed_run_source = Get-ProjectRelative $FailedRun
    preserved_second_failed_run_copy = Get-ProjectRelative $ArchivedRun
    retry_run = $NewRunNames[0]
    retry_map_sha256 = Get-Sha256 $FailedMap
    create_receipt_sha256 = Get-Sha256 $CreateReceipt
    validation_receipt_sha256 = Get-Sha256 $ValidationReceipt
    protected_hashes = $After
}
$Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $RetrySummary -Encoding utf8
Write-Host 'PASS: both failed One Factory outputs are preserved and exactly one clean v002 retry passed.'
Write-Host "Second incident archive: $ArchiveRoot"
Write-Host "Retry run: $($NewRunNames[0])"
