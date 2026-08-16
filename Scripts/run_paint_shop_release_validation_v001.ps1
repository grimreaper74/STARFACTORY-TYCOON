[CmdletBinding()]
param(
    [switch]$SkipEditorBuild
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Engine = 'C:\Program Files\Epic Games\UE_5.8'
$Editor = Join-Path $Engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Build = Join-Path $Engine 'Engine\Build\BatchFiles\Build.bat'
$ValidatorScript = Join-Path $Root 'Scripts\validate_paint_shop_actual_player_edcoat_pie_v001.py'

$CreateReceipt = Join-Path $Root 'Saved\Audits\PaintShop\Experimental_v001\paint_shop_prototype_map_create_v001.json'
$ValidationReceipt = Join-Path $Root 'Saved\Audits\PaintShop\Experimental_v001\paint_shop_prototype_map_validation_v001.json'
$PaintMap = Join-Path $Root 'Content\LineBoss\PaintShop\Experimental\v001\Maps\LB_PaintShop_Prototype_v001.umap'
$PressV913Map = Join-Path $Root 'Content\LineBoss\Maps\LB_PressShop_RebuildFromLorry_v20260810_v913.umap'
$BodyV005Map = Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001\Maps\LB_BodyShop_Prototype_v001.umap'
$BodyWeldHeader = Join-Path $Root 'Source\LineBossCarFactory\LBBodyWeldLineActor.h'
$BodyWeldSource = Join-Path $Root 'Source\LineBossCarFactory\LBBodyWeldLineActor.cpp'
$ECoatHeader = Join-Path $Root 'Source\LineBossCarFactory\LBECoatLineActor.h'
$ECoatSource = Join-Path $Root 'Source\LineBossCarFactory\LBECoatLineActor.cpp'

$ExpectedCreateSchema = 'lineboss/audit/paint-shop/prototype-map-create-v001/v1'
$ExpectedCreateStatus = 'PASS__ISOLATED_PAINT_SHOP_ONE_BOOTSTRAP_ZERO_MAP_OWNED_PRODUCTION'
$ExpectedValidationSchema = 'lineboss/audit/paint-shop/prototype-map-validation-v001/v1'
$ExpectedValidationStatus = 'PASS__FRESH_RELOAD_PAINT_SHOP_PROTOTYPE_MAP_V001'
$ExpectedLiveSchema = 'lineboss/audit/paint-shop/actual-player-edcoat-pie-v001/v1'
$ExpectedLiveStatus = 'PASS__PAINT_SHOP_ACTUAL_PLAYER_ED_COAT_PIE_V001'
$ExpectedMapSha256 = '2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069'
$ExpectedCreateReceiptSha256 = '4E65E671CB25D8615F3A775B1697E7D72C523D58FFA7481356A5BF8D5941AC09'

$BuildTimeoutSeconds = 1800
$AutomationTimeoutSeconds = 1800
$LivePieTimeoutSeconds = 900

$ExpectedTests = @(
    'LineBoss.PaintShop.Experimental.BuildAuthority.ApprovedEDCoatPlacement',
    'LineBoss.PaintShop.Experimental.BuildAuthority.BuildFindAndCapture',
    'LineBoss.PaintShop.Experimental.BuildAuthority.TransactionalRestoreAndWIPIsolation',
    'LineBoss.PaintShop.Experimental.CanonicalCarrierFlowValidation',
    'LineBoss.PaintShop.Experimental.CellActor.EDCoat.CanonicalConfiguration',
    'LineBoss.PaintShop.Experimental.CellActor.EDCoat.CollisionAuthority',
    'LineBoss.PaintShop.Experimental.CellActor.EDCoat.FailClosed',
    'LineBoss.PaintShop.Experimental.CellActor.EDCoat.PresentationStateRoundTrip',
    'LineBoss.PaintShop.Experimental.PlayerControls.UI.NativeUMGOnlyNoCanvas',
    'LineBoss.PaintShop.Experimental.PlayerControls.World.CanonicalHandoffPauseReleaseSaveLoad',
    'LineBoss.PaintShop.Experimental.PlayerShell.Camera.FixedEDCoatFocusContract',
    'LineBoss.PaintShop.Experimental.PlayerShell.GameMode.DefaultClassesAndBootstrapGate',
    'LineBoss.PaintShop.Experimental.PlayerShell.HUD.IsolationStageAndControls',
    'LineBoss.PaintShop.Experimental.PlayerShell.World.LiveCardinalityOwnershipAndFocus',
    'LineBoss.PaintShop.Experimental.PortComponent.FailClosedConfiguration',
    'LineBoss.PaintShop.Experimental.PortComponent.ValidConfiguration',
    'LineBoss.PaintShop.Experimental.Runtime.AtomicWeldHandoffExactOnce',
    'LineBoss.PaintShop.Experimental.Runtime.BoundAuthorityInitializationAndStarvation',
    'LineBoss.PaintShop.Experimental.Runtime.PauseStagesBlockedOutputReleaseAndFault',
    'LineBoss.PaintShop.Experimental.Runtime.SaveRestoreExactLineageAndNoDuplicate',
    'LineBoss.PaintShop.Experimental.SaveGameV1Isolation',
    'LineBoss.PaintShop.Experimental.SaveGameV1LineageCompatibilityAndFailClosed',
    'LineBoss.PaintShop.Experimental.SaveGameV1TopologyAndWIPInvariant',
    'LineBoss.PaintShop.Experimental.SaveGameV2ExactLineageInvalidAndDuplicateRejection',
    'LineBoss.PaintShop.Experimental.SaveGameV2ExactLineageRoundTripAndMaterialProgression',
    'LineBoss.PaintShop.Experimental.StableIdsAndCanonicalDefinitions',
    'LineBoss.PaintShop.Experimental.WorldBootstrap.InitializeExactlyOnePair',
    'LineBoss.PaintShop.Experimental.WorldBootstrap.PreExistingPaintAuthorityFailsClosed',
    'LineBoss.PaintShop.Experimental.WorldBootstrap.SpawnPreconditions'
)

$ExpectedScreenshotNames = @(
    '01_actual_management_pawn_overview.png',
    '01_actual_management_pawn_overview_with_ui.png',
    '02_edcoat_immersing.png',
    '02_edcoat_immersing_with_ui.png',
    '03_edcoat_output_ready.png',
    '03_edcoat_output_ready_with_ui.png'
)

$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$RunRoot = Join-Path $Root "Saved\Audits\PaintShop\Experimental_v001\ReleaseValidation\$Stamp"
$Logs = Join-Path $RunRoot 'Logs'
$AutomationRoot = Join-Path $Root "Saved\Automation\PaintShop\Experimental_v001\ReleaseValidation_$Stamp"
$CaptureRoot = Join-Path $Root "Saved\ValidationScreenshots\PaintShop\Experimental_v001\ReleaseValidation\$Stamp"
$LiveReceipt = Join-Path $RunRoot 'live_pie_edcoat_validation_v001.json'
$SummaryPath = Join-Path $RunRoot 'release_validation_summary_v001.json'

function Assert-Leaf {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label is missing: $Path"
    }
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
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -gt 0) {
        $Descriptions = @($Active | Sort-Object ProcessName, Id | ForEach-Object { "$($_.ProcessName)[$($_.Id)]" })
        throw "Refusing release validation while Unreal/build processes are active: $($Descriptions -join ', ')"
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

function Get-ProjectRelativePath {
    param([Parameter(Mandatory = $true)][string]$Path)
    $RootFull = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
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
    $RootFull = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $Prefix = $RootFull + [IO.Path]::DirectorySeparatorChar
    if (-not $Resolved.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the project root: $Resolved"
    }
    return $Resolved
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
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Full).Hash
    }
}

function Get-ProtectedSnapshot {
    $Paths = New-Object System.Collections.Generic.List[string]
    foreach ($Path in @(
        $PSCommandPath,
        $ValidatorScript,
        $PressV913Map,
        $BodyV005Map,
        $PaintMap,
        $BodyWeldHeader,
        $BodyWeldSource,
        $ECoatHeader,
        $ECoatSource
    )) {
        [void]$Paths.Add([IO.Path]::GetFullPath($Path))
    }

    $ConfigRoot = Join-Path $Root 'Config'
    if (Test-Path -LiteralPath $ConfigRoot -PathType Container) {
        foreach ($Item in @(Get-ChildItem -LiteralPath $ConfigRoot -Recurse -File -ErrorAction Stop)) {
            [void]$Paths.Add($Item.FullName)
        }
    }

    $SourceRoot = Join-Path $Root 'Source'
    if (Test-Path -LiteralPath $SourceRoot -PathType Container) {
        $PaintSources = @(Get-ChildItem -LiteralPath $SourceRoot -Recurse -File -ErrorAction Stop | Where-Object {
            $_.Name -match '^LBPaintShop.*\.(?:h|cpp)$'
        })
        foreach ($Item in $PaintSources) {
            [void]$Paths.Add($Item.FullName)
        }
    }

    foreach ($Item in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Filter '*.sav' -ErrorAction Stop)) {
        [void]$Paths.Add($Item.FullName)
    }

    $Rows = @()
    foreach ($Path in @($Paths | Sort-Object -Unique)) {
        $Rows += Get-HashRecord $Path
    }
    return @($Rows)
}

function Get-ProtectedChanges {
    param(
        [Parameter(Mandatory = $true)]$Before,
        [Parameter(Mandatory = $true)]$After
    )
    $BeforeByPath = @{}
    $AfterByPath = @{}
    foreach ($Row in @($Before)) { $BeforeByPath[[string]$Row.relative_path] = $Row }
    foreach ($Row in @($After)) { $AfterByPath[[string]$Row.relative_path] = $Row }

    $AllPaths = @((@($BeforeByPath.Keys) + @($AfterByPath.Keys)) | Sort-Object -Unique)
    $Changes = @()
    foreach ($Path in $AllPaths) {
        if (-not $BeforeByPath.ContainsKey($Path)) {
            $Changes += [ordered]@{ relative_path = $Path; change = 'ADDED'; before = $null; after = $AfterByPath[$Path] }
            continue
        }
        if (-not $AfterByPath.ContainsKey($Path)) {
            $Changes += [ordered]@{ relative_path = $Path; change = 'REMOVED'; before = $BeforeByPath[$Path]; after = $null }
            continue
        }
        $Old = $BeforeByPath[$Path]
        $New = $AfterByPath[$Path]
        if ([bool]$Old.exists -ne [bool]$New.exists -or [string]$Old.sha256 -cne [string]$New.sha256 -or [string]$Old.bytes -cne [string]$New.bytes) {
            $Changes += [ordered]@{ relative_path = $Path; change = 'CHANGED'; before = $Old; after = $New }
        }
    }
    return @($Changes)
}

function Assert-ProtectedCheckpoint {
    param(
        [Parameter(Mandatory = $true)]$Before,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $After = Get-ProtectedSnapshot
    $Changes = @(Get-ProtectedChanges $Before $After)
    if ($Changes.Count -gt 0) {
        $Preview = @($Changes | Select-Object -First 12 | ForEach-Object { "$($_.change):$($_.relative_path)" })
        throw "$Label changed protected Config/map/source/save files: $($Preview -join ', ')"
    }
    return [ordered]@{
        label = $Label
        checked_utc = (Get-Date).ToUniversalTime().ToString('o')
        file_count = @($After).Count
        unchanged = $true
    }
}

function ConvertTo-ProcessArgument {
    param([AllowEmptyString()][string]$Value)
    if ($Value.Contains('"')) {
        throw "Process argument unexpectedly contains a double quote: $Value"
    }
    if ($Value.Length -eq 0) { return '""' }
    if ($Value -match '[\s]') { return ('"{0}"' -f $Value) }
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
    if (-not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
        throw "$Label working directory is missing: $WorkingDirectory"
    }
    foreach ($LogPath in @($StdoutPath, $StderrPath)) {
        if (Test-Path -LiteralPath $LogPath) {
            throw "$Label refuses to overwrite process log: $LogPath"
        }
    }

    $ArgumentLine = if ($PSCmdlet.ParameterSetName -eq 'Raw') {
        $RawArgumentLine
    }
    else {
        (@($Arguments | ForEach-Object { ConvertTo-ProcessArgument ([string]$_) }) -join ' ')
    }

    $Started = (Get-Date).ToUniversalTime()
    $StartParameters = @{
        FilePath = $FilePath
        WorkingDirectory = $WorkingDirectory
        RedirectStandardOutput = $StdoutPath
        RedirectStandardError = $StderrPath
        WindowStyle = 'Hidden'
        PassThru = $true
    }
    if (-not [string]::IsNullOrWhiteSpace($ArgumentLine)) {
        $StartParameters.ArgumentList = $ArgumentLine
    }
    $Process = Start-Process @StartParameters
    $null = $Process.Handle
    $Deadline = $Started.AddSeconds($TimeoutSeconds)
    while (-not $Process.HasExited -and (Get-Date).ToUniversalTime() -lt $Deadline) {
        [void]$Process.WaitForExit(500)
    }

    $TimedOut = -not $Process.HasExited
    $KillLog = $null
    if ($TimedOut) {
        $KillLog = Join-Path (Split-Path -Parent $StdoutPath) (([IO.Path]::GetFileNameWithoutExtension($StdoutPath)) + '.timeout-kill.log')
        $KillMessages = @()
        $TaskKill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
        if (Test-Path -LiteralPath $TaskKill -PathType Leaf) {
            try {
                $KillMessages += (& $TaskKill /PID $Process.Id /T /F 2>&1 | Out-String)
            }
            catch {
                $KillMessages += "taskkill failed: $($_.Exception.Message)"
            }
        }
        try {
            if (-not $Process.HasExited) { $Process.Kill() }
        }
        catch {
            $KillMessages += "Process.Kill failed: $($_.Exception.Message)"
        }
        try { [void]$Process.WaitForExit(15000) } catch { $KillMessages += "Final wait failed: $($_.Exception.Message)" }
        $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [IO.File]::WriteAllText($KillLog, ($KillMessages -join "`r`n"), $Utf8NoBom)
    }
    else {
        # Flush asynchronous redirected output after the bounded wait.
        $Process.WaitForExit()
    }

    $Finished = (Get-Date).ToUniversalTime()
    $ExitCode = $null
    if ($Process.HasExited) { $ExitCode = [int]$Process.ExitCode }
    return [pscustomobject][ordered]@{
        label = $Label
        executable = $FilePath
        argument_line = $ArgumentLine
        started_utc = $Started.ToString('o')
        finished_utc = $Finished.ToString('o')
        duration_seconds = [Math]::Round(($Finished - $Started).TotalSeconds, 3)
        timeout_seconds = $TimeoutSeconds
        timed_out = $TimedOut
        exit_code = $ExitCode
        stdout_log = $StdoutPath
        stderr_log = $StderrPath
        timeout_kill_log = $KillLog
    }
}

function Assert-ProcessSucceeded {
    param([Parameter(Mandatory = $true)]$Result)
    if ([bool]$Result.timed_out) {
        throw "$($Result.label) exceeded its $($Result.timeout_seconds)-second timeout; logs: $($Result.stdout_log), $($Result.stderr_log)"
    }
    if ($null -eq $Result.exit_code) {
        throw "$($Result.label) did not expose an exit code; logs: $($Result.stdout_log), $($Result.stderr_log)"
    }
    if ([int]$Result.exit_code -ne 0) {
        throw "$($Result.label) failed with exit code $($Result.exit_code); logs: $($Result.stdout_log), $($Result.stderr_log)"
    }
}

function Wait-StableLeaf {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Int64]$MinimumBytes = 1,
        [string]$ExpectedSha256 = ''
    )
    $Previous = $null
    $LastProblem = 'not checked'
    for ($Attempt = 1; $Attempt -le 24; $Attempt++) {
        try {
            if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
                $Previous = $null
                $LastProblem = 'missing'
            }
            else {
                $Item = Get-Item -LiteralPath $Path
                $Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
                if ([Int64]$Item.Length -lt $MinimumBytes) {
                    $Previous = $null
                    $LastProblem = "too small ($($Item.Length) bytes)"
                }
                elseif (-not [string]::IsNullOrWhiteSpace($ExpectedSha256) -and $Hash -cne $ExpectedSha256.ToUpperInvariant()) {
                    $Previous = $null
                    $LastProblem = "hash mismatch ($Hash)"
                }
                else {
                    $Signature = "$($Item.Length)|$($Item.LastWriteTimeUtc.Ticks)|$Hash"
                    if ($Signature -ceq $Previous) { return $Hash }
                    $Previous = $Signature
                    $LastProblem = 'awaiting a second identical size/time/hash sample'
                }
            }
        }
        catch {
            $Previous = $null
            $LastProblem = $_.Exception.Message
        }
        Start-Sleep -Milliseconds 250
    }
    throw "File did not become stable and readable: $Path ($LastProblem)"
}

function Assert-AutomationIndex {
    param([Parameter(Mandatory = $true)][string]$Path)
    $Report = Read-JsonLeaf $Path 'Paint Shop automation index'
    foreach ($Property in @('succeeded', 'succeededWithWarnings', 'failed', 'notRun', 'inProcess', 'tests')) {
        Assert-JsonProperty $Report $Property 'Paint Shop automation index'
    }
    $Succeeded = [int]$Report.succeeded
    $SucceededWithWarnings = [int]$Report.succeededWithWarnings
    $Failed = [int]$Report.failed
    $NotRun = [int]$Report.notRun
    $InProcess = [int]$Report.inProcess
    if (($Succeeded + $SucceededWithWarnings) -ne $ExpectedTests.Count -or $Failed -ne 0 -or $NotRun -ne 0 -or $InProcess -ne 0) {
        throw "Paint Shop automation is incomplete: succeeded=$Succeeded succeededWithWarnings=$SucceededWithWarnings failed=$Failed notRun=$NotRun inProcess=$InProcess"
    }

    $Tests = @($Report.tests)
    if ($Tests.Count -ne $ExpectedTests.Count) {
        throw "Paint Shop automation index has $($Tests.Count) test rows; expected exactly $($ExpectedTests.Count)"
    }
    $NonSuccess = @($Tests | Where-Object { [string]$_.state -cne 'Success' })
    if ($NonSuccess.Count -ne 0) {
        throw "Paint Shop automation contains non-success rows: $(@($NonSuccess | ForEach-Object { [string]$_.fullTestPath }) -join ', ')"
    }
    $ActualTests = @($Tests | ForEach-Object { [string]$_.fullTestPath } | Sort-Object)
    $ExpectedSorted = @($ExpectedTests | Sort-Object)
    $Differences = @(Compare-Object -ReferenceObject $ExpectedSorted -DifferenceObject $ActualTests -CaseSensitive)
    if ($ActualTests.Count -ne $ExpectedTests.Count -or $Differences.Count -ne 0 -or @($ActualTests | Sort-Object -Unique).Count -ne $ExpectedTests.Count) {
        $DifferenceText = @($Differences | ForEach-Object { "$($_.SideIndicator)$($_.InputObject)" }) -join ', '
        throw "Paint Shop automation leaf inventory mismatch: $DifferenceText"
    }
    return [ordered]@{
        index = $Path
        index_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
        succeeded = $Succeeded
        succeeded_with_warnings = $SucceededWithWarnings
        failed = $Failed
        not_run = $NotRun
        in_process = $InProcess
        exact_leaf_count = $ActualTests.Count
        exact_leaf_names = $ActualTests
    }
}

function Get-ScreenshotRows {
    param([Parameter(Mandatory = $true)]$Screenshots)
    if ($Screenshots -is [System.Array]) {
        $Rows = @()
        for ($Index = 0; $Index -lt @($Screenshots).Count; $Index++) {
            $Rows += [pscustomobject]@{ key = [string]$Index; record = @($Screenshots)[$Index] }
        }
        return @($Rows)
    }
    $Properties = @($Screenshots.PSObject.Properties)
    return @($Properties | ForEach-Object { [pscustomobject]@{ key = $_.Name; record = $_.Value } })
}

function Get-PngDimensions {
    param([Parameter(Mandatory = $true)][string]$Path)
    $Stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
        $Header = New-Object byte[] 24
        $Read = $Stream.Read($Header, 0, $Header.Length)
    }
    finally {
        $Stream.Dispose()
    }
    $Signature = @(137, 80, 78, 71, 13, 10, 26, 10)
    if ($Read -ne 24) { throw "PNG is too short to contain an IHDR: $Path" }
    for ($Index = 0; $Index -lt $Signature.Count; $Index++) {
        if ([int]$Header[$Index] -ne $Signature[$Index]) { throw "Screenshot is not a PNG: $Path" }
    }
    if ([Text.Encoding]::ASCII.GetString($Header, 12, 4) -cne 'IHDR') {
        throw "PNG does not have IHDR as its first chunk: $Path"
    }
    $Width = [int](([int64]$Header[16] * 16777216) + ([int64]$Header[17] * 65536) + ([int64]$Header[18] * 256) + [int64]$Header[19])
    $Height = [int](([int64]$Header[20] * 16777216) + ([int64]$Header[21] * 65536) + ([int64]$Header[22] * 256) + [int64]$Header[23])
    return [pscustomobject]@{ width = $Width; height = $Height }
}

function Assert-LiveReceipt {
    param([Parameter(Mandatory = $true)][string]$Path)
    $StableReceiptHash = Wait-StableLeaf $Path 128
    $Live = Read-JsonLeaf $Path 'Paint Shop actual-player E-coat PIE receipt'
    foreach ($Property in @('$schema', 'status', 'failures', 'map_sha256_before', 'map_sha256_after', 'map_hash_unchanged', 'checks', 'screenshots')) {
        Assert-JsonProperty $Live $Property 'Paint Shop actual-player E-coat PIE receipt'
    }
    if ([string]$Live.'$schema' -cne $ExpectedLiveSchema) {
        throw "Live PIE receipt schema mismatch: $($Live.'$schema')"
    }
    if ([string]$Live.status -cne $ExpectedLiveStatus) {
        throw "Live PIE receipt status mismatch: $($Live.status)"
    }
    if (@($Live.failures).Count -ne 0) {
        throw "Live PIE receipt contains failures: $(@($Live.failures) -join '; ')"
    }
    if ([string]$Live.map_sha256_before -cne $ExpectedMapSha256 -or [string]$Live.map_sha256_after -cne $ExpectedMapSha256) {
        throw "Live PIE receipt does not bind the exact unchanged Paint Shop map hash: before=$($Live.map_sha256_before) after=$($Live.map_sha256_after)"
    }
    if ($Live.map_hash_unchanged -isnot [bool] -or -not $Live.map_hash_unchanged) {
        throw 'Live PIE receipt does not report map_hash_unchanged=true as a JSON boolean'
    }
    if ($null -eq $Live.checks) {
        throw 'Live PIE receipt has a null checks object'
    }

    $Rows = @(Get-ScreenshotRows $Live.screenshots)
    if ($Rows.Count -ne 6) {
        throw "Live PIE receipt has $($Rows.Count) screenshot records; expected exactly six"
    }
    $CaptureFull = [IO.Path]::GetFullPath($CaptureRoot).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $Evidence = @()
    foreach ($Entry in $Rows) {
        $Record = $Entry.record
        foreach ($Property in @('path', 'sha256', 'bytes', 'dimensions')) {
            Assert-JsonProperty $Record $Property "Screenshot record '$($Entry.key)'"
        }
        $Screenshot = Resolve-ProjectPath ([string]$Record.path) "Screenshot record '$($Entry.key)'"
        if ([string]$Entry.key -cne [IO.Path]::GetFileName($Screenshot)) {
            throw "Screenshot object key must exactly equal its basename: key=$($Entry.key) path=$Screenshot"
        }
        if (-not [IO.Path]::GetDirectoryName($Screenshot).Equals($CaptureFull, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Screenshot record '$($Entry.key)' escapes the exact current-run capture directory: $Screenshot"
        }
        $ExpectedHash = ([string]$Record.sha256).ToUpperInvariant()
        if ($ExpectedHash -notmatch '^[0-9A-F]{64}$') {
            throw "Screenshot record '$($Entry.key)' has an invalid SHA-256: $($Record.sha256)"
        }
        $ActualHash = Wait-StableLeaf $Screenshot 1024 $ExpectedHash
        $ActualItem = Get-Item -LiteralPath $Screenshot
        if ([Int64]$Record.bytes -ne [Int64]$ActualItem.Length) {
            throw "Screenshot record '$($Entry.key)' byte count differs from disk: receipt=$($Record.bytes) disk=$($ActualItem.Length)"
        }
        $ReceiptDimensions = @($Record.dimensions)
        $ActualDimensions = Get-PngDimensions $Screenshot
        if ($ReceiptDimensions.Count -ne 2 -or [int]$ReceiptDimensions[0] -ne [int]$ActualDimensions.width -or
            [int]$ReceiptDimensions[1] -ne [int]$ActualDimensions.height -or
            [int]$ActualDimensions.width -le 0 -or [int]$ActualDimensions.height -le 0) {
            throw "Screenshot record '$($Entry.key)' dimensions differ from its PNG: receipt=$($ReceiptDimensions -join 'x') disk=$($ActualDimensions.width)x$($ActualDimensions.height)"
        }
        if ([string]$Entry.key -notlike '*_with_ui.png' -and
            ([int]$ActualDimensions.width -ne 1920 -or [int]$ActualDimensions.height -ne 1080)) {
            throw "High-resolution screenshot '$($Entry.key)' is not exactly 1920x1080: $($ActualDimensions.width)x$($ActualDimensions.height)"
        }
        $Evidence += [ordered]@{
            key = [string]$Entry.key
            path = $Screenshot
            basename = [IO.Path]::GetFileName($Screenshot)
            sha256 = $ActualHash
            bytes = [Int64]$ActualItem.Length
            dimensions = @([int]$ActualDimensions.width, [int]$ActualDimensions.height)
        }
    }

    $ActualNames = @($Evidence | ForEach-Object { [string]$_.basename } | Sort-Object)
    $ExpectedNamesSorted = @($ExpectedScreenshotNames | Sort-Object)
    $NameDifferences = @(Compare-Object -ReferenceObject $ExpectedNamesSorted -DifferenceObject $ActualNames -CaseSensitive)
    if ($NameDifferences.Count -ne 0 -or @($ActualNames | Sort-Object -Unique).Count -ne 6) {
        $DifferenceText = @($NameDifferences | ForEach-Object { "$($_.SideIndicator)$($_.InputObject)" }) -join ', '
        throw "Live PIE screenshot basename inventory mismatch: $DifferenceText"
    }
    $DiskPngNames = @(Get-ChildItem -LiteralPath $CaptureRoot -File -Filter '*.png' -ErrorAction Stop | ForEach-Object { $_.Name } | Sort-Object)
    $DiskDifferences = @(Compare-Object -ReferenceObject $ExpectedNamesSorted -DifferenceObject $DiskPngNames -CaseSensitive)
    if ($DiskPngNames.Count -ne 6 -or $DiskDifferences.Count -ne 0) {
        $DifferenceText = @($DiskDifferences | ForEach-Object { "$($_.SideIndicator)$($_.InputObject)" }) -join ', '
        throw "Fresh capture directory does not contain exactly the six expected PNGs: $DifferenceText"
    }
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash -cne $StableReceiptHash) {
        throw 'Live PIE receipt changed while its screenshot evidence was stabilizing'
    }
    return [ordered]@{
        receipt = $Path
        receipt_sha256 = $StableReceiptHash
        schema = [string]$Live.'$schema'
        status = [string]$Live.status
        map_sha256_before = [string]$Live.map_sha256_before
        map_sha256_after = [string]$Live.map_sha256_after
        map_hash_unchanged = $true
        screenshot_count = $Evidence.Count
        screenshots = $Evidence
    }
}

function Assert-PrerequisiteReceipts {
    $Create = Read-JsonLeaf $CreateReceipt 'Paint Shop prototype-map creation receipt'
    foreach ($Property in @('$schema', 'status', 'map_sha256', 'failures')) {
        Assert-JsonProperty $Create $Property 'Paint Shop prototype-map creation receipt'
    }
    $CreateHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $CreateReceipt).Hash
    if ($CreateHash -cne $ExpectedCreateReceiptSha256) {
        throw "Creation receipt SHA-256 mismatch: expected=$ExpectedCreateReceiptSha256 actual=$CreateHash"
    }
    if ([string]$Create.'$schema' -cne $ExpectedCreateSchema -or [string]$Create.status -cne $ExpectedCreateStatus) {
        throw "Creation receipt schema/status mismatch: schema=$($Create.'$schema') status=$($Create.status)"
    }
    if ([string]$Create.map_sha256 -cne $ExpectedMapSha256 -or @($Create.failures).Count -ne 0) {
        throw 'Creation receipt does not bind the exact failure-free Paint Shop prototype map'
    }

    $Validation = Read-JsonLeaf $ValidationReceipt 'Independent Paint Shop prototype-map validation receipt'
    foreach ($Property in @('$schema', 'status', 'creation_receipt', 'creation_receipt_sha256', 'map_sha256', 'writes_to_content_config_or_source', 'failures')) {
        Assert-JsonProperty $Validation $Property 'Independent Paint Shop prototype-map validation receipt'
    }
    if ([string]$Validation.'$schema' -cne $ExpectedValidationSchema -or [string]$Validation.status -cne $ExpectedValidationStatus) {
        throw "Independent validation receipt schema/status mismatch: schema=$($Validation.'$schema') status=$($Validation.status)"
    }
    if ([string]$Validation.creation_receipt -cne 'Saved/Audits/PaintShop/Experimental_v001/paint_shop_prototype_map_create_v001.json' -or
        [string]$Validation.creation_receipt_sha256 -cne $ExpectedCreateReceiptSha256 -or
        [string]$Validation.map_sha256 -cne $ExpectedMapSha256 -or
        $Validation.writes_to_content_config_or_source -isnot [bool] -or
        [bool]$Validation.writes_to_content_config_or_source -or
        @($Validation.failures).Count -ne 0) {
        throw 'Independent validation receipt does not prove an exact read-only fresh-reload validation of the frozen creation receipt and map'
    }

    $CurrentMapHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PaintMap).Hash
    if ($CurrentMapHash -cne $ExpectedMapSha256) {
        throw "Current Paint Shop map SHA-256 mismatch: expected=$ExpectedMapSha256 actual=$CurrentMapHash"
    }
    return [ordered]@{
        create_receipt = [ordered]@{
            path = $CreateReceipt
            sha256 = $CreateHash
            schema = [string]$Create.'$schema'
            status = [string]$Create.status
        }
        independent_validation_receipt = [ordered]@{
            path = $ValidationReceipt
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $ValidationReceipt).Hash
            schema = [string]$Validation.'$schema'
            status = [string]$Validation.status
            creation_receipt_sha256 = [string]$Validation.creation_receipt_sha256
            map_sha256 = [string]$Validation.map_sha256
        }
        current_map_sha256 = $CurrentMapHash
    }
}

if (Test-Path -LiteralPath $RunRoot) { throw "Fresh release-validation run directory already exists: $RunRoot" }
if (Test-Path -LiteralPath $AutomationRoot) { throw "Fresh automation export directory already exists: $AutomationRoot" }
if (Test-Path -LiteralPath $CaptureRoot) { throw "Fresh screenshot capture directory already exists: $CaptureRoot" }
# The Python validator owns creation of the fresh capture directory and uses
# exist_ok=False as its stale-evidence guard, so the runner must leave it absent.
New-Item -ItemType Directory -Path $Logs, $AutomationRoot -Force | Out-Null

$ProcessRuns = New-Object System.Collections.Generic.List[object]
$ProtectedCheckpoints = New-Object System.Collections.Generic.List[object]
$Failures = New-Object System.Collections.Generic.List[string]
$PrerequisiteEvidence = $null
$AutomationEvidence = $null
$LiveEvidence = $null
$ProtectedBefore = $null
$ProtectedAfter = $null
$ProtectedChanges = @()
$RunPhasesCompleted = $false
$PreviousStamp = [Environment]::GetEnvironmentVariable('LB_PAINTSHOP_VALIDATION_STAMP', 'Process')

try {
    foreach ($PathAndLabel in @(
        @($Project, 'Unreal project'),
        @($Editor, 'UnrealEditor-Cmd'),
        @($ValidatorScript, 'Paint Shop actual-player E-coat PIE validator'),
        @($PaintMap, 'Paint Shop prototype map'),
        @($PressV913Map, 'protected Press Shop v913 map'),
        @($BodyV005Map, 'protected Body Shop v005 map'),
        @($BodyWeldHeader, 'protected LBBodyWeldLineActor header'),
        @($BodyWeldSource, 'protected LBBodyWeldLineActor source'),
        @($ECoatHeader, 'protected LBECoatLineActor header'),
        @($ECoatSource, 'protected LBECoatLineActor source')
    )) {
        Assert-Leaf $PathAndLabel[0] $PathAndLabel[1]
    }
    if (-not $SkipEditorBuild) {
        Assert-Leaf $Build 'Unreal editor build script'
    }
    Assert-NoActiveUnrealProcess
    $ProtectedBefore = Get-ProtectedSnapshot
    $MissingProtected = @($ProtectedBefore | Where-Object { -not [bool]$_.exists })
    if ($MissingProtected.Count -ne 0) {
        throw "Required protected files are missing at baseline: $(@($MissingProtected | ForEach-Object { $_.relative_path }) -join ', ')"
    }

    $PrerequisiteEvidence = Assert-PrerequisiteReceipts
    [Environment]::SetEnvironmentVariable('LB_PAINTSHOP_VALIDATION_STAMP', $Stamp, 'Process')

    if (-not $SkipEditorBuild) {
        $ComSpec = [Environment]::GetEnvironmentVariable('ComSpec', 'Process')
        Assert-Leaf $ComSpec 'Windows command processor'
        $BuildArgumentLine = '/d /s /c ""{0}" LineBossCarFactoryEditor Win64 Development "-Project={1}" -WaitMutex -NoHotReloadFromIDE"' -f $Build, $Project
        $BuildResult = Invoke-GuardedProcess -Label 'LineBossCarFactoryEditor Development build' -FilePath $ComSpec `
            -RawArgumentLine $BuildArgumentLine -WorkingDirectory $Root `
            -StdoutPath (Join-Path $Logs 'editor_build.stdout.log') `
            -StderrPath (Join-Path $Logs 'editor_build.stderr.log') `
            -TimeoutSeconds $BuildTimeoutSeconds
        [void]$ProcessRuns.Add($BuildResult)
        Assert-ProcessSucceeded $BuildResult
        [void]$ProtectedCheckpoints.Add((Assert-ProtectedCheckpoint $ProtectedBefore 'After editor build'))
    }

    $AutomationArguments = @(
        $Project,
        '-ExecCmds=Automation RunTests LineBoss.PaintShop.Experimental; Quit',
        "-ReportExportPath=$AutomationRoot",
        '-TestExit=Automation Test Queue Empty',
        '-unattended',
        '-nop4',
        '-nosplash',
        '-nosound',
        '-NullRHI',
        '-stdout',
        '-FullStdOutLogOutput'
    )
    $AutomationResult = Invoke-GuardedProcess -Label 'Paint Shop Experimental automation' -FilePath $Editor `
        -Arguments $AutomationArguments -WorkingDirectory $Root `
        -StdoutPath (Join-Path $Logs 'automation.stdout.log') `
        -StderrPath (Join-Path $Logs 'automation.stderr.log') `
        -TimeoutSeconds $AutomationTimeoutSeconds
    [void]$ProcessRuns.Add($AutomationResult)
    Assert-ProcessSucceeded $AutomationResult
    $AutomationEvidence = Assert-AutomationIndex (Join-Path $AutomationRoot 'index.json')
    [void]$ProtectedCheckpoints.Add((Assert-ProtectedCheckpoint $ProtectedBefore 'After NullRHI automation'))

    $PythonPathForUnreal = $ValidatorScript.Replace('\', '/')
    $LiveArguments = @(
        $Project,
        "-ExecutePythonScript=$PythonPathForUnreal",
        '-unattended',
        '-nop4',
        '-nosplash',
        '-nosound',
        '-windowed',
        '-ResX=1920',
        '-ResY=1080',
        '-stdout',
        '-FullStdOutLogOutput'
    )
    if (@($LiveArguments | Where-Object { $_ -match '(?i)nullrhi' }).Count -ne 0) {
        throw 'Internal guard rejected NullRHI in the live actual-player PIE argument set'
    }
    $LiveResult = Invoke-GuardedProcess -Label 'Paint Shop actual-player E-coat real-RHI PIE validation' -FilePath $Editor `
        -Arguments $LiveArguments -WorkingDirectory $Root `
        -StdoutPath (Join-Path $Logs 'live_pie.stdout.log') `
        -StderrPath (Join-Path $Logs 'live_pie.stderr.log') `
        -TimeoutSeconds $LivePieTimeoutSeconds
    [void]$ProcessRuns.Add($LiveResult)
    Assert-ProcessSucceeded $LiveResult
    $LiveEvidence = Assert-LiveReceipt $LiveReceipt
    $CurrentMapHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PaintMap).Hash
    if ($CurrentMapHash -cne $ExpectedMapSha256) {
        throw "Paint Shop map hash changed after live PIE: $CurrentMapHash"
    }
    [void]$ProtectedCheckpoints.Add((Assert-ProtectedCheckpoint $ProtectedBefore 'After real-RHI actual-player PIE'))
    $RunPhasesCompleted = $true
}
catch {
    [void]$Failures.Add($_.Exception.Message)
}
finally {
    if ($null -eq $PreviousStamp) {
        [Environment]::SetEnvironmentVariable('LB_PAINTSHOP_VALIDATION_STAMP', $null, 'Process')
    }
    else {
        [Environment]::SetEnvironmentVariable('LB_PAINTSHOP_VALIDATION_STAMP', $PreviousStamp, 'Process')
    }

    if ($null -ne $ProtectedBefore) {
        try {
            $ProtectedAfter = Get-ProtectedSnapshot
            $ProtectedChanges = @(Get-ProtectedChanges $ProtectedBefore $ProtectedAfter)
            if ($ProtectedChanges.Count -gt 0) {
                $Preview = @($ProtectedChanges | Select-Object -First 12 | ForEach-Object { "$($_.change):$($_.relative_path)" })
                [void]$Failures.Add("Final protected-file comparison failed: $($Preview -join ', ')")
            }
        }
        catch {
            [void]$Failures.Add("Final protected-file snapshot failed: $($_.Exception.Message)")
        }
    }

    $Passed = $RunPhasesCompleted -and $Failures.Count -eq 0
    $Summary = [ordered]@{
        '$schema' = 'lineboss/audit/paint-shop/release-validation-run-v001/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = if ($Passed) { 'PASS__PAINT_SHOP_AUTOMATION_AND_ACTUAL_PLAYER_ED_COAT_PIE_V001' } else { 'FAIL__PAINT_SHOP_RELEASE_VALIDATION_V001' }
        stamp = $Stamp
        skip_editor_build = [bool]$SkipEditorBuild
        project = $Project
        runner_script = $PSCommandPath
        runner_script_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash
        validator_script = $ValidatorScript
        validator_script_sha256 = if (Test-Path -LiteralPath $ValidatorScript -PathType Leaf) { (Get-FileHash -Algorithm SHA256 -LiteralPath $ValidatorScript).Hash } else { $null }
        run_root = $RunRoot
        automation_root = $AutomationRoot
        capture_root = $CaptureRoot
        expected_map_sha256 = $ExpectedMapSha256
        prerequisites = $PrerequisiteEvidence
        processes = $ProcessRuns.ToArray()
        automation = $AutomationEvidence
        live_pie = $LiveEvidence
        protected = [ordered]@{
            before = $ProtectedBefore
            checkpoints = $ProtectedCheckpoints.ToArray()
            after = $ProtectedAfter
            changes = $ProtectedChanges
        }
        failures = $Failures.ToArray()
    }
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($SummaryPath, ($Summary | ConvertTo-Json -Depth 16), $Utf8NoBom)
}

if ($Failures.Count -gt 0) {
    throw "Paint Shop release validation failed. Summary: $SummaryPath. $($Failures -join ' | ')"
}

Write-Output $SummaryPath
