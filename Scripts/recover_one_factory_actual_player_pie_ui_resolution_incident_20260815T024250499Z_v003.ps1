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
$BridgeHeader = Join-Path $Root 'Source\LineBossCarFactory\LBOneFactoryCaptureBridge.h'
$BridgeSource = Join-Path $Root 'Source\LineBossCarFactory\LBOneFactoryCaptureBridge.cpp'
$RunsRoot = Join-Path $Root 'Saved\Audits\OneFactory\v001\ActualPlayerPIE\Runs'
$CapturesRoot = Join-Path $Root 'Saved\ValidationScreenshots\OneFactory\v001\ActualPlayerPIE'
$FirstFailedStamp = '20260815T023449580Z'
$SecondFailedStamp = '20260815T024250499Z'
$FirstFailedRun = Join-Path $RunsRoot $FirstFailedStamp
$SecondFailedRun = Join-Path $RunsRoot $SecondFailedStamp
$FirstFailedCapture = Join-Path $CapturesRoot $FirstFailedStamp
$SecondFailedCapture = Join-Path $CapturesRoot $SecondFailedStamp
$RecoveryRoot = Join-Path $Root "Saved\Audits\OneFactory\v001\ActualPlayerPIE\IncidentRecovery\Incident_${SecondFailedStamp}_v003"
$PreRetryReceipt = Join-Path $RecoveryRoot 'pre_retry_evidence_v003.json'
$RetryConsole = Join-Path $RecoveryRoot 'fresh_retry_console_v003.log'
$RecoverySummary = Join-Path $RecoveryRoot 'retry_summary_v003.json'

$ExpectedRunnerSha256 = '537C7DE93026F649618820931E6DE4FB8E8F4E3E9616BB7D6DEC3C243EBDA3E3'
$ExpectedValidatorSha256 = '73336DB831F35EE330E6DFB6FAF3FBCBD30735E9116BE075D576847152E54A0E'
$ExpectedBridgeHeaderSha256 = '5D24296B0FF7239276793DCA0232DBFB239E6C393B0ED7EA2D767F15BFF7F8C8'
$ExpectedBridgeSourceSha256 = '447C04E64A2F322754C6F78523A34A59D9E133B3D949B766064D9FD112F15ECD'
$ExpectedMapSha256 = '750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682'
$ExpectedFirstFailedFiles = [ordered]@{
    'Logs/actual_player_pie.stderr.log' = [ordered]@{ bytes = 0; sha256 = 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855' }
    'Logs/actual_player_pie.stdout.log' = [ordered]@{ bytes = 330166; sha256 = '2837BEBA0056057B6339A8956604FA5191DA983B26E9C3D2D6F2AB84E2AF53E4' }
    'Logs/editor_build.stderr.log' = [ordered]@{ bytes = 0; sha256 = 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855' }
    'Logs/editor_build.stdout.log' = [ordered]@{ bytes = 1052; sha256 = '5022D2EEC8BE9C89006E757795E19315E5A2F4D2A2421597452F676E90AA8C0B' }
    'one_factory_actual_player_pie_run_summary_v001.json' = [ordered]@{ bytes = 31856; sha256 = '51AE20C988345075EA7DAAD67E12C44D55CF3568C6A3988DD8188F9B1B62C169' }
    'one_factory_actual_player_pie_v001.json' = [ordered]@{ bytes = 16518; sha256 = 'FBE5FA4EF00E365BB6101EF29D7C9510FDC4A6EC77418F5B9906CBDC13C518A5' }
}
$ExpectedSecondFailedFiles = [ordered]@{
    'Logs/actual_player_pie.stderr.log' = [ordered]@{ bytes = 0; sha256 = 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855' }
    'Logs/actual_player_pie.stdout.log' = [ordered]@{ bytes = 335102; sha256 = '5A6A3C9B76D63E51DD4967039EB62A7AC77C0C352C6D0D7F6F0A234B7D6BC1B4' }
    'Logs/editor_build.stderr.log' = [ordered]@{ bytes = 0; sha256 = 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855' }
    'Logs/editor_build.stdout.log' = [ordered]@{ bytes = 1052; sha256 = '752C3C7D5F9663B5CCDB0CB45A442A3435F337C44A114EC27EBD13186D761E58' }
    'one_factory_actual_player_pie_run_summary_v001.json' = [ordered]@{ bytes = 31856; sha256 = '4F1383241C962B664A8C7EFC8CD6A367FC785D1DB90DC20566D6AC7630FC0D5E' }
    'one_factory_actual_player_pie_v001.json' = [ordered]@{ bytes = 35026; sha256 = 'FE9C50B9408ED279C50D762A1DF71BB78B9630B8EF11D911A80E0DF6B2001F19' }
}
$ExpectedSecondFailedScreenshots = [ordered]@{
    '01_empty_factory_management_overview.png' = [ordered]@{ bytes = 1662302; sha256 = 'C9EB1B2AB86375C7CDF1EECF0A876872834D0C1B374B57ACB4798D8AFB8FE600'; width = 1920; height = 1080 }
    '02_populated_press_starter_wide_overview.png' = [ordered]@{ bytes = 1665220; sha256 = 'CDEF996D2A7A5933B3F0C8EB2FCA58A66624CE2E244F534CA764D7B92C104A3B'; width = 1920; height = 1080 }
    '03_press_train_dispatch_agv_close.png' = [ordered]@{ bytes = 2277618; sha256 = 'ED7D476C42FAE9AF1F757CA0238D691B5A33F0F49E6EF3A3801C499030C9BCFF'; width = 1920; height = 1080 }
    '04_populated_press_starter_with_umg.png' = [ordered]@{ bytes = 431899; sha256 = '6120A5ECCDB3FA24D00251E92961FE623CBFE4B0E3B4C88AF362BAF8CCC8E11B'; width = 1300; height = 740 }
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

function Assert-Leaf([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "$Label is missing: $Path" }
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
        (($Value | ConvertTo-Json -Depth 30) + "`n"),
        (New-Object Text.UTF8Encoding($false))
    )
}

function Assert-NoActiveUnrealProcess {
    $Names = @('UnrealEditor', 'UnrealEditor-Cmd', 'UnrealBuildTool', 'AutomationTool', 'RunUAT', 'ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -ne 0) {
        throw "Incident recovery refuses active Unreal/build processes: $(@($Active | ForEach-Object { "$($_.ProcessName)[$($_.Id)]" }) -join ', ')"
    }
}

function Get-PngDimensions([string]$Path) {
    Assert-Leaf $Path 'PNG evidence'
    $Stream = [IO.File]::OpenRead($Path)
    try {
        $Header = New-Object byte[] 24
        if ($Stream.Read($Header, 0, 24) -ne 24) { throw "PNG header is truncated: $Path" }
    }
    finally { $Stream.Dispose() }
    $Signature = @(137,80,78,71,13,10,26,10)
    for ($Index = 0; $Index -lt 8; $Index++) {
        if ($Header[$Index] -ne $Signature[$Index]) { throw "PNG signature drift: $Path" }
    }
    if ([Text.Encoding]::ASCII.GetString($Header, 12, 4) -cne 'IHDR') { throw "PNG IHDR drift: $Path" }
    return [ordered]@{
        width = [int](($Header[16] -shl 24) -bor ($Header[17] -shl 16) -bor ($Header[18] -shl 8) -bor $Header[19])
        height = [int](($Header[20] -shl 24) -bor ($Header[21] -shl 16) -bor ($Header[22] -shl 8) -bor $Header[23])
    }
}

function Get-HashRecord([string]$Path) {
    $Item = Get-Item -LiteralPath $Path -ErrorAction Stop
    return [ordered]@{ path = Get-Relative $Path; bytes = [Int64]$Item.Length; sha256 = Get-Sha256 $Path }
}

function Assert-ExactDirectory([string]$Directory, [object]$Expected, [switch]$Png) {
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { throw "Evidence directory is missing: $Directory" }
    $ActualNames = @(Get-ChildItem -LiteralPath $Directory -Recurse -File | ForEach-Object {
        $_.FullName.Substring($Directory.Length + 1).Replace('\', '/')
    } | Sort-Object)
    $ExpectedNames = @($Expected.Keys | Sort-Object)
    if (@(Compare-Object $ExpectedNames $ActualNames -CaseSensitive).Count -ne 0) {
        throw "Evidence inventory drift under $Directory"
    }
    $Rows = @()
    foreach ($Relative in $Expected.Keys) {
        $Path = Join-Path $Directory $Relative.Replace('/', '\')
        $Record = Get-HashRecord $Path
        $Pinned = $Expected[$Relative]
        if ([Int64]$Record.bytes -ne [Int64]$Pinned.bytes -or [string]$Record.sha256 -cne [string]$Pinned.sha256) {
            throw "Evidence hash/size drift: $Relative"
        }
        if ($Png) {
            $Dimensions = Get-PngDimensions $Path
            if ([int]$Dimensions.width -ne [int]$Pinned.width -or [int]$Dimensions.height -ne [int]$Pinned.height) {
                throw "Evidence PNG dimension drift: $Relative"
            }
            $Record.dimensions = @([int]$Dimensions.width, [int]$Dimensions.height)
        }
        $Rows += $Record
    }
    return @($Rows)
}

function Get-ProtectedSnapshot {
    $Paths = New-Object 'System.Collections.Generic.List[string]'
    foreach ($Relative in $CriticalProtected.Keys) { [void]$Paths.Add((Join-Path $Root $Relative.Replace('/', '\'))) }
    foreach ($Path in @($Runner, $Validator, $BridgeHeader, $BridgeSource)) { [void]$Paths.Add($Path) }
    foreach ($Directory in @((Join-Path $Root 'Config'), (Join-Path $Root 'Saved\SaveGames'))) {
        if (Test-Path -LiteralPath $Directory -PathType Container) {
            foreach ($Item in @(Get-ChildItem -LiteralPath $Directory -Recurse -File)) { [void]$Paths.Add($Item.FullName) }
        }
    }
    $Rows = @($Paths | Sort-Object -Unique | ForEach-Object { Get-HashRecord $_ })
    foreach ($Relative in $CriticalProtected.Keys) {
        $Match = @($Rows | Where-Object { [string]$_.path -ceq $Relative })
        if ($Match.Count -ne 1 -or [string]$Match[0].sha256 -cne [string]$CriticalProtected[$Relative]) {
            throw "Protected anchor hash drift: $Relative"
        }
    }
    return $Rows
}

function Assert-SameSnapshot([object]$Before, [object]$After, [string]$Label) {
    $Old = @{}; $New = @{}
    foreach ($Row in @($Before)) { $Old[[string]$Row.path] = "$($Row.bytes)|$($Row.sha256)" }
    foreach ($Row in @($After)) { $New[[string]$Row.path] = "$($Row.bytes)|$($Row.sha256)" }
    $Changed = @((@($Old.Keys) + @($New.Keys)) | Sort-Object -Unique | Where-Object {
        -not $Old.ContainsKey($_) -or -not $New.ContainsKey($_) -or [string]$Old[$_] -cne [string]$New[$_]
    })
    if ($Changed.Count -ne 0) { throw "$Label changed protected anchors: $($Changed -join ', ')" }
}

function Assert-PreservedIncidents {
    $FirstFiles = Assert-ExactDirectory $FirstFailedRun $ExpectedFirstFailedFiles
    $SecondFiles = Assert-ExactDirectory $SecondFailedRun $ExpectedSecondFailedFiles
    if (-not (Test-Path -LiteralPath $FirstFailedCapture -PathType Container) `
            -or @(Get-ChildItem -LiteralPath $FirstFailedCapture -Recurse -File).Count -ne 0) {
        throw 'First incident no longer has its exact empty capture directory'
    }
    $SecondScreens = Assert-ExactDirectory $SecondFailedCapture $ExpectedSecondFailedScreenshots -Png
    return [ordered]@{ first_run = $FirstFiles; second_run = $SecondFiles; second_screenshots = $SecondScreens }
}

Assert-Leaf $PSCommandPath 'UI-resolution incident recovery script'
$ExpectedRecoverySha256 = $ExpectedRecoverySha256.ToUpperInvariant()
$ActualRecoverySha256 = Get-Sha256 $PSCommandPath
if ($ActualRecoverySha256 -cne $ExpectedRecoverySha256) {
    throw "Recovery self-hash mismatch: expected $ExpectedRecoverySha256 actual $ActualRecoverySha256"
}
if ((Get-Sha256 $Runner) -cne $ExpectedRunnerSha256) { throw 'Corrected normal runner hash drift' }
if ((Get-Sha256 $Validator) -cne $ExpectedValidatorSha256) { throw 'Corrected validator hash drift' }
if ((Get-Sha256 $BridgeHeader) -cne $ExpectedBridgeHeaderSha256) { throw 'Native capture bridge header hash drift' }
if ((Get-Sha256 $BridgeSource) -cne $ExpectedBridgeSourceSha256) { throw 'Native capture bridge source hash drift' }
Assert-NoActiveUnrealProcess
if (Test-Path -LiteralPath $RecoveryRoot) { throw "One-use recovery destination already exists: $RecoveryRoot" }

$PreservedBefore = Assert-PreservedIncidents
$FirstReceipt = Read-Json (Join-Path $FirstFailedRun 'one_factory_actual_player_pie_v001.json') 'First failed receipt'
$SecondReceipt = Read-Json (Join-Path $SecondFailedRun 'one_factory_actual_player_pie_v001.json') 'Second failed receipt'
$SecondSummary = Read-Json (Join-Path $SecondFailedRun 'one_factory_actual_player_pie_run_summary_v001.json') 'Second failed runner summary'
$ExactSecondCause = 'OneFactory screenshot is not 1920x1080: 04_populated_press_starter_with_umg.png=[1300, 740]'
if ([string]$FirstReceipt.status -cne 'FAIL__ONE_FACTORY_ACTUAL_PLAYER_PIE_V001' `
        -or -not (@($FirstReceipt.failures) -contains "module 'unreal' has no attribute 'WidgetBlueprintLibrary'") `
        -or -not [bool]$FirstReceipt.map_hash_unchanged -or @($FirstReceipt.protected.changes).Count -ne 0) {
    throw 'First failed-run semantic contract drift'
}
if ([string]$SecondReceipt.status -cne 'FAIL__ONE_FACTORY_ACTUAL_PLAYER_PIE_V001' `
        -or -not (@($SecondReceipt.failures) -contains $ExactSecondCause) `
        -or @($SecondReceipt.screenshots.PSObject.Properties).Count -ne 3 `
        -or -not [bool]$SecondReceipt.map_hash_unchanged `
        -or [string]$SecondReceipt.map_sha256_after -cne $ExpectedMapSha256 `
        -or @($SecondReceipt.protected.changes).Count -ne 0) {
    throw 'Second failed-run semantic UI-resolution contract drift'
}
if ([string]$SecondSummary.status -cne 'FAIL__ONE_FACTORY_ACTUAL_PLAYER_REAL_RHI_RUN_V001' `
        -or @($SecondSummary.failures).Count -ne 1 `
        -or [string]$SecondSummary.current_map_sha256 -cne $ExpectedMapSha256 `
        -or @($SecondSummary.protected_changes).Count -ne 0) {
    throw 'Second failed runner-summary contract drift'
}

$ProtectedBefore = Get-ProtectedSnapshot
$RunNamesBefore = @(Get-ChildItem -LiteralPath $RunsRoot -Directory | ForEach-Object Name | Sort-Object)
New-Item -ItemType Directory -Path $RecoveryRoot | Out-Null
$PreRetry = [ordered]@{
    '$schema' = 'lineboss/audit/one-factory/actual-player-ui-resolution-incident-recovery-v003/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'READY__TWO_FAILED_RUNS_HASH_BOUND__NATIVE_SLATE_RESIZE_FIX_FROZEN__ONE_RETRY_NOT_STARTED'
    first_incident_stamp = $FirstFailedStamp
    second_incident_stamp = $SecondFailedStamp
    second_incident_cause = $ExactSecondCause
    preserved_evidence = $PreservedBefore
    correction = [ordered]@{
        api = 'FSceneViewport.SetViewportSize'
        bridge = '/Script/LineBossCarFactory.LBOneFactoryCaptureBridge'
        requested_size = @(1920, 1080)
        native_umg_required = $true
        rescale_crop_or_composite = $false
    }
    corrected_validator_sha256 = $ExpectedValidatorSha256
    corrected_runner_sha256 = $ExpectedRunnerSha256
    capture_bridge_header_sha256 = $ExpectedBridgeHeaderSha256
    capture_bridge_source_sha256 = $ExpectedBridgeSourceSha256
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
    if ($RetryExitCode -ne 0) { throw "Corrected normal runner failed with exit code $RetryExitCode; see $RetryConsole" }

    $RunNamesAfter = @(Get-ChildItem -LiteralPath $RunsRoot -Directory | ForEach-Object Name | Sort-Object)
    $NewRuns = @($RunNamesAfter | Where-Object { $RunNamesBefore -cnotcontains $_ })
    if ($NewRuns.Count -ne 1) { throw "Expected exactly one fresh retry run, found $($NewRuns.Count)" }
    $NewRunName = $NewRuns[0]
    if ($NewRunName -in @($FirstFailedStamp, $SecondFailedStamp)) { throw 'Fresh retry reused a preserved incident stamp' }
    $NewRun = Join-Path $RunsRoot $NewRunName
    $NewSummaryPath = Join-Path $NewRun 'one_factory_actual_player_pie_run_summary_v001.json'
    $NewReceiptPath = Join-Path $NewRun 'one_factory_actual_player_pie_v001.json'
    $NewSummary = Read-Json $NewSummaryPath 'Fresh retry runner summary'
    $NewReceipt = Read-Json $NewReceiptPath 'Fresh retry actual-player receipt'
    $UICheck = $NewReceipt.checks.native_ui_capture_viewport_1920x1080.evidence
    $UIShot = $NewReceipt.screenshots.'04_populated_press_starter_with_umg.png'
    if ([string]$NewSummary.status -cne 'PASS__ONE_FACTORY_ACTUAL_PLAYER_REAL_RHI_NATIVE_UMG_RUN_V001' `
            -or @($NewSummary.failures).Count -ne 0 `
            -or [string]$NewReceipt.status -cne 'PASS__ONE_FACTORY_ACTUAL_PLAYER_NATIVE_UMG_PRESS_STARTER_REAL_RHI_PIE_V001' `
            -or @($NewReceipt.failures).Count -ne 0 `
            -or @($NewReceipt.screenshots.PSObject.Properties).Count -ne 4 `
            -or @($UIShot.dimensions).Count -ne 2 -or [int]$UIShot.dimensions[0] -ne 1920 -or [int]$UIShot.dimensions[1] -ne 1080 `
            -or -not [bool]$UIShot.hud_required `
            -or [string]$UICheck.api -cne 'FSceneViewport.SetViewportSize' `
            -or -not [bool]$UICheck.native_umg_visible_after_resize -or [bool]$UICheck.post_processing `
            -or -not [bool]$NewReceipt.map_hash_unchanged `
            -or @($NewReceipt.protected.changes).Count -ne 0) {
        throw 'Fresh retry did not prove native 1920x1080 Slate/UMG PASS contract'
    }
    Assert-SameSnapshot $ProtectedBefore (Get-ProtectedSnapshot) 'Fresh UI-resolution incident retry'
    $PreservedAfter = Assert-PreservedIncidents
    Assert-NoActiveUnrealProcess

    $Success = [ordered]@{
        '$schema' = 'lineboss/audit/one-factory/actual-player-ui-resolution-incident-retry-summary-v003/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__TWO_INCIDENTS_PRESERVED__EXACTLY_ONE_NATIVE_SLATE_1920X1080_UMG_RETRY_PASSED'
        first_incident_stamp = $FirstFailedStamp
        second_incident_stamp = $SecondFailedStamp
        retry_stamp = $NewRunName
        retry_invocations = 1
        retry_exit_code = $RetryExitCode
        incidents_unchanged = $true
        protected_anchors_unchanged = $true
        map_sha256 = $ExpectedMapSha256
        corrected_validator_sha256 = $ExpectedValidatorSha256
        corrected_runner_sha256 = $ExpectedRunnerSha256
        recovery_script_sha256 = $ActualRecoverySha256
        retry_receipt = Get-HashRecord $NewReceiptPath
        retry_runner_summary = Get-HashRecord $NewSummaryPath
        native_ui_screenshot = $UIShot
        preserved_evidence_after = $PreservedAfter
        content_or_map_package_removals = 0
    }
    Write-Json $RecoverySummary $Success
}
catch {
    $FailureSummary = [ordered]@{
        '$schema' = 'lineboss/audit/one-factory/actual-player-ui-resolution-incident-retry-summary-v003/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'FAIL__UI_RESOLUTION_INCIDENT_ONE_USE_RETRY_V003'
        failure = $_.Exception.Message
        first_incident_stamp = $FirstFailedStamp
        second_incident_stamp = $SecondFailedStamp
        retry_stamp = $NewRunName
        retry_invocations = 1
        retry_exit_code = $RetryExitCode
        incidents = Assert-PreservedIncidents
        map_sha256 = Get-Sha256 (Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Maps\LB_MoorcrossWorks_OneFactory_v001.umap')
        recovery_script_sha256 = $ActualRecoverySha256
        content_or_map_package_removals = 0
    }
    Write-Json $RecoverySummary $FailureSummary
    throw
}

Write-Host 'PASS: preserved both OneFactory incidents and completed exactly one native 1920x1080 Slate/UMG retry.'
Write-Host "Recovery summary: $RecoverySummary"
