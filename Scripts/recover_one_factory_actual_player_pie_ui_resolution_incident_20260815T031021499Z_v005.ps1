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
$RejectedV003 = Join-Path $Root 'Scripts\recover_one_factory_actual_player_pie_ui_resolution_incident_20260815T024250499Z_v003.ps1'
$FailedV004 = Join-Path $Root 'Scripts\recover_one_factory_actual_player_pie_ui_resolution_incident_20260815T024250499Z_v004.ps1'
$ParserRegression = Join-Path $Root 'Scripts\tests\test_one_factory_png_ihdr_parser_ps51_v004.ps1'
$RunsRoot = Join-Path $Root 'Saved\Audits\OneFactory\v001\ActualPlayerPIE\Runs'
$CapturesRoot = Join-Path $Root 'Saved\ValidationScreenshots\OneFactory\v001\ActualPlayerPIE'
$IncidentRoot = Join-Path $Root 'Saved\Audits\OneFactory\v001\ActualPlayerPIE\IncidentRecovery'
$FirstStamp = '20260815T023449580Z'
$SecondStamp = '20260815T024250499Z'
$ThirdStamp = '20260815T031021499Z'
$V003Root = Join-Path $IncidentRoot "Incident_${SecondStamp}_v003"
$V004Root = Join-Path $IncidentRoot "Incident_${SecondStamp}_v004"
$RecoveryRoot = Join-Path $IncidentRoot "Incident_${ThirdStamp}_v005"
$PreRetryReceipt = Join-Path $RecoveryRoot 'pre_retry_evidence_v005.json'
$RetryConsole = Join-Path $RecoveryRoot 'fresh_retry_console_v005.log'
$RecoverySummary = Join-Path $RecoveryRoot 'retry_summary_v005.json'

$ExpectedRunnerSha256 = 'B0E7010DFACD27584F1EB096B38D2783F066682FCFDCE09801B371D28CCDFEB7'
$ExpectedValidatorSha256 = '9DFEEE6D6C29B5D96EB6650F38494854BDA780BFDDC09A146150118FF3610099'
$ExpectedBridgeHeaderSha256 = '2C5442B15B94504CEA085A3F46F4740BCC4FD0A83CDE70DB37E3C7D0FC04673B'
$ExpectedBridgeSourceSha256 = '849C7E1ACD6A02B27126831202E774E8C922E422050904EC3DF5349C6D01CA30'
$ExpectedRejectedV003Sha256 = 'C04D5610F4959D6BD36CA7AC2DCF1C69E7A114DB312B5ACCF12F274F3869CB8C'
$ExpectedFailedV004Sha256 = 'A1D18D036FF2FB8E862C56F8618513A7FD4654D3AE5EF4C74AD07E6DE1565B76'
$ExpectedParserRegressionSha256 = '6C287FC9BDB9D495337D955F8D1DDA928CBD0B2F35EB3C42CFF73EFB6C63794D'
$ExpectedMapSha256 = '750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682'
$EmptySha256 = 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855'

$ExpectedRuns = [ordered]@{
    $FirstStamp = [ordered]@{
        'Logs/actual_player_pie.stderr.log' = @(0, $EmptySha256)
        'Logs/actual_player_pie.stdout.log' = @(330166, '2837BEBA0056057B6339A8956604FA5191DA983B26E9C3D2D6F2AB84E2AF53E4')
        'Logs/editor_build.stderr.log' = @(0, $EmptySha256)
        'Logs/editor_build.stdout.log' = @(1052, '5022D2EEC8BE9C89006E757795E19315E5A2F4D2A2421597452F676E90AA8C0B')
        'one_factory_actual_player_pie_run_summary_v001.json' = @(31856, '51AE20C988345075EA7DAAD67E12C44D55CF3568C6A3988DD8188F9B1B62C169')
        'one_factory_actual_player_pie_v001.json' = @(16518, 'FBE5FA4EF00E365BB6101EF29D7C9510FDC4A6EC77418F5B9906CBDC13C518A5')
    }
    $SecondStamp = [ordered]@{
        'Logs/actual_player_pie.stderr.log' = @(0, $EmptySha256)
        'Logs/actual_player_pie.stdout.log' = @(335102, '5A6A3C9B76D63E51DD4967039EB62A7AC77C0C352C6D0D7F6F0A234B7D6BC1B4')
        'Logs/editor_build.stderr.log' = @(0, $EmptySha256)
        'Logs/editor_build.stdout.log' = @(1052, '752C3C7D5F9663B5CCDB0CB45A442A3435F337C44A114EC27EBD13186D761E58')
        'one_factory_actual_player_pie_run_summary_v001.json' = @(31856, '4F1383241C962B664A8C7EFC8CD6A367FC785D1DB90DC20566D6AC7630FC0D5E')
        'one_factory_actual_player_pie_v001.json' = @(35026, 'FE9C50B9408ED279C50D762A1DF71BB78B9630B8EF11D911A80E0DF6B2001F19')
    }
    $ThirdStamp = [ordered]@{
        'Logs/actual_player_pie.stderr.log' = @(0, $EmptySha256)
        'Logs/actual_player_pie.stdout.log' = @(331660, '22C4BCA1F56577975E4452506A0C1E95324302AA3D0595B5C700F6BC5C7DA606')
        'Logs/editor_build.stderr.log' = @(0, $EmptySha256)
        'Logs/editor_build.stdout.log' = @(7833, '01F7B6FEE6172B42BE889FCDD5326372BDA525A506411DCA4BD5BD4F7E569492')
        'one_factory_actual_player_pie_run_summary_v001.json' = @(33397, '1F091680D688933ECEAD17AC7FC8E1F6B0BCCC3BE676085E1B402AA1E2B87CC9')
        'one_factory_actual_player_pie_v001.json' = @(36495, 'E981B74B9D740EAEBA52CF6EC234FB48F9755DCD5D50B8D2E9604ECC6252505D')
    }
}

$ExpectedCaptures = [ordered]@{
    $SecondStamp = [ordered]@{
        '01_empty_factory_management_overview.png' = @(1662302, 'C9EB1B2AB86375C7CDF1EECF0A876872834D0C1B374B57ACB4798D8AFB8FE600', 1920, 1080)
        '02_populated_press_starter_wide_overview.png' = @(1665220, 'CDEF996D2A7A5933B3F0C8EB2FCA58A66624CE2E244F534CA764D7B92C104A3B', 1920, 1080)
        '03_press_train_dispatch_agv_close.png' = @(2277618, 'ED7D476C42FAE9AF1F757CA0238D691B5A33F0F49E6EF3A3801C499030C9BCFF', 1920, 1080)
        '04_populated_press_starter_with_umg.png' = @(431899, '6120A5ECCDB3FA24D00251E92961FE623CBFE4B0E3B4C88AF362BAF8CCC8E11B', 1300, 740)
    }
    $ThirdStamp = [ordered]@{
        '01_empty_factory_management_overview.png' = @(1663756, '1FDD542C869F4A3BACBA1D61FFDBCC9B3C37147AE5048508D18BED3F00C22DC5', 1920, 1080)
        '02_populated_press_starter_wide_overview.png' = @(1669381, 'FF81AE126A087AC9952422235A615EC79933E669640C1FCC18BCEF5436B25F08', 1920, 1080)
        '03_press_train_dispatch_agv_close.png' = @(2357071, 'B3E1BC0FE5959441EB0A0CB230BCCB46CE6AF57C9DD6A2DED47C6D9A403D3AD5', 1920, 1080)
        '04_populated_press_starter_with_umg.png' = @(630835, '7DBD3120806F76763A78B92E6AA93F215C3E3F3137011F7909EF0ED017AE5DE8', 1300, 740)
    }
}

$ExpectedV004Evidence = [ordered]@{
    'fresh_retry_console_v004.log' = @(0, $EmptySha256)
    'pre_retry_evidence_v004.json' = @(12615, 'A12AEE0D655F689126803F272EAC543C933BD470CCE045AB13E0BF93CA9481F5')
    'retry_summary_v004.json' = @(9411, 'F689F33B4C411EB06553AAC6D14765042626C7F8426CC9DDD75B7A5BC925AD82')
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
    if (-not $Full.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Path escapes project root: $Full" }
    return $Full.Substring($Prefix.Length).Replace('\', '/')
}

function Get-Record([string]$Path) {
    $Item = Get-Item -LiteralPath $Path -ErrorAction Stop
    return [ordered]@{ path = Get-Relative $Path; bytes = [Int64]$Item.Length; sha256 = Get-Sha256 $Path }
}

function Read-Json([string]$Path, [string]$Label) {
    Assert-Leaf $Path $Label
    try { return (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json) }
    catch { throw "$Label is invalid JSON: $($_.Exception.Message)" }
}

function Write-Json([string]$Path, [object]$Value) {
    [IO.File]::WriteAllText($Path, (($Value | ConvertTo-Json -Depth 30) + "`n"), (New-Object Text.UTF8Encoding($false)))
}

function Get-PngDimensions([string]$Path) {
    Assert-Leaf $Path 'PNG evidence'
    $Stream = [IO.File]::OpenRead($Path)
    try {
        $Header = New-Object byte[] 24
        if ($Stream.Read($Header, 0, 24) -ne 24) { throw "PNG header is truncated: $Path" }
    }
    finally { $Stream.Dispose() }
    $Signature = @(137, 80, 78, 71, 13, 10, 26, 10)
    for ($Index = 0; $Index -lt 8; $Index++) {
        if ([int]$Header[$Index] -ne [int]$Signature[$Index]) { throw "PNG signature drift: $Path" }
    }
    if ([Text.Encoding]::ASCII.GetString($Header, 12, 4) -cne 'IHDR') { throw "PNG IHDR drift: $Path" }
    $Width = ((([uint32]$Header[16]) -shl 24) -bor (([uint32]$Header[17]) -shl 16) -bor (([uint32]$Header[18]) -shl 8) -bor ([uint32]$Header[19]))
    $Height = ((([uint32]$Header[20]) -shl 24) -bor (([uint32]$Header[21]) -shl 16) -bor (([uint32]$Header[22]) -shl 8) -bor ([uint32]$Header[23]))
    return @([uint32]$Width, [uint32]$Height)
}

function Assert-ExactDirectory([string]$Directory, [object]$Expected, [switch]$Png) {
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { throw "Evidence directory is missing: $Directory" }
    $ActualNames = @(Get-ChildItem -LiteralPath $Directory -Recurse -File | ForEach-Object {
        $_.FullName.Substring($Directory.Length + 1).Replace('\', '/')
    } | Sort-Object)
    if (@(Compare-Object @($Expected.Keys | Sort-Object) $ActualNames -CaseSensitive).Count -ne 0) {
        throw "Evidence inventory drift under $Directory"
    }
    $Records = @()
    foreach ($Relative in $Expected.Keys) {
        $Path = Join-Path $Directory $Relative.Replace('/', '\')
        $Pinned = @($Expected[$Relative])
        $Record = Get-Record $Path
        if ([Int64]$Record.bytes -ne [Int64]$Pinned[0] -or [string]$Record.sha256 -cne [string]$Pinned[1]) {
            throw "Evidence hash/size drift: $Relative"
        }
        if ($Png) {
            $Dimensions = @(Get-PngDimensions $Path)
            if ([uint32]$Dimensions[0] -ne [uint32]$Pinned[2] -or [uint32]$Dimensions[1] -ne [uint32]$Pinned[3]) {
                throw "Evidence PNG dimension drift: $Relative"
            }
            $Record.dimensions = @([uint32]$Dimensions[0], [uint32]$Dimensions[1])
        }
        $Records += $Record
    }
    return @($Records)
}

function Assert-NoActiveUnrealProcess {
    $Names = @('UnrealEditor', 'UnrealEditor-Cmd', 'UnrealBuildTool', 'AutomationTool', 'RunUAT', 'ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -ne 0) {
        throw "Recovery refuses active Unreal/build processes: $(@($Active | ForEach-Object { "$($_.ProcessName)[$($_.Id)]" }) -join ', ')"
    }
}

function Assert-PreservedIncidents {
    $RunRecords = [ordered]@{}
    foreach ($Stamp in $ExpectedRuns.Keys) {
        $RunRecords[$Stamp] = Assert-ExactDirectory (Join-Path $RunsRoot $Stamp) $ExpectedRuns[$Stamp]
    }
    $FirstCapture = Join-Path $CapturesRoot $FirstStamp
    if (-not (Test-Path -LiteralPath $FirstCapture -PathType Container) `
            -or @(Get-ChildItem -LiteralPath $FirstCapture -Recurse -File).Count -ne 0) {
        throw 'First incident no longer has its exact empty capture directory'
    }
    $CaptureRecords = [ordered]@{}
    foreach ($Stamp in $ExpectedCaptures.Keys) {
        $CaptureRecords[$Stamp] = Assert-ExactDirectory (Join-Path $CapturesRoot $Stamp) $ExpectedCaptures[$Stamp] -Png
    }
    $V004Records = Assert-ExactDirectory $V004Root $ExpectedV004Evidence
    if (Test-Path -LiteralPath $V003Root) { throw 'Rejected v003 unexpectedly has a recovery root' }
    return [ordered]@{ failed_runs = $RunRecords; screenshots = $CaptureRecords; v004_recovery = $V004Records }
}

function Get-ProtectedSnapshot {
    $Paths = New-Object 'System.Collections.Generic.List[string]'
    foreach ($Relative in $CriticalProtected.Keys) { [void]$Paths.Add((Join-Path $Root $Relative.Replace('/', '\'))) }
    foreach ($Path in @($Runner, $Validator, $BridgeHeader, $BridgeSource, $RejectedV003, $FailedV004, $ParserRegression, $PSCommandPath)) {
        [void]$Paths.Add($Path)
    }
    foreach ($Directory in @((Join-Path $Root 'Config'), (Join-Path $Root 'Saved\SaveGames'))) {
        if (Test-Path -LiteralPath $Directory -PathType Container) {
            foreach ($Item in @(Get-ChildItem -LiteralPath $Directory -Recurse -File)) { [void]$Paths.Add($Item.FullName) }
        }
    }
    $Rows = @($Paths | Sort-Object -Unique | ForEach-Object { Get-Record $_ })
    foreach ($Relative in $CriticalProtected.Keys) {
        $Match = @($Rows | Where-Object { [string]$_.path -ceq $Relative })
        if ($Match.Count -ne 1 -or [string]$Match[0].sha256 -cne [string]$CriticalProtected[$Relative]) {
            throw "Protected anchor hash drift: $Relative"
        }
    }
    return $Rows
}

function Assert-SameSnapshot([object]$Before, [object]$After) {
    $Old = @{}; $New = @{}
    foreach ($Row in @($Before)) { $Old[[string]$Row.path] = "$($Row.bytes)|$($Row.sha256)" }
    foreach ($Row in @($After)) { $New[[string]$Row.path] = "$($Row.bytes)|$($Row.sha256)" }
    $Changed = @((@($Old.Keys) + @($New.Keys)) | Sort-Object -Unique | Where-Object {
        -not $Old.ContainsKey($_) -or -not $New.ContainsKey($_) -or [string]$Old[$_] -cne [string]$New[$_]
    })
    if ($Changed.Count -ne 0) { throw "Fresh retry changed protected anchors: $($Changed -join ', ')" }
}

Assert-Leaf $PSCommandPath 'v005 one-use recovery script'
$ActualRecoverySha256 = Get-Sha256 $PSCommandPath
if ($ActualRecoverySha256 -cne $ExpectedRecoverySha256.ToUpperInvariant()) { throw 'Recovery self-hash mismatch' }
$PinnedTools = [ordered]@{
    $Runner = $ExpectedRunnerSha256
    $Validator = $ExpectedValidatorSha256
    $BridgeHeader = $ExpectedBridgeHeaderSha256
    $BridgeSource = $ExpectedBridgeSourceSha256
    $RejectedV003 = $ExpectedRejectedV003Sha256
    $FailedV004 = $ExpectedFailedV004Sha256
    $ParserRegression = $ExpectedParserRegressionSha256
}
foreach ($Path in $PinnedTools.Keys) {
    if ((Get-Sha256 $Path) -cne [string]$PinnedTools[$Path]) { throw "Corrected/preserved tool hash drift: $Path" }
}
if ($PSVersionTable.PSVersion.Major -ne 5) { throw "Recovery requires Windows PowerShell 5.1, found $($PSVersionTable.PSVersion)" }
Assert-NoActiveUnrealProcess
if (Test-Path -LiteralPath $RecoveryRoot) { throw "One-use v005 recovery destination already exists: $RecoveryRoot" }

$ParserOutput = @(& $ParserRegression)
if ($ParserOutput.Count -ne 1 -or [string]$ParserOutput[0] -cne 'PASS__WINDOWS_POWERSHELL_5_1_PNG_IHDR_1920X1080_AND_1300X740_V004') {
    throw 'Pinned PS5.1 PNG parser regression did not pass exactly'
}
$PreservedBefore = Assert-PreservedIncidents
$ExactCause = 'OneFactory screenshot is not 1920x1080: 04_populated_press_starter_with_umg.png=[1300, 740]'
$FirstReceipt = Read-Json (Join-Path $RunsRoot "$FirstStamp\one_factory_actual_player_pie_v001.json") 'First failed receipt'
$SecondReceipt = Read-Json (Join-Path $RunsRoot "$SecondStamp\one_factory_actual_player_pie_v001.json") 'Second failed receipt'
$ThirdReceipt = Read-Json (Join-Path $RunsRoot "$ThirdStamp\one_factory_actual_player_pie_v001.json") 'Third failed receipt'
if (-not (@($FirstReceipt.failures) -contains "module 'unreal' has no attribute 'WidgetBlueprintLibrary'")) { throw 'First incident cause drift' }
if (-not (@($SecondReceipt.failures) -contains $ExactCause)) { throw 'Second incident cause drift' }
$OldUI = $ThirdReceipt.checks.native_ui_capture_viewport_1920x1080.evidence
if ([string]$ThirdReceipt.status -cne 'FAIL__ONE_FACTORY_ACTUAL_PLAYER_PIE_V001' `
        -or -not (@($ThirdReceipt.failures) -contains $ExactCause) `
        -or [string]$OldUI.api -cne 'FSceneViewport.SetViewportSize' `
        -or @($OldUI.reflected_viewport).Count -ne 2 `
        -or [int]$OldUI.reflected_viewport[0] -ne 1920 -or [int]$OldUI.reflected_viewport[1] -ne 1080 `
        -or @($OldUI.actual_player_viewport).Count -ne 2 `
        -or [int]$OldUI.actual_player_viewport[0] -ne 1920 -or [int]$OldUI.actual_player_viewport[1] -ne 1080 `
        -or -not [bool]$OldUI.native_umg_visible_after_resize -or [bool]$OldUI.post_processing `
        -or -not [bool]$ThirdReceipt.map_hash_unchanged -or @($ThirdReceipt.protected.changes).Count -ne 0) {
    throw 'Third incident exact backbuffer-versus-Slate-geometry cause drift'
}

$ProtectedBefore = Get-ProtectedSnapshot
$RunNamesBefore = @(Get-ChildItem -LiteralPath $RunsRoot -Directory | ForEach-Object Name | Sort-Object)
New-Item -ItemType Directory -Path $RecoveryRoot | Out-Null
$PreRetry = [ordered]@{
    '$schema' = 'lineboss/audit/one-factory/actual-player-ui-resolution-incident-recovery-v005/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'READY__THREE_INCIDENTS_AND_V003_V004_EVIDENCE_PRESERVED__ONE_RETRY_NOT_STARTED'
    incident_stamps = @($FirstStamp, $SecondStamp, $ThirdStamp)
    exact_ui_failure = $ExactCause
    third_failure_proof = [ordered]@{
        scene_viewport = @(1920, 1080)
        actual_player_viewport = @(1920, 1080)
        slate_ui_png = @(1300, 740)
        cause = 'FSceneViewport render size does not change SViewport arranged Slate geometry'
    }
    preserved_evidence = $PreservedBefore
    correction = [ordered]@{
        resize_api = 'SWindow.ReshapeWindow'
        query_api = 'SViewport.GetCachedGeometry().GetDrawSize'
        capture_api = 'FScreenshotRequest.RequestScreenshot(bShowUI=true,bRestrictToGameViewport=true)'
        requested_size = @(1920, 1080)
        native_umg_required = $true
        rescale_crop_or_composite = $false
    }
    corrected_validator_sha256 = $ExpectedValidatorSha256
    corrected_runner_sha256 = $ExpectedRunnerSha256
    bridge_header_sha256 = $ExpectedBridgeHeaderSha256
    bridge_source_sha256 = $ExpectedBridgeSourceSha256
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
    if ($NewRunName -in @($FirstStamp, $SecondStamp, $ThirdStamp)) { throw 'Fresh retry reused a preserved incident stamp' }
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
            -or @($UIShot.dimensions).Count -ne 2 `
            -or [int]$UIShot.dimensions[0] -ne 1920 -or [int]$UIShot.dimensions[1] -ne 1080 `
            -or -not [bool]$UIShot.hud_required `
            -or [string]$UICheck.resize_api -cne 'SWindow.ReshapeWindow' `
            -or [string]$UICheck.query_api -cne 'SViewport.GetCachedGeometry().GetDrawSize' `
            -or [string]$UICheck.capture_api -cne 'FScreenshotRequest.RequestScreenshot(bShowUI=true,bRestrictToGameViewport=true)' `
            -or @($UICheck.arranged_game_widget).Count -ne 2 `
            -or [int]$UICheck.arranged_game_widget[0] -ne 1920 -or [int]$UICheck.arranged_game_widget[1] -ne 1080 `
            -or -not [bool]$UICheck.native_umg_visible_after_resize -or [bool]$UICheck.post_processing `
            -or -not [bool]$NewReceipt.map_hash_unchanged -or @($NewReceipt.protected.changes).Count -ne 0) {
        throw 'Fresh retry did not prove native restricted 1920x1080 SViewport/UMG PASS contract'
    }
    Assert-SameSnapshot $ProtectedBefore (Get-ProtectedSnapshot)
    $PreservedAfter = Assert-PreservedIncidents
    Assert-NoActiveUnrealProcess
    $Success = [ordered]@{
        '$schema' = 'lineboss/audit/one-factory/actual-player-ui-resolution-incident-retry-summary-v005/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__EXACTLY_ONE_NATIVE_RESTRICTED_SVIEWPORT_1920X1080_UMG_RETRY_PASSED'
        retry_stamp = $NewRunName
        retry_invocations = 1
        retry_exit_code = $RetryExitCode
        incidents_unchanged = $true
        protected_anchors_unchanged = $true
        map_sha256 = $ExpectedMapSha256
        corrected_validator_sha256 = $ExpectedValidatorSha256
        corrected_runner_sha256 = $ExpectedRunnerSha256
        recovery_script_sha256 = $ActualRecoverySha256
        retry_receipt = Get-Record $NewReceiptPath
        retry_runner_summary = Get-Record $NewSummaryPath
        native_ui_screenshot = $UIShot
        preserved_evidence_after = $PreservedAfter
        content_or_map_package_removals = 0
    }
    Write-Json $RecoverySummary $Success
}
catch {
    $RunNamesAtFailure = @(Get-ChildItem -LiteralPath $RunsRoot -Directory | ForEach-Object Name | Sort-Object)
    $NewRunsAtFailure = @($RunNamesAtFailure | Where-Object { $RunNamesBefore -cnotcontains $_ })
    if ($NewRunsAtFailure.Count -eq 1) { $NewRunName = $NewRunsAtFailure[0] }
    $Failure = [ordered]@{
        '$schema' = 'lineboss/audit/one-factory/actual-player-ui-resolution-incident-retry-summary-v005/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'FAIL__UI_RESOLUTION_INCIDENT_ONE_USE_RETRY_V005'
        failure = $_.Exception.Message
        retry_stamp = $NewRunName
        retry_invocations = 1
        retry_exit_code = $RetryExitCode
        incidents = Assert-PreservedIncidents
        map_sha256 = Get-Sha256 (Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Maps\LB_MoorcrossWorks_OneFactory_v001.umap')
        recovery_script_sha256 = $ActualRecoverySha256
        content_or_map_package_removals = 0
    }
    Write-Json $RecoverySummary $Failure
    throw
}

Write-Host 'PASS: preserved all three incidents and completed exactly one native restricted 1920x1080 SViewport/UMG retry.'
Write-Host "Recovery summary: $RecoverySummary"
