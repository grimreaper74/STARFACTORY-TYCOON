param(
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8',
    [int]$BuilderTimeoutSeconds = 300,
    [int]$ValidatorTimeoutSeconds = 360
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Contract = Join-Path $Root 'Scripts\one_factory_visual_navigation_v002_contract.py'
$UnrealContract = Join-Path $Root 'Scripts\one_factory_visual_navigation_v002_unreal.py'
$Builder = Join-Path $Root 'Scripts\build_one_factory_visual_navigation_v002.py'
$Validator = Join-Path $Root 'Scripts\validate_one_factory_visual_navigation_v002.py'
$SourceMap = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Maps\LB_MoorcrossWorks_OneFactory_v001.umap'
$TargetMap = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v002\Maps\LB_MoorcrossWorks_OneFactory_v002.umap'
$AuditRoot = Join-Path $Root 'Saved\Audits\OneFactory\v002\VisualNavigation'
$BuildReceipt = Join-Path $AuditRoot 'one_factory_visual_navigation_build_v002.json'
$ValidationReceipt = Join-Path $AuditRoot 'one_factory_visual_navigation_validation_v002.json'
$FailureBuildReceipt = Join-Path $AuditRoot 'one_factory_visual_navigation_build_v002_failed.json'
$FailureValidationReceipt = Join-Path $AuditRoot 'one_factory_visual_navigation_validation_v002_failed.json'
$RunnerReceipt = Join-Path $AuditRoot 'one_factory_visual_navigation_runner_v002.json'
$LogRoot = Join-Path $AuditRoot 'Runner\Logs'
$ScreenshotRoot = Join-Path $Root 'Saved\ValidationScreenshots\OneFactory\v002\VisualNavigation'

$ExpectedSourceMapSha256 = '750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682'
$ExpectedContractSha256 = 'AF463353CC94988F5B1E413E84898077EB587CF81A4E69A940B006D216EF4DA9'
$ExpectedUnrealContractSha256 = '5F385670623D485F1716C459484A601105DFE7F6EA70E6793FD978272E357F81'
$ExpectedBuilderSha256 = 'A89E7C2BCA312581567488A9321A91D808733B7DBAB15BEEE61002F9F7801F5C'
$ExpectedValidatorSha256 = '5752E46164EEAF122B1773CC870ED8358C2C994CD6A34BAF58D834844980967D'
$ExpectedBuildStatus = 'PASS__ONE_FACTORY_V002_FACTORY_WIDE_CAIRNWELL_LIGHTING_AND_NAVIGATION_BUILT__SOURCE_V001_UNCHANGED'
$ExpectedValidationStatus = 'PASS__ONE_FACTORY_V002_FRESH_RELOAD_REAL_RHI_PIE_EVEN_LIGHTING_AND_NAV_VALID__ZERO_SAVED_PRODUCTION_OR_WIP'

$StaticProtectedHashes = [ordered]@{
    'Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap' = $ExpectedSourceMapSha256
    'Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap' = '26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6'
    'Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap' = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'
    'Docs/LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md' = '0E61306C437BCB587C82D6BF5609CAFDA1211E004CCFC86C6C4608CBA42A2971'
    'Scripts/validate_one_factory_shell_v001.py' = '2043ED396DFD366CB857F208A38054EE9CCE4906A04EA53C4ABD86ADF1CB5E61'
}

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is absent: $Path"
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Assert-ExactHash([string]$Path, [string]$Expected, [string]$Label) {
    $Actual = Get-Sha256 $Path
    if ($Actual -ne $Expected) {
        throw "$Label hash drift: $Actual != $Expected ($Path)"
    }
    return $Actual
}

function Get-ProjectRelativePath([string]$Path) {
    $Full = [IO.Path]::GetFullPath($Path)
    $Prefix = $Root.TrimEnd('\') + '\'
    if (-not $Full.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escaped project root: $Full"
    }
    return $Full.Substring($Prefix.Length).Replace('\', '/')
}

function Assert-NoActiveUnrealProcess {
    $Names = @(
        'UnrealEditor', 'UnrealEditor-Cmd', 'UnrealBuildTool',
        'AutomationTool', 'RunUAT', 'ShaderCompileWorker'
    )
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $Names -contains $_.ProcessName
    })
    if ($Active.Count -gt 0) {
        $Description = ($Active | Sort-Object ProcessName, Id | ForEach-Object {
            "$($_.ProcessName)[$($_.Id)]"
        }) -join ', '
        throw "Close Unreal/build/shader processes before this guarded run: $Description"
    }
}

function Assert-StaticProtectedAnchors {
    $Rows = [ordered]@{}
    foreach ($Entry in $StaticProtectedHashes.GetEnumerator()) {
        $Path = Join-Path $Root $Entry.Key.Replace('/', '\')
        $Rows[$Entry.Key] = Assert-ExactHash $Path $Entry.Value "Protected anchor $($Entry.Key)"
    }
    return $Rows
}

function Get-GuardedWorkspaceSnapshot {
    $Rows = [ordered]@{}
    $Roots = @(
        @{ Path = (Join-Path $Root 'Source'); Filter = '*' },
        @{ Path = (Join-Path $Root 'Config'); Filter = '*' },
        @{ Path = (Join-Path $Root 'Saved\SaveGames'); Filter = '*.sav' },
        @{ Path = (Join-Path $Root 'Content'); Filter = '*' }
    )
    $TargetFull = [IO.Path]::GetFullPath($TargetMap)
    foreach ($Spec in $Roots) {
        if (-not (Test-Path -LiteralPath $Spec.Path -PathType Container)) { continue }
        $Files = @(Get-ChildItem -LiteralPath $Spec.Path -Recurse -File -Filter $Spec.Filter |
            Sort-Object FullName)
        foreach ($File in $Files) {
            $Full = [IO.Path]::GetFullPath($File.FullName)
            if ($Full.Equals($TargetFull, [StringComparison]::OrdinalIgnoreCase)) { continue }
            $Rows[(Get-ProjectRelativePath $Full)] = Get-Sha256 $Full
        }
    }
    return $Rows
}

function Compare-Snapshot([Collections.IDictionary]$Before, [Collections.IDictionary]$After) {
    $Changes = [Collections.Generic.List[object]]::new()
    $Keys = @($Before.Keys + $After.Keys | Sort-Object -Unique)
    foreach ($Key in $Keys) {
        $Old = if ($Before.Contains($Key)) { $Before[$Key] } else { $null }
        $New = if ($After.Contains($Key)) { $After[$Key] } else { $null }
        if ($Old -ne $New) {
            [void]$Changes.Add([ordered]@{ path = $Key; before = $Old; after = $New })
        }
    }
    return @($Changes)
}

function Assert-SnapshotUnchanged(
    [Collections.IDictionary]$Before,
    [string]$Checkpoint
) {
    $After = Get-GuardedWorkspaceSnapshot
    $Changes = @(Compare-Snapshot $Before $After)
    if ($Changes.Count -gt 0) {
        throw "$Checkpoint changed protected Content/Source/Config/SaveGames: $($Changes | ConvertTo-Json -Compress)"
    }
    return [ordered]@{ checkpoint = $Checkpoint; file_count = $After.Count; changes = @() }
}

function Quote-ProcessArgument([string]$Value) {
    if ($Value -notmatch '[\s"]') { return $Value }
    return '"' + $Value.Replace('"', '\"') + '"'
}

function Invoke-GuardedProcess(
    [string]$Label,
    [string[]]$Arguments,
    [string]$StdoutPath,
    [string]$StderrPath,
    [int]$TimeoutSeconds
) {
    if ((Test-Path -LiteralPath $StdoutPath) -or (Test-Path -LiteralPath $StderrPath)) {
        throw "Refusing to overwrite process logs for $Label"
    }
    $Started = (Get-Date).ToUniversalTime()
    $ArgumentLine = ($Arguments | ForEach-Object { Quote-ProcessArgument $_ }) -join ' '
    $Process = Start-Process -FilePath $Editor -ArgumentList $ArgumentLine `
        -WorkingDirectory $Root -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath -WindowStyle Hidden -PassThru
    $null = $Process.Handle
    $Deadline = $Started.AddSeconds($TimeoutSeconds)
    while (-not $Process.HasExited -and (Get-Date).ToUniversalTime() -lt $Deadline) {
        [void]$Process.WaitForExit(500)
    }
    if (-not $Process.HasExited) {
        try { $Process.Kill($true) } catch { }
        throw "$Label exceeded ${TimeoutSeconds}s and was terminated"
    }
    $Process.WaitForExit()
    $Result = [ordered]@{
        label = $Label
        executable = $Editor
        argument_line = $ArgumentLine
        started_utc = $Started.ToString('o')
        finished_utc = (Get-Date).ToUniversalTime().ToString('o')
        exit_code = $Process.ExitCode
        stdout = Get-ProjectRelativePath $StdoutPath
        stderr = Get-ProjectRelativePath $StderrPath
        stdout_sha256 = Get-Sha256 $StdoutPath
        stderr_sha256 = Get-Sha256 $StderrPath
    }
    if ($Process.ExitCode -ne 0) {
        throw "$Label failed with exit code $($Process.ExitCode)"
    }
    return $Result
}

function Read-ExactJson([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Expected JSON receipt is absent: $Path"
    }
    return Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
}

Assert-NoActiveUnrealProcess
if (-not (Test-Path -LiteralPath $Project -PathType Leaf)) { throw "Project is absent: $Project" }
if (-not (Test-Path -LiteralPath $Editor -PathType Leaf)) { throw "UnrealEditor-Cmd is absent: $Editor" }
if (Test-Path -LiteralPath $TargetMap) { throw "Refusing to overwrite existing v002 map: $TargetMap" }
foreach ($Path in @(
    $BuildReceipt, $ValidationReceipt, $FailureBuildReceipt,
    $FailureValidationReceipt, $RunnerReceipt, $LogRoot, $ScreenshotRoot
)) {
    if (Test-Path -LiteralPath $Path) { throw "Refusing to overwrite prior evidence: $Path" }
}

[void](Assert-ExactHash $SourceMap $ExpectedSourceMapSha256 'Source OneFactory v001 map')
[void](Assert-ExactHash $Contract $ExpectedContractSha256 'v002 contract')
[void](Assert-ExactHash $UnrealContract $ExpectedUnrealContractSha256 'v002 Unreal contract')
[void](Assert-ExactHash $Builder $ExpectedBuilderSha256 'v002 builder')
[void](Assert-ExactHash $Validator $ExpectedValidatorSha256 'v002 validator')
$AnchorsBefore = Assert-StaticProtectedAnchors
$Baseline = Get-GuardedWorkspaceSnapshot

New-Item -ItemType Directory -Path $LogRoot -ErrorAction Stop | Out-Null
$Processes = [Collections.Generic.List[object]]::new()
$Checkpoints = [Collections.Generic.List[object]]::new()

$BuilderForUnreal = $Builder.Replace('\', '/')
$BuilderArguments = @(
    $Project,
    "-ExecutePythonScript=$BuilderForUnreal",
    '-unattended', '-nop4', '-nosplash', '-nosound', '-NullRHI',
    '-NoCompile', '-NoCompileEditor', '-NoAutoSave', '-NoSaveOnExit',
    '-stdout', '-FullStdOutLogOutput'
)
$BuilderResult = Invoke-GuardedProcess -Label 'OneFactory v002 guarded builder' `
    -Arguments $BuilderArguments `
    -StdoutPath (Join-Path $LogRoot 'builder.stdout.log') `
    -StderrPath (Join-Path $LogRoot 'builder.stderr.log') `
    -TimeoutSeconds $BuilderTimeoutSeconds
[void]$Processes.Add($BuilderResult)
[void]$Checkpoints.Add((Assert-SnapshotUnchanged $Baseline 'After v002 builder'))
[void](Assert-ExactHash $SourceMap $ExpectedSourceMapSha256 'Source v001 after builder')
if (-not (Test-Path -LiteralPath $TargetMap -PathType Leaf)) {
    throw 'Builder did not create the reserved v002 target map'
}
$Build = Read-ExactJson $BuildReceipt
if ($Build.status -ne $ExpectedBuildStatus -or $Build.target_map_sha256 -ne (Get-Sha256 $TargetMap)) {
    throw 'Builder receipt status/map hash contract failed'
}

Assert-NoActiveUnrealProcess
$ValidatorForUnreal = $Validator.Replace('\', '/')
$ValidatorArguments = @(
    $Project,
    "-ExecutePythonScript=$ValidatorForUnreal",
    '-unattended', '-nop4', '-nosplash', '-nosound', '-windowed',
    '-RenderOffscreen', '-ResX=1920', '-ResY=1080',
    '-NoCompile', '-NoCompileEditor', '-NoAutoSave', '-NoSaveOnExit',
    '-stdout', '-FullStdOutLogOutput'
)
if (@($ValidatorArguments | Where-Object { $_ -match '(?i)nullrhi' }).Count -ne 0) {
    throw 'Internal guard rejected NullRHI in the real-player validator arguments'
}
$ValidatorResult = Invoke-GuardedProcess -Label 'OneFactory v002 fresh real-RHI PIE validator' `
    -Arguments $ValidatorArguments `
    -StdoutPath (Join-Path $LogRoot 'validator.stdout.log') `
    -StderrPath (Join-Path $LogRoot 'validator.stderr.log') `
    -TimeoutSeconds $ValidatorTimeoutSeconds
[void]$Processes.Add($ValidatorResult)

$CombinedLog = @(
    Get-Content -Raw -LiteralPath (Join-Path $LogRoot 'validator.stdout.log')
    Get-Content -Raw -LiteralPath (Join-Path $LogRoot 'validator.stderr.log')
) -join "`n"
if ($CombinedLog -match '(?i)NAVMESH NEEDS TO BE REBUILT|Unable to find RecastNavMesh') {
    throw 'Fresh validator log still contains the v001 navigation failure signature'
}

$Validation = Read-ExactJson $ValidationReceipt
if ($Validation.status -ne $ExpectedValidationStatus) {
    throw "Independent validator status failed: $($Validation.status)"
}
$ExpectedScreenshots = @(
    '01_empty_factory_overview.png', '02_populated_press_bay.png',
    '03_body_bay.png', '04_paint_bay.png', '05_assembly_bay.png',
    '06_populated_press_with_umg_nav_clean.png'
)
$ActualScreenshots = @($Validation.screenshots.PSObject.Properties.Name | Sort-Object)
if (Compare-Object ($ExpectedScreenshots | Sort-Object) $ActualScreenshots) {
    throw "Validator screenshot inventory drift: $($ActualScreenshots -join ', ')"
}
[void]$Checkpoints.Add((Assert-SnapshotUnchanged $Baseline 'After independent validator'))
[void](Assert-ExactHash $SourceMap $ExpectedSourceMapSha256 'Source v001 after validator')
$AnchorsAfter = Assert-StaticProtectedAnchors
if ((Compare-Object ($AnchorsBefore.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) `
        ($AnchorsAfter.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }))) {
    throw 'Static protected-anchor snapshot changed'
}

$RunnerPayload = [ordered]@{
    '$schema' = 'lineboss/audit/one-factory/visual-navigation-runner-v002/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'PASS__ONE_FACTORY_VISUAL_NAVIGATION_V002_GUARDED_BUILD_AND_INDEPENDENT_VALIDATION'
    source_map = '/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001'
    source_map_sha256 = Get-Sha256 $SourceMap
    target_map = '/Game/LineBoss/Factory/OneFactory/v002/Maps/LB_MoorcrossWorks_OneFactory_v002'
    target_map_sha256 = Get-Sha256 $TargetMap
    overwrite_refused = $true
    ubt_or_source_build_invoked = $false
    real_rhi_validator = $true
    builder_receipt = Get-ProjectRelativePath $BuildReceipt
    builder_receipt_sha256 = Get-Sha256 $BuildReceipt
    validation_receipt = Get-ProjectRelativePath $ValidationReceipt
    validation_receipt_sha256 = Get-Sha256 $ValidationReceipt
    processes = @($Processes)
    protected_checkpoints = @($Checkpoints)
    protected_anchors = $AnchorsAfter
    guarded_workspace_file_count = $Baseline.Count
    content_source_config_saves_unchanged_except_new_target = $true
}
$RunnerPayload | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $RunnerReceipt -Encoding utf8
Write-Host "PASS: OneFactory v002 lighting/navigation successor built and validated."
Write-Host "Target: /Game/LineBoss/Factory/OneFactory/v002/Maps/LB_MoorcrossWorks_OneFactory_v002"
Write-Host "Runner receipt: $RunnerReceipt"
