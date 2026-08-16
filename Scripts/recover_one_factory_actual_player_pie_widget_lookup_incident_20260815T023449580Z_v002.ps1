[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Fa-f0-9]{64}$')]
    [string]$ExpectedRecoverySha256
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Runner = Join-Path $Root 'Scripts\run_one_factory_actual_player_pie_v001.ps1'
$Validator = Join-Path $Root 'Scripts\validate_one_factory_actual_player_pie_v001.py'
$RunsRoot = Join-Path $Root 'Saved\Audits\OneFactory\v001\ActualPlayerPIE\Runs'
$FailedStamp = '20260815T023449580Z'
$FailedRun = Join-Path $RunsRoot $FailedStamp
$FailedCapture = Join-Path $Root "Saved\ValidationScreenshots\OneFactory\v001\ActualPlayerPIE\$FailedStamp"
$FailedReceipt = Join-Path $FailedRun 'one_factory_actual_player_pie_v001.json'
$FailedSummary = Join-Path $FailedRun 'one_factory_actual_player_pie_run_summary_v001.json'
$FailedStdout = Join-Path $FailedRun 'Logs\actual_player_pie.stdout.log'
$FailedStderr = Join-Path $FailedRun 'Logs\actual_player_pie.stderr.log'
$FailedBuildStdout = Join-Path $FailedRun 'Logs\editor_build.stdout.log'
$FailedBuildStderr = Join-Path $FailedRun 'Logs\editor_build.stderr.log'
$RecoveryRoot = Join-Path $Root "Saved\Audits\OneFactory\v001\ActualPlayerPIE\IncidentRecovery\Incident_${FailedStamp}_v002"
$PreRetryReceipt = Join-Path $RecoveryRoot 'pre_retry_evidence_v002.json'
$RetryConsole = Join-Path $RecoveryRoot 'fresh_retry_console_v002.log'
$RecoverySummary = Join-Path $RecoveryRoot 'retry_summary_v002.json'

$ExpectedRunnerSha256 = '131E5CAD2F186DB4AE117B7D08B39B170297E23E186597FAD69BD48FA2A9C2CF'
$ExpectedValidatorSha256 = 'B2B8CF70340DCA000E5FCA452FB659C23EE857713A4DC490F8824BD760486792'
$ExpectedMapSha256 = '750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682'
$ExpectedFailedFiles = [ordered]@{
    'one_factory_actual_player_pie_v001.json' = [ordered]@{ bytes = 16518; sha256 = 'FBE5FA4EF00E365BB6101EF29D7C9510FDC4A6EC77418F5B9906CBDC13C518A5' }
    'one_factory_actual_player_pie_run_summary_v001.json' = [ordered]@{ bytes = 31856; sha256 = '51AE20C988345075EA7DAAD67E12C44D55CF3568C6A3988DD8188F9B1B62C169' }
    'Logs/actual_player_pie.stdout.log' = [ordered]@{ bytes = 330166; sha256 = '2837BEBA0056057B6339A8956604FA5191DA983B26E9C3D2D6F2AB84E2AF53E4' }
    'Logs/actual_player_pie.stderr.log' = [ordered]@{ bytes = 0; sha256 = 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855' }
    'Logs/editor_build.stdout.log' = [ordered]@{ bytes = 1052; sha256 = '5022D2EEC8BE9C89006E757795E19315E5A2F4D2A2421597452F676E90AA8C0B' }
    'Logs/editor_build.stderr.log' = [ordered]@{ bytes = 0; sha256 = 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855' }
}
$CriticalProtected = [ordered]@{
    'Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap' = '26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6'
    'Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap' = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'
    'Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap' = '8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F'
    'Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap' = '2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069'
    'Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap' = $ExpectedMapSha256
    'Saved/Audits/OneFactory/v001/one_factory_shell_create_v001.json' = '7D26748BBCE53A11CFE6EEC71FFEE54CBC1504EA48950CADC3E236B2AE16DDB7'
    'Saved/Audits/OneFactory/v001/one_factory_shell_validation_v001.json' = '26F332294FA1640CDACA1D73F23C2F3B8185A6F3EA67A1DEA976AFB09632791E'
}
$ProtectedSource = @(
    'Source/LineBossCarFactory/LBOneFactoryBootstrap.h',
    'Source/LineBossCarFactory/LBOneFactoryBootstrap.cpp',
    'Source/LineBossCarFactory/LBOneFactoryGameMode.h',
    'Source/LineBossCarFactory/LBOneFactoryGameMode.cpp',
    'Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.h',
    'Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.cpp',
    'Source/LineBossCarFactory/LBOneFactoryPressStarterLayout.h',
    'Source/LineBossCarFactory/LBOneFactoryPressStarterLayout.cpp',
    'Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.h',
    'Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp',
    'Source/LineBossCarFactory/LBManagementPawn.h',
    'Source/LineBossCarFactory/LBManagementPawn.cpp',
    'Source/LineBossCarFactory/LBControlRoomHUD.h',
    'Source/LineBossCarFactory/LBControlRoomHUD.cpp',
    'Source/LineBossCarFactory/LBManagementRootWidget.h',
    'Source/LineBossCarFactory/LBManagementRootWidget.cpp'
)

function Assert-Leaf([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label is missing: $Path"
    }
}

function Get-Sha256([string]$Path) {
    Assert-Leaf $Path 'Hash target'
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}

function Get-Relative([string]$Path) {
    $Full = [IO.Path]::GetFullPath($Path)
    $Prefix = $Root.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if (-not $Full.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes project root: $Full"
    }
    return $Full.Substring($Prefix.Length).Replace('\', '/')
}

function Read-Json([string]$Path, [string]$Label) {
    Assert-Leaf $Path $Label
    try { return (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json) }
    catch { throw "$Label is invalid JSON: $($_.Exception.Message)" }
}

function Write-Json([string]$Path, [object]$Value) {
    [IO.File]::WriteAllText(
        $Path,
        (($Value | ConvertTo-Json -Depth 20) + "`n"),
        (New-Object Text.UTF8Encoding($false))
    )
}

function Assert-NoActiveUnrealProcess {
    $Names = @('UnrealEditor', 'UnrealEditor-Cmd', 'UnrealBuildTool', 'AutomationTool', 'RunUAT', 'ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -ne 0) {
        throw "Incident retry refuses active Unreal/build processes: $(@($Active | ForEach-Object { "$($_.ProcessName)[$($_.Id)]" }) -join ', ')"
    }
}

function Get-HashRecord([string]$Path) {
    $Item = Get-Item -LiteralPath $Path -ErrorAction Stop
    return [ordered]@{
        path = Get-Relative $Path
        bytes = [Int64]$Item.Length
        sha256 = Get-Sha256 $Path
    }
}

function Get-ProtectedSnapshot {
    $Paths = New-Object 'System.Collections.Generic.List[string]'
    foreach ($Relative in $CriticalProtected.Keys) {
        [void]$Paths.Add((Join-Path $Root $Relative.Replace('/', '\')))
    }
    foreach ($Relative in $ProtectedSource) {
        [void]$Paths.Add((Join-Path $Root $Relative.Replace('/', '\')))
    }
    foreach ($Path in @($Runner, $Validator)) { [void]$Paths.Add($Path) }
    foreach ($Directory in @((Join-Path $Root 'Config'), (Join-Path $Root 'Saved\SaveGames'))) {
        if (Test-Path -LiteralPath $Directory -PathType Container) {
            foreach ($Item in @(Get-ChildItem -LiteralPath $Directory -Recurse -File -ErrorAction Stop)) {
                [void]$Paths.Add($Item.FullName)
            }
        }
    }
    $Rows = @()
    foreach ($Path in @($Paths | Sort-Object -Unique)) {
        $Rows += Get-HashRecord $Path
    }
    foreach ($Relative in $CriticalProtected.Keys) {
        $Match = @($Rows | Where-Object { [string]$_.path -ceq $Relative })
        if ($Match.Count -ne 1 -or [string]$Match[0].sha256 -cne [string]$CriticalProtected[$Relative]) {
            throw "Protected anchor drift before incident retry: $Relative"
        }
    }
    return @($Rows)
}

function Assert-SameSnapshot([object]$Before, [object]$After, [string]$Label) {
    $Old = @{}
    $New = @{}
    foreach ($Row in @($Before)) { $Old[[string]$Row.path] = "$($Row.bytes)|$($Row.sha256)" }
    foreach ($Row in @($After)) { $New[[string]$Row.path] = "$($Row.bytes)|$($Row.sha256)" }
    $Changed = @((@($Old.Keys) + @($New.Keys)) | Sort-Object -Unique | Where-Object {
        -not $Old.ContainsKey($_) -or -not $New.ContainsKey($_) -or [string]$Old[$_] -cne [string]$New[$_]
    })
    if ($Changed.Count -ne 0) {
        throw "$Label changed protected anchors: $($Changed -join ', ')"
    }
}

function Get-FailedEvidence {
    $Rows = @()
    foreach ($Relative in $ExpectedFailedFiles.Keys) {
        $Path = Join-Path $FailedRun $Relative.Replace('/', '\')
        $Record = Get-HashRecord $Path
        $Expected = $ExpectedFailedFiles[$Relative]
        if ([Int64]$Record.bytes -ne [Int64]$Expected.bytes `
                -or [string]$Record.sha256 -cne [string]$Expected.sha256) {
            throw "Failed-run evidence drift: $Relative"
        }
        $Rows += $Record
    }
    return @($Rows)
}

Assert-Leaf $PSCommandPath 'Incident recovery script'
$ExpectedRecoverySha256 = $ExpectedRecoverySha256.ToUpperInvariant()
$ActualRecoverySha256 = Get-Sha256 $PSCommandPath
if ($ActualRecoverySha256 -cne $ExpectedRecoverySha256) {
    throw "Recovery self-hash mismatch: expected $ExpectedRecoverySha256 actual $ActualRecoverySha256"
}
if ((Get-Sha256 $Runner) -cne $ExpectedRunnerSha256) { throw 'Corrected runner hash drift' }
if ((Get-Sha256 $Validator) -cne $ExpectedValidatorSha256) { throw 'Corrected validator hash drift' }
Assert-NoActiveUnrealProcess
if (Test-Path -LiteralPath $RecoveryRoot) {
    throw "One-use incident recovery destination already exists: $RecoveryRoot"
}
if (-not (Test-Path -LiteralPath $FailedCapture -PathType Container) `
        -or @(Get-ChildItem -LiteralPath $FailedCapture -File -ErrorAction Stop).Count -ne 0) {
    throw 'Failed run must retain one empty screenshot directory'
}

$FailedEvidence = Get-FailedEvidence
$Failed = Read-Json $FailedReceipt 'Failed actual-player receipt'
$FailedRunSummary = Read-Json $FailedSummary 'Failed actual-player runner summary'
if ([string]$Failed.'$schema' -cne 'lineboss/audit/one-factory/actual-player-pie-v001/v1' `
        -or [string]$Failed.status -cne 'FAIL__ONE_FACTORY_ACTUAL_PLAYER_PIE_V001' `
        -or @($Failed.failures).Count -lt 1 `
        -or -not (@($Failed.failures) -contains "module 'unreal' has no attribute 'WidgetBlueprintLibrary'") `
        -or [string]$Failed.map_sha256_before -cne $ExpectedMapSha256 `
        -or [string]$Failed.map_sha256_after -cne $ExpectedMapSha256 `
        -or -not [bool]$Failed.map_hash_unchanged `
        -or @($Failed.protected.changes).Count -ne 0 `
        -or @($Failed.screenshots.PSObject.Properties).Count -ne 0) {
    throw 'Failed receipt no longer proves the exact WidgetBlueprintLibrary incident and clean rollback'
}
if ([string]$FailedRunSummary.status -cne 'FAIL__ONE_FACTORY_ACTUAL_PLAYER_REAL_RHI_RUN_V001' `
        -or @($FailedRunSummary.failures).Count -ne 1 `
        -or [string]$FailedRunSummary.current_map_sha256 -cne $ExpectedMapSha256 `
        -or @($FailedRunSummary.protected_changes).Count -ne 0) {
    throw 'Failed runner summary semantic incident contract drift'
}

$ProtectedBefore = Get-ProtectedSnapshot
$RunNamesBefore = @(Get-ChildItem -LiteralPath $RunsRoot -Directory | ForEach-Object { $_.Name } | Sort-Object)
New-Item -ItemType Directory -Path $RecoveryRoot | Out-Null
$PreRetry = [ordered]@{
    '$schema' = 'lineboss/audit/one-factory/actual-player-widget-lookup-incident-recovery-v002/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'READY__FAILED_RUN_HASH_BOUND__OBJECT_ITERATOR_FIX_FROZEN__ONE_FRESH_RETRY_NOT_STARTED'
    incident_stamp = $FailedStamp
    incident_cause = "module 'unreal' has no attribute 'WidgetBlueprintLibrary'"
    failed_run_evidence = $FailedEvidence
    failed_capture_directory = Get-Relative $FailedCapture
    failed_capture_file_count = 0
    saved_map_sha256 = $ExpectedMapSha256
    protected_change_count = 0
    corrected_validator_sha256 = $ExpectedValidatorSha256
    corrected_runner_sha256 = $ExpectedRunnerSha256
    recovery_script_sha256 = $ActualRecoverySha256
    retry_invocation_limit = 1
}
Write-Json $PreRetryReceipt $PreRetry

$RetryExitCode = $null
$NewRunName = $null
try {
    $PowerShellExe = Join-Path $PSHOME 'powershell.exe'
    Assert-Leaf $PowerShellExe 'Windows PowerShell executable'
    & $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $Runner `
        -ExpectedRunnerSha256 $ExpectedRunnerSha256 *> $RetryConsole
    $RetryExitCode = $LASTEXITCODE
    if ($RetryExitCode -ne 0) {
        throw "Corrected normal runner failed with exit code $RetryExitCode; see $RetryConsole"
    }

    $RunNamesAfter = @(Get-ChildItem -LiteralPath $RunsRoot -Directory | ForEach-Object { $_.Name } | Sort-Object)
    $NewRuns = @($RunNamesAfter | Where-Object { $RunNamesBefore -cnotcontains $_ })
    if ($NewRuns.Count -ne 1) { throw "Expected exactly one fresh retry run, found $($NewRuns.Count)" }
    $NewRunName = $NewRuns[0]
    if ($NewRunName -ceq $FailedStamp) { throw 'Fresh retry reused the preserved incident stamp' }
    $NewRun = Join-Path $RunsRoot $NewRunName
    $NewSummaryPath = Join-Path $NewRun 'one_factory_actual_player_pie_run_summary_v001.json'
    $NewReceiptPath = Join-Path $NewRun 'one_factory_actual_player_pie_v001.json'
    $NewSummary = Read-Json $NewSummaryPath 'Fresh retry runner summary'
    $NewReceipt = Read-Json $NewReceiptPath 'Fresh retry actual-player receipt'
    if ([string]$NewSummary.status -cne 'PASS__ONE_FACTORY_ACTUAL_PLAYER_REAL_RHI_NATIVE_UMG_RUN_V001' `
            -or @($NewSummary.failures).Count -ne 0 `
            -or [string]$NewReceipt.status -cne 'PASS__ONE_FACTORY_ACTUAL_PLAYER_NATIVE_UMG_PRESS_STARTER_REAL_RHI_PIE_V001' `
            -or @($NewReceipt.failures).Count -ne 0 `
            -or @($NewReceipt.screenshots.PSObject.Properties).Count -ne 4 `
            -or [string]$NewReceipt.map_sha256_after -cne $ExpectedMapSha256 `
            -or -not [bool]$NewReceipt.map_hash_unchanged `
            -or @($NewReceipt.protected.changes).Count -ne 0) {
        throw 'Fresh retry receipts did not prove the complete actual-player PASS contract'
    }
    Assert-SameSnapshot $ProtectedBefore (Get-ProtectedSnapshot) 'Fresh incident retry'
    [void](Get-FailedEvidence)
    Assert-NoActiveUnrealProcess

    $Success = [ordered]@{
        '$schema' = 'lineboss/audit/one-factory/actual-player-widget-lookup-incident-retry-summary-v002/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__WIDGET_LOOKUP_INCIDENT_PRESERVED__EXACTLY_ONE_OBJECT_ITERATOR_RETRY_PASSED'
        incident_stamp = $FailedStamp
        retry_stamp = $NewRunName
        retry_invocations = 1
        retry_exit_code = $RetryExitCode
        incident_files_unchanged = $true
        map_sha256 = $ExpectedMapSha256
        protected_anchors_unchanged = $true
        corrected_validator_sha256 = $ExpectedValidatorSha256
        corrected_runner_sha256 = $ExpectedRunnerSha256
        recovery_script_sha256 = $ActualRecoverySha256
        retry_receipt = Get-HashRecord $NewReceiptPath
        retry_runner_summary = Get-HashRecord $NewSummaryPath
        screenshot_count = 4
        content_or_map_packages_deleted = 0
    }
    Write-Json $RecoverySummary $Success
}
catch {
    $FailureSummary = [ordered]@{
        '$schema' = 'lineboss/audit/one-factory/actual-player-widget-lookup-incident-retry-summary-v002/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'FAIL__WIDGET_LOOKUP_INCIDENT_ONE_USE_RETRY_V002'
        failure = $_.Exception.Message
        incident_stamp = $FailedStamp
        retry_stamp = $NewRunName
        retry_invocations = 1
        retry_exit_code = $RetryExitCode
        incident_files = Get-FailedEvidence
        map_sha256 = Get-Sha256 (Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Maps\LB_MoorcrossWorks_OneFactory_v001.umap')
        recovery_script_sha256 = $ActualRecoverySha256
        content_or_map_packages_deleted = 0
    }
    Write-Json $RecoverySummary $FailureSummary
    throw
}

Write-Host 'PASS: preserved WidgetBlueprintLibrary incident and completed exactly one corrected ObjectIterator retry.'
Write-Host "Recovery summary: $RecoverySummary"
