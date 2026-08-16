[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Fa-f0-9]{64}$')]
    [string]$ExpectedRunnerSha256,
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8',
    [switch]$SkipEditorBuild,
    [ValidateRange(1, 86400)][int]$BuildTimeoutSeconds = 1800,
    [ValidateRange(1, 86400)][int]$LivePieTimeoutSeconds = 900
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Build = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
$Validator = Join-Path $Root 'Scripts\validate_one_factory_actual_player_pie_v001.py'
$Map = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Maps\LB_MoorcrossWorks_OneFactory_v001.umap'
$CreateReceipt = Join-Path $Root 'Saved\Audits\OneFactory\v001\one_factory_shell_create_v001.json'
$ShellValidationReceipt = Join-Path $Root 'Saved\Audits\OneFactory\v001\one_factory_shell_validation_v001.json'

$ExpectedValidatorSha256 = '9DFEEE6D6C29B5D96EB6650F38494854BDA780BFDDC09A146150118FF3610099'
$ExpectedMapSha256 = '750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682'
$ExpectedCreateReceiptSha256 = '7D26748BBCE53A11CFE6EEC71FFEE54CBC1504EA48950CADC3E236B2AE16DDB7'
$ExpectedShellValidationReceiptSha256 = '26F332294FA1640CDACA1D73F23C2F3B8185A6F3EA67A1DEA976AFB09632791E'
$ExpectedMapPackage = '/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001'
$ExpectedLiveSchema = 'lineboss/audit/one-factory/actual-player-pie-v001/v1'
$ExpectedLiveStatus = 'PASS__ONE_FACTORY_ACTUAL_PLAYER_NATIVE_UMG_PRESS_STARTER_REAL_RHI_PIE_V001'
$ExpectedCreateStatus = 'PASS__ONE_FACTORY_NATIVE_HISM_SHELL_ONE_BOOTSTRAP_ONE_PRESS_AUTHORITY_ZERO_PRODUCTION_MACHINE_OR_WIP'
$ExpectedShellValidationStatus = 'PASS__FRESH_RELOAD_ONE_FACTORY_NATIVE_HISM_SHELL_EXACT_AUTHORITIES_ZERO_PRODUCTION_MACHINE_OR_WIP'

$ExpectedScreenshots = @(
    '01_empty_factory_management_overview.png',
    '02_populated_press_starter_wide_overview.png',
    '03_press_train_dispatch_agv_close.png',
    '04_populated_press_starter_with_umg.png'
)
$ExpectedChecks = @(
    'fresh_loaded_editor_shell_before_pie',
    'actual_player_empty_shell',
    'safe_commission_rejection_before_creation',
    'fixed_5000k_lighting_and_exposure',
    'new_factory_via_native_umg_hud_route',
    'native_only_press_starter_7_roles_8_batches_268_instances',
    'populated_press_wide_render',
    'programme_change_and_commission_success_via_umg_hud_route',
    'press_train_dispatch_agv_close_render',
    'populated_native_umg_visible',
    'native_ui_capture_viewport_1920x1080',
    'pie_transient_pair_destroyed_and_editor_shell_retained',
    'protected_anchors_unchanged'
)

$CriticalProtected = [ordered]@{
    'Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap' = '26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6'
    'Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap' = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'
    'Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap' = '8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F'
    'Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap' = '2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069'
    'Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap' = $ExpectedMapSha256
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
    'Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h',
    'Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp',
    'Source/LineBossCarFactory/LBManagementPawn.h',
    'Source/LineBossCarFactory/LBManagementPawn.cpp',
    'Source/LineBossCarFactory/LBControlRoomHUD.h',
    'Source/LineBossCarFactory/LBControlRoomHUD.cpp',
    'Source/LineBossCarFactory/LBManagementRootWidget.h',
    'Source/LineBossCarFactory/LBManagementRootWidget.cpp'
)

function Assert-Leaf {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label is missing: $Path"
    }
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    Assert-Leaf $Path 'Hash target'
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}

function Get-ProjectRelativePath {
    param([Parameter(Mandatory = $true)][string]$Path)
    $RootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $Full = [IO.Path]::GetFullPath($Path)
    $Prefix = $RootFull + [IO.Path]::DirectorySeparatorChar
    if (-not $Full.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes the project root: $Full"
    }
    return $Full.Substring($Prefix.Length).Replace('\', '/')
}

function Resolve-ProjectPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $Candidate = if ([IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $Root $Path }
    $Resolved = [IO.Path]::GetFullPath($Candidate)
    [void](Get-ProjectRelativePath $Resolved)
    return $Resolved
}

function Assert-NoActiveUnrealProcess {
    $Names = @(
        'UnrealEditor',
        'UnrealEditor-Cmd',
        'UnrealBuildTool',
        'AutomationTool',
        'RunUAT',
        'ShaderCompileWorker'
    )
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $Names -contains $_.ProcessName
    })
    if ($Active.Count -gt 0) {
        $Rows = @($Active | Sort-Object ProcessName, Id | ForEach-Object {
            "$($_.ProcessName)[$($_.Id)]"
        })
        throw "Refusing actual-player validation while Unreal/build processes are active: $($Rows -join ', ')"
    }
}

function Assert-JsonProperty {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Label
    )
    if ($null -eq $Object -or -not (@($Object.PSObject.Properties.Name) -ccontains $Name)) {
        throw "$Label is missing required JSON property '$Name'"
    }
}

function Read-JsonLeaf {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )
    Assert-Leaf $Path $Label
    try {
        return (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json)
    }
    catch {
        throw "$Label is not valid JSON: $Path ($($_.Exception.Message))"
    }
}

function Get-HashRecord {
    param([Parameter(Mandatory = $true)][string]$Path)
    $Full = [IO.Path]::GetFullPath($Path)
    if (-not (Test-Path -LiteralPath $Full -PathType Leaf)) {
        return [ordered]@{
            relative_path = Get-ProjectRelativePath $Full
            exists = $false
            bytes = $null
            sha256 = $null
        }
    }
    $Item = Get-Item -LiteralPath $Full
    return [ordered]@{
        relative_path = Get-ProjectRelativePath $Full
        exists = $true
        bytes = [Int64]$Item.Length
        sha256 = Get-Sha256 $Full
    }
}

function Get-ProtectedSnapshot {
    $Paths = New-Object 'System.Collections.Generic.List[string]'
    foreach ($Relative in $CriticalProtected.Keys) {
        [void]$Paths.Add((Join-Path $Root $Relative.Replace('/', '\')))
    }
    foreach ($Path in @($CreateReceipt, $ShellValidationReceipt, $PSCommandPath, $Validator)) {
        [void]$Paths.Add([IO.Path]::GetFullPath($Path))
    }
    foreach ($Relative in $ProtectedSource) {
        [void]$Paths.Add((Join-Path $Root $Relative.Replace('/', '\')))
    }
    $ConfigRoot = Join-Path $Root 'Config'
    if (-not (Test-Path -LiteralPath $ConfigRoot -PathType Container)) {
        throw "Protected Config directory is missing: $ConfigRoot"
    }
    foreach ($Item in @(Get-ChildItem -LiteralPath $ConfigRoot -Recurse -File -ErrorAction Stop)) {
        [void]$Paths.Add($Item.FullName)
    }
    $SaveRoot = Join-Path $Root 'Saved\SaveGames'
    if (Test-Path -LiteralPath $SaveRoot -PathType Container) {
        foreach ($Item in @(Get-ChildItem -LiteralPath $SaveRoot -Recurse -File -ErrorAction Stop)) {
            [void]$Paths.Add($Item.FullName)
        }
    }
    $Rows = @()
    foreach ($Path in @($Paths | Sort-Object -Unique)) {
        $Rows += Get-HashRecord $Path
    }
    foreach ($Relative in $CriticalProtected.Keys) {
        $Match = @($Rows | Where-Object { [string]$_.relative_path -ceq $Relative })
        if ($Match.Count -ne 1 -or -not [bool]$Match[0].exists `
                -or [string]$Match[0].sha256 -cne [string]$CriticalProtected[$Relative]) {
            throw "Protected anchor hash drift: $Relative"
        }
    }
    return @($Rows)
}

function Get-ProtectedChanges {
    param(
        [Parameter(Mandatory = $true)]$Before,
        [Parameter(Mandatory = $true)]$After
    )
    $Old = @{}
    $New = @{}
    foreach ($Row in @($Before)) { $Old[[string]$Row.relative_path] = $Row }
    foreach ($Row in @($After)) { $New[[string]$Row.relative_path] = $Row }
    $Changes = @()
    foreach ($Path in @((@($Old.Keys) + @($New.Keys)) | Sort-Object -Unique)) {
        if (-not $Old.ContainsKey($Path)) {
            $Changes += [ordered]@{ path = $Path; change = 'ADDED'; before = $null; after = $New[$Path] }
            continue
        }
        if (-not $New.ContainsKey($Path)) {
            $Changes += [ordered]@{ path = $Path; change = 'REMOVED'; before = $Old[$Path]; after = $null }
            continue
        }
        $BeforeRow = $Old[$Path]
        $AfterRow = $New[$Path]
        if ([bool]$BeforeRow.exists -ne [bool]$AfterRow.exists `
                -or [string]$BeforeRow.bytes -cne [string]$AfterRow.bytes `
                -or [string]$BeforeRow.sha256 -cne [string]$AfterRow.sha256) {
            $Changes += [ordered]@{ path = $Path; change = 'CHANGED'; before = $BeforeRow; after = $AfterRow }
        }
    }
    return @($Changes)
}

function Assert-ProtectedCheckpoint {
    param(
        [Parameter(Mandatory = $true)]$Baseline,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $Current = Get-ProtectedSnapshot
    $Changes = @(Get-ProtectedChanges $Baseline $Current)
    if ($Changes.Count -ne 0) {
        $Preview = @($Changes | Select-Object -First 12 | ForEach-Object {
            "$($_.change):$($_.path)"
        })
        throw "$Label changed protected map/Config/SaveGames/source/tooling files: $($Preview -join ', ')"
    }
    return [ordered]@{
        label = $Label
        checked_utc = (Get-Date).ToUniversalTime().ToString('o')
        file_count = @($Current).Count
        changes = @()
    }
}

function ConvertTo-ProcessArgument {
    param([AllowEmptyString()][string]$Value)
    if ($Value.Contains('"')) {
        throw "Process argument unexpectedly contains a double quote: $Value"
    }
    if ($Value.Length -eq 0) { return '""' }
    if ($Value -match '\s') { return ('"{0}"' -f $Value) }
    return $Value
}

function Invoke-GuardedProcess {
    [CmdletBinding(DefaultParameterSetName = 'Arguments')]
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(ParameterSetName = 'Arguments')][string[]]$Arguments = @(),
        [Parameter(Mandatory = $true, ParameterSetName = 'Raw')][string]$RawArgumentLine,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$StdoutPath,
        [Parameter(Mandatory = $true)][string]$StderrPath,
        [Parameter(Mandatory = $true)][ValidateRange(1, 86400)][int]$TimeoutSeconds
    )
    Assert-Leaf $FilePath "$Label executable"
    foreach ($Log in @($StdoutPath, $StderrPath)) {
        if (Test-Path -LiteralPath $Log) { throw "$Label refuses to overwrite log: $Log" }
    }
    $ArgumentLine = if ($PSCmdlet.ParameterSetName -eq 'Raw') {
        $RawArgumentLine
    }
    else {
        (@($Arguments | ForEach-Object { ConvertTo-ProcessArgument ([string]$_) }) -join ' ')
    }
    $Started = (Get-Date).ToUniversalTime()
    $Start = @{
        FilePath = $FilePath
        WorkingDirectory = $WorkingDirectory
        RedirectStandardOutput = $StdoutPath
        RedirectStandardError = $StderrPath
        WindowStyle = 'Hidden'
        PassThru = $true
    }
    if (-not [string]::IsNullOrWhiteSpace($ArgumentLine)) { $Start.ArgumentList = $ArgumentLine }
    $Process = Start-Process @Start
    $null = $Process.Handle
    $Deadline = $Started.AddSeconds($TimeoutSeconds)
    while (-not $Process.HasExited -and (Get-Date).ToUniversalTime() -lt $Deadline) {
        [void]$Process.WaitForExit(500)
    }
    $TimedOut = -not $Process.HasExited
    $KillLog = $null
    if ($TimedOut) {
        $KillLog = Join-Path (Split-Path -Parent $StdoutPath) 'timeout_process_tree.log'
        $Messages = @()
        $TaskKill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
        try { $Messages += (& $TaskKill /PID $Process.Id /T /F 2>&1 | Out-String) }
        catch { $Messages += "taskkill failed: $($_.Exception.Message)" }
        try { if (-not $Process.HasExited) { $Process.Kill() } }
        catch { $Messages += "Process.Kill failed: $($_.Exception.Message)" }
        try { [void]$Process.WaitForExit(15000) }
        catch { $Messages += "Final wait failed: $($_.Exception.Message)" }
        [IO.File]::WriteAllText($KillLog, ($Messages -join "`r`n"), (New-Object Text.UTF8Encoding($false)))
    }
    else {
        $Process.WaitForExit()
    }
    $Finished = (Get-Date).ToUniversalTime()
    return [pscustomobject][ordered]@{
        label = $Label
        executable = $FilePath
        argument_line = $ArgumentLine
        started_utc = $Started.ToString('o')
        finished_utc = $Finished.ToString('o')
        duration_seconds = [Math]::Round(($Finished - $Started).TotalSeconds, 3)
        timeout_seconds = $TimeoutSeconds
        timed_out = $TimedOut
        exit_code = if ($Process.HasExited) { [int]$Process.ExitCode } else { $null }
        stdout_log = $StdoutPath
        stderr_log = $StderrPath
        timeout_kill_log = $KillLog
    }
}

function Assert-ProcessSucceeded {
    param([Parameter(Mandatory = $true)]$Result)
    if ([bool]$Result.timed_out) {
        throw "$($Result.label) exceeded its timeout; logs: $($Result.stdout_log), $($Result.stderr_log)"
    }
    if ($null -eq $Result.exit_code -or [int]$Result.exit_code -ne 0) {
        throw "$($Result.label) failed with exit code $($Result.exit_code); logs: $($Result.stdout_log), $($Result.stderr_log)"
    }
}

function Wait-StableLeaf {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Int64]$MinimumBytes = 1
    )
    $Previous = $null
    for ($Attempt = 1; $Attempt -le 24; $Attempt++) {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            try {
                $Item = Get-Item -LiteralPath $Path
                $Hash = Get-Sha256 $Path
                if ([Int64]$Item.Length -ge $MinimumBytes) {
                    $Signature = "$($Item.Length)|$($Item.LastWriteTimeUtc.Ticks)|$Hash"
                    if ($Signature -ceq $Previous) { return $Hash }
                    $Previous = $Signature
                }
            }
            catch { $Previous = $null }
        }
        Start-Sleep -Milliseconds 250
    }
    throw "File did not become stable and readable: $Path"
}

function Get-PngDimensions {
    param([Parameter(Mandatory = $true)][string]$Path)
    $Stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
        $Header = New-Object byte[] 24
        $Read = $Stream.Read($Header, 0, 24)
    }
    finally { $Stream.Dispose() }
    $Signature = @(137, 80, 78, 71, 13, 10, 26, 10)
    if ($Read -ne 24) { throw "PNG header is truncated: $Path" }
    for ($Index = 0; $Index -lt 8; $Index++) {
        if ([int]$Header[$Index] -ne $Signature[$Index]) { throw "Not a PNG: $Path" }
    }
    if ([Text.Encoding]::ASCII.GetString($Header, 12, 4) -cne 'IHDR') {
        throw "PNG first chunk is not IHDR: $Path"
    }
    $Width = [int](([int64]$Header[16] * 16777216) + ([int64]$Header[17] * 65536) + ([int64]$Header[18] * 256) + [int64]$Header[19])
    $Height = [int](([int64]$Header[20] * 16777216) + ([int64]$Header[21] * 65536) + ([int64]$Header[22] * 256) + [int64]$Header[23])
    return [pscustomobject]@{ width = $Width; height = $Height }
}

function Assert-FrozenShellReceipts {
    if ((Get-Sha256 $Map) -cne $ExpectedMapSha256) { throw 'Frozen OneFactory map hash drift' }
    if ((Get-Sha256 $CreateReceipt) -cne $ExpectedCreateReceiptSha256) { throw 'Shell creation receipt hash drift' }
    if ((Get-Sha256 $ShellValidationReceipt) -cne $ExpectedShellValidationReceiptSha256) { throw 'Shell validation receipt hash drift' }
    $Create = Read-JsonLeaf $CreateReceipt 'OneFactory shell creation receipt'
    $Validation = Read-JsonLeaf $ShellValidationReceipt 'OneFactory shell validation receipt'
    if ([string]$Create.'$schema' -cne 'lineboss/audit/one-factory/shell-create-v001/v1' `
            -or [string]$Create.status -cne $ExpectedCreateStatus `
            -or [string]$Create.map -cne $ExpectedMapPackage `
            -or [string]$Create.map_sha256 -cne $ExpectedMapSha256 `
            -or @($Create.failures).Count -ne 0) {
        throw 'Shell creation receipt semantic contract drift'
    }
    if ([string]$Validation.'$schema' -cne 'lineboss/audit/one-factory/shell-validation-v001/v1' `
            -or [string]$Validation.status -cne $ExpectedShellValidationStatus `
            -or [string]$Validation.map -cne $ExpectedMapPackage `
            -or [string]$Validation.map_sha256 -cne $ExpectedMapSha256 `
            -or @($Validation.failures).Count -ne 0 `
            -or [bool]$Validation.writes_to_content_config_or_saves) {
        throw 'Shell independent-validation receipt semantic contract drift'
    }
    return [ordered]@{
        map_sha256 = $ExpectedMapSha256
        creation_receipt_sha256 = $ExpectedCreateReceiptSha256
        validation_receipt_sha256 = $ExpectedShellValidationReceiptSha256
    }
}

function Assert-LiveReceipt {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedCaptureRoot
    )
    $ReceiptHash = Wait-StableLeaf $Path 512
    $Live = Read-JsonLeaf $Path 'OneFactory actual-player PIE receipt'
    foreach ($Property in @('$schema', 'status', 'failures', 'map', 'map_sha256_before',
            'map_sha256_after', 'map_hash_unchanged', 'validator_script_sha256',
            'real_rhi_contract', 'checks', 'screenshots', 'protected')) {
        Assert-JsonProperty $Live $Property 'OneFactory actual-player PIE receipt'
    }
    if ([string]$Live.'$schema' -cne $ExpectedLiveSchema -or [string]$Live.status -cne $ExpectedLiveStatus) {
        throw "Actual-player receipt schema/status mismatch: $($Live.'$schema') / $($Live.status)"
    }
    if (@($Live.failures).Count -ne 0) { throw "Actual-player receipt contains failures: $(@($Live.failures) -join '; ')" }
    if ([string]$Live.map -cne $ExpectedMapPackage `
            -or [string]$Live.map_sha256_before -cne $ExpectedMapSha256 `
            -or [string]$Live.map_sha256_after -cne $ExpectedMapSha256 `
            -or $Live.map_hash_unchanged -isnot [bool] -or -not [bool]$Live.map_hash_unchanged) {
        throw 'Actual-player receipt does not bind the exact unchanged OneFactory map'
    }
    if ([string]$Live.validator_script_sha256 -cne $ExpectedValidatorSha256) {
        throw 'Actual-player receipt validator hash drift'
    }
    if ([bool]$Live.real_rhi_contract.command_line_has_nullrhi `
            -or @($Live.real_rhi_contract.requested_resolution).Count -ne 2 `
            -or [int]$Live.real_rhi_contract.requested_resolution[0] -ne 1920 `
            -or [int]$Live.real_rhi_contract.requested_resolution[1] -ne 1080 `
            -or [string]$Live.real_rhi_contract.render_proof -cne `
                'three completed high-res tasks plus one native UI-inclusive capture restricted to an arranged 1920x1080 PIE SViewport' `
            -or -not [bool]$Live.pie_transient_only `
            -or [bool]$Live.writes_to_content_config_source_or_saves_requested) {
        throw 'Actual-player receipt real-RHI/transient/no-save contract drift'
    }
    if ([string]$Live.real_rhi_contract.ui_capture_resize_bridge -cne `
            '/Script/LineBossCarFactory.LBOneFactoryCaptureBridge') {
        throw 'Actual-player receipt native UI-capture bridge drift'
    }
    foreach ($CheckName in $ExpectedChecks) {
        Assert-JsonProperty $Live.checks $CheckName 'OneFactory actual-player checks'
        if ($Live.checks.$CheckName.passed -isnot [bool] -or -not [bool]$Live.checks.$CheckName.passed) {
            throw "Actual-player required check did not pass: $CheckName"
        }
    }
    $UICapture = $Live.checks.native_ui_capture_viewport_1920x1080.evidence
    if ([string]$UICapture.bridge -cne '/Script/LineBossCarFactory.LBOneFactoryCaptureBridge' `
            -or [string]$UICapture.resize_api -cne 'SWindow.ReshapeWindow' `
            -or [string]$UICapture.query_api -cne 'SViewport.GetCachedGeometry().GetDrawSize' `
            -or [string]$UICapture.capture_api -cne `
                'FScreenshotRequest.RequestScreenshot(bShowUI=true,bRestrictToGameViewport=true)' `
            -or @($UICapture.arranged_game_widget).Count -ne 2 `
            -or [int]$UICapture.arranged_game_widget[0] -ne 1920 `
            -or [int]$UICapture.arranged_game_widget[1] -ne 1080 `
            -or @($UICapture.actual_player_viewport).Count -ne 2 `
            -or [int]$UICapture.actual_player_viewport[0] -le 0 `
            -or [int]$UICapture.actual_player_viewport[1] -le 0 `
            -or -not [bool]$UICapture.native_umg_visible_after_resize `
            -or [bool]$UICapture.post_processing) {
        throw 'Actual-player receipt does not prove native restricted 1920x1080 SViewport/UMG capture sizing'
    }
    $Starter = $Live.checks.native_only_press_starter_7_roles_8_batches_268_instances.evidence
    if (@($Starter.roles).Count -ne 7 -or @($Starter.batches).Count -ne 8 `
            -or [int]$Starter.visible_instance_count -ne 268 `
            -or [int]$Starter.visual_batch_count -ne 8 `
            -or [bool]$Starter.represents_process_wip `
            -or @($Starter.forbidden_reference_hits).Count -ne 0 `
            -or @($Starter.production_actor_hits).Count -ne 0 `
            -or @($Starter.process_wip_hits).Count -ne 0) {
        throw 'Actual-player receipt does not prove 7 roles / 8 HISM batches / 268 visible / zero WIP'
    }
    $RoleCounts = @($Starter.roles | ForEach-Object { [int]$_.instances })
    $BatchCounts = @($Starter.batches | ForEach-Object { [int]$_.instances })
    if (($RoleCounts | Measure-Object -Sum).Sum -ne 268 `
            -or ($BatchCounts | Measure-Object -Sum).Sum -ne 268 `
            -or @($Starter.roles | Where-Object { [int]$_.instances -ne [int]$_.expected_instances }).Count -ne 0) {
        throw 'Actual-player role/batch instance totals do not independently sum to 268'
    }
    if (@($Live.protected.changes).Count -ne 0) {
        throw 'Actual-player validator reports protected-file changes'
    }

    $ShotProperties = @($Live.screenshots.PSObject.Properties)
    if ($ShotProperties.Count -ne 4) { throw "Expected exactly four screenshots, found $($ShotProperties.Count)" }
    $ActualNames = @($ShotProperties.Name | Sort-Object)
    $ExpectedNames = @($ExpectedScreenshots | Sort-Object)
    if (@(Compare-Object $ExpectedNames $ActualNames -CaseSensitive).Count -ne 0) {
        throw "Screenshot name inventory drift: $($ActualNames -join ', ')"
    }
    $CaptureFull = [IO.Path]::GetFullPath($ExpectedCaptureRoot).TrimEnd('\', '/')
    $ShotEvidence = @()
    foreach ($Name in $ExpectedScreenshots) {
        $Record = $Live.screenshots.$Name
        $Full = Resolve-ProjectPath ([string]$Record.path) "Screenshot $Name"
        $ExpectedFull = [IO.Path]::GetFullPath((Join-Path $CaptureFull $Name))
        if (-not $Full.Equals($ExpectedFull, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Screenshot escaped its run-specific capture directory: $Full"
        }
        $Hash = Wait-StableLeaf $Full 32768
        $Item = Get-Item -LiteralPath $Full
        $Dimensions = Get-PngDimensions $Full
        $HudExpected = $Name -ceq '04_populated_press_starter_with_umg.png'
        if ($Dimensions.width -ne 1920 -or $Dimensions.height -ne 1080 `
                -or [string]$Record.sha256 -cne $Hash `
                -or [Int64]$Record.bytes -ne [Int64]$Item.Length `
                -or @($Record.dimensions).Count -ne 2 `
                -or [int]$Record.dimensions[0] -ne 1920 `
                -or [int]$Record.dimensions[1] -ne 1080 `
                -or $Record.real_rhi -isnot [bool] -or -not [bool]$Record.real_rhi `
                -or $Record.hud_required -isnot [bool] -or [bool]$Record.hud_required -ne $HudExpected) {
            throw "Screenshot evidence contract drift: $Name"
        }
        $ShotEvidence += [ordered]@{
            name = $Name
            path = $Full
            bytes = [Int64]$Item.Length
            sha256 = $Hash
            dimensions = @(1920, 1080)
            hud_required = $HudExpected
        }
    }
    return [ordered]@{
        receipt_path = $Path
        receipt_sha256 = $ReceiptHash
        status = [string]$Live.status
        map_hash_unchanged = $true
        required_checks = @($ExpectedChecks)
        starter_roles = @($Starter.roles)
        starter_batches = @($Starter.batches)
        visible_instances = 268
        screenshots = @($ShotEvidence)
    }
}

foreach ($Required in @($Project, $Editor, $Validator, $Map, $CreateReceipt, $ShellValidationReceipt)) {
    Assert-Leaf $Required 'OneFactory actual-player prerequisite'
}
if (-not $SkipEditorBuild) { Assert-Leaf $Build 'Unreal editor build script' }
$ExpectedRunnerSha256 = $ExpectedRunnerSha256.ToUpperInvariant()
$ActualRunnerSha256 = Get-Sha256 $PSCommandPath
if ($ActualRunnerSha256 -cne $ExpectedRunnerSha256) {
    throw "Runner self-hash mismatch: expected $ExpectedRunnerSha256, actual $ActualRunnerSha256"
}
if ((Get-Sha256 $Validator) -cne $ExpectedValidatorSha256) {
    throw 'Frozen OneFactory actual-player validator script hash drift'
}
Assert-NoActiveUnrealProcess
$Prerequisites = Assert-FrozenShellReceipts

$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$RunRoot = Join-Path $Root "Saved\Audits\OneFactory\v001\ActualPlayerPIE\Runs\$Stamp"
$LogRoot = Join-Path $RunRoot 'Logs'
$CaptureRoot = Join-Path $Root "Saved\ValidationScreenshots\OneFactory\v001\ActualPlayerPIE\$Stamp"
$LiveReceipt = Join-Path $RunRoot 'one_factory_actual_player_pie_v001.json'
$SummaryPath = Join-Path $RunRoot 'one_factory_actual_player_pie_run_summary_v001.json'
if ((Test-Path -LiteralPath $RunRoot) -or (Test-Path -LiteralPath $CaptureRoot)) {
    throw "Fresh run destination already exists for stamp $Stamp"
}
New-Item -ItemType Directory -Path $LogRoot | Out-Null

$Baseline = Get-ProtectedSnapshot
$Missing = @($Baseline | Where-Object { -not [bool]$_.exists })
if ($Missing.Count -ne 0) {
    throw "Required protected files are missing: $(@($Missing.relative_path) -join ', ')"
}
$Processes = New-Object System.Collections.Generic.List[object]
$Checkpoints = New-Object System.Collections.Generic.List[object]
$Failures = New-Object System.Collections.Generic.List[string]
$LiveEvidence = $null
$Completed = $false
$PreviousStamp = [Environment]::GetEnvironmentVariable('LB_ONE_FACTORY_ACTUAL_PLAYER_STAMP', 'Process')
[Environment]::SetEnvironmentVariable('LB_ONE_FACTORY_ACTUAL_PLAYER_STAMP', $Stamp, 'Process')

try {
    if (-not $SkipEditorBuild) {
        $ComSpec = [Environment]::GetEnvironmentVariable('ComSpec', 'Process')
        Assert-Leaf $ComSpec 'Windows command processor'
        $RawBuildArguments = '/d /s /c ""{0}" LineBossCarFactoryEditor Win64 Development "-Project={1}" -WaitMutex -NoHotReloadFromIDE"' -f $Build, $Project
        $BuildResult = Invoke-GuardedProcess -Label 'LineBossCarFactoryEditor Development build' `
            -FilePath $ComSpec -RawArgumentLine $RawBuildArguments -WorkingDirectory $Root `
            -StdoutPath (Join-Path $LogRoot 'editor_build.stdout.log') `
            -StderrPath (Join-Path $LogRoot 'editor_build.stderr.log') `
            -TimeoutSeconds $BuildTimeoutSeconds
        [void]$Processes.Add($BuildResult)
        Assert-ProcessSucceeded $BuildResult
        [void]$Checkpoints.Add((Assert-ProtectedCheckpoint $Baseline 'After editor build'))
    }

    $ValidatorForUnreal = $Validator.Replace('\', '/')
    $Arguments = @(
        $Project,
        "-ExecutePythonScript=$ValidatorForUnreal",
        '-unattended',
        '-nop4',
        '-nosplash',
        '-nosound',
        '-windowed',
        '-RenderOffscreen',
        '-ResX=1920',
        '-ResY=1080',
        '-NoAutoSave',
        '-NoSaveOnExit',
        '-stdout',
        '-FullStdOutLogOutput'
    )
    if (@($Arguments | Where-Object { $_ -match '(?i)nullrhi' }).Count -ne 0) {
        throw 'Internal guard rejected NullRHI in the OneFactory actual-player argument set'
    }
    $LiveResult = Invoke-GuardedProcess -Label 'OneFactory actual-player native-UMG real-RHI PIE' `
        -FilePath $Editor -Arguments $Arguments -WorkingDirectory $Root `
        -StdoutPath (Join-Path $LogRoot 'actual_player_pie.stdout.log') `
        -StderrPath (Join-Path $LogRoot 'actual_player_pie.stderr.log') `
        -TimeoutSeconds $LivePieTimeoutSeconds
    [void]$Processes.Add($LiveResult)
    Assert-ProcessSucceeded $LiveResult
    $LiveEvidence = Assert-LiveReceipt $LiveReceipt $CaptureRoot
    if ((Get-Sha256 $Map) -cne $ExpectedMapSha256) {
        throw 'Saved OneFactory map hash changed after actual-player PIE'
    }
    [void]$Checkpoints.Add((Assert-ProtectedCheckpoint $Baseline 'After real-RHI actual-player PIE'))
    $Completed = $true
}
catch {
    [void]$Failures.Add($_.Exception.Message)
}
finally {
    if ($null -eq $PreviousStamp) {
        [Environment]::SetEnvironmentVariable('LB_ONE_FACTORY_ACTUAL_PLAYER_STAMP', $null, 'Process')
    }
    else {
        [Environment]::SetEnvironmentVariable('LB_ONE_FACTORY_ACTUAL_PLAYER_STAMP', $PreviousStamp, 'Process')
    }
    $After = $null
    $FinalChanges = @()
    try {
        $After = Get-ProtectedSnapshot
        $FinalChanges = @(Get-ProtectedChanges $Baseline $After)
        if ($FinalChanges.Count -ne 0) {
            [void]$Failures.Add("Final protected comparison found changes: $(@($FinalChanges.path) -join ', ')")
        }
    }
    catch { [void]$Failures.Add("Final protected snapshot failed: $($_.Exception.Message)") }
    try {
        Assert-NoActiveUnrealProcess
    }
    catch { [void]$Failures.Add("Process cleanup gate failed: $($_.Exception.Message)") }

    $Passed = $Completed -and $Failures.Count -eq 0
    $Summary = [ordered]@{
        '$schema' = 'lineboss/audit/one-factory/actual-player-pie-run-v001/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = if ($Passed) { 'PASS__ONE_FACTORY_ACTUAL_PLAYER_REAL_RHI_NATIVE_UMG_RUN_V001' } else { 'FAIL__ONE_FACTORY_ACTUAL_PLAYER_REAL_RHI_RUN_V001' }
        failures = $Failures.ToArray()
        stamp = $Stamp
        project = $Project
        map = $ExpectedMapPackage
        expected_map_sha256 = $ExpectedMapSha256
        current_map_sha256 = if (Test-Path -LiteralPath $Map -PathType Leaf) { Get-Sha256 $Map } else { $null }
        runner = [ordered]@{ path = $PSCommandPath; sha256 = $ActualRunnerSha256; expected_sha256_argument = $ExpectedRunnerSha256 }
        validator = [ordered]@{ path = $Validator; sha256 = if (Test-Path -LiteralPath $Validator -PathType Leaf) { Get-Sha256 $Validator } else { $null }; expected_sha256 = $ExpectedValidatorSha256 }
        skip_editor_build = [bool]$SkipEditorBuild
        real_rhi = $true
        nullrhi_forbidden = $true
        requested_resolution = @(1920, 1080)
        no_content_save_requested = $true
        prerequisites = $Prerequisites
        processes = $Processes.ToArray()
        checkpoints = $Checkpoints.ToArray()
        live_evidence = $LiveEvidence
        protected_before = $Baseline
        protected_after = $After
        protected_changes = $FinalChanges
        content_config_maps_saves_or_pinned_source_changed = ($FinalChanges.Count -ne 0)
        run_root = $RunRoot
        capture_root = $CaptureRoot
        receipt = $LiveReceipt
    }
    [IO.File]::WriteAllText(
        $SummaryPath,
        (($Summary | ConvertTo-Json -Depth 20) + "`n"),
        (New-Object Text.UTF8Encoding($false))
    )
    if (-not $Passed) {
        throw "OneFactory actual-player PIE validation failed closed: $($Failures -join '; '). Evidence: $SummaryPath"
    }
}

Write-Host 'PASS: OneFactory actual-player native UMG / Press starter real-RHI PIE validation.'
Write-Host "Summary: $SummaryPath"
Write-Host "Screenshots: $CaptureRoot"
