[CmdletBinding()]
param(
    [string]$ProjectRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$EditorPieBlocker = @'
BLOCKED__BODY_SHOP_1920X1080_EDITOR_PIE_PERFORMANCE_LOD_V001: UE 5.8 editor PIE
could not establish an exact 1920x1080 real-RHI viewport on the 1280x720 host.
The DPI/native-window workaround caused a renderer/Slate worker-thread crash in
fresh run 20260814T103148Z. This retired runner intentionally launches nothing.
Use the separately designed packaged Development capture seam after a current
Development package exists.
'@
throw $EditorPieBlocker

$Root = [IO.Path]::GetFullPath($ProjectRoot)
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Engine = 'C:\Program Files\Epic Games\UE_5.8'
$Editor = Join-Path $Engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Python = Join-Path $Engine 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$RunRoot = Join-Path $Root "Saved\Audits\BodyShop\Experimental_v001\PerformanceLODValidation\$Stamp"
$Logs = Join-Path $RunRoot 'Logs'
$RawReceipt = Join-Path $RunRoot 'performance_lod_raw_capture_v001.json'
$GateReceipt = Join-Path $RunRoot 'performance_lod_release_gate_v001.json'
$Summary = Join-Path $RunRoot 'performance_lod_validation_summary_v001.json'
$PieLog = Join-Path $Logs 'performance_lod_pie.log'
$AnalysisLog = Join-Path $Logs 'performance_lod_analysis.log'
$CaptureScript = Join-Path $Root 'Scripts\validate_body_shop_performance_lod_pie_v001.py'
$AnalysisScript = Join-Path $Root 'Scripts\analyze_body_shop_performance_lod_v001.py'
$PressMap = Join-Path $Root 'Content\LineBoss\Maps\LB_PressShop_RebuildFromLorry_v20260810_v913.umap'
$BodyMap = Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001\Maps\LB_BodyShop_Prototype_v001.umap'
$PlaySettings = Join-Path $Root 'Saved\Config\WindowsEditor\EditorPerProjectUserSettings.ini'
$PlaySettingsBackup = Join-Path $RunRoot 'EditorPerProjectUserSettings.before-run.ini'
$PlaySettingsExisted = Test-Path -LiteralPath $PlaySettings -PathType Leaf
$PlaySettingOverrides = @(
    '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.LevelEditorPlaySettings]:LastExecutedPlayModeType=PlayMode_InEditorFloating',
    '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.LevelEditorPlaySettings]:LastExecutedPlayModeLocation=PlayLocation_DefaultPlayerStart',
    '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.LevelEditorPlaySettings]:NewWindowWidth=1920',
    '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.LevelEditorPlaySettings]:NewWindowHeight=1080',
    '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.LevelEditorPlaySettings]:CenterNewWindow=False'
)

function Assert-NoActiveUnrealProcess {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName }
    if ($Active) {
        throw "Refusing numeric capture while Unreal/build processes are active: $($Active.ProcessName -join ', ')"
    }
}

function Get-HashRecord([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [ordered]@{ path=$Path; exists=$false; length=$null; sha256=$null }
    }
    $Item = Get-Item -LiteralPath $Path
    return [ordered]@{
        path=$Item.FullName
        exists=$true
        length=$Item.Length
        sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $Item.FullName).Hash
    }
}

function Get-ProtectedSnapshot {
    $Files = @($PressMap,$BodyMap,$CaptureScript,$AnalysisScript,$PSCommandPath,$PlaySettings)
    foreach ($Directory in @(
        (Join-Path $Root 'Config'),
        (Join-Path $Root 'Source\LineBossCarFactory'),
        (Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001'),
        (Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopUnderbodySlice_v001'),
        (Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopRobotNative_v001')
    )) {
        if (Test-Path -LiteralPath $Directory -PathType Container) {
            $Files += (Get-ChildItem -LiteralPath $Directory -Recurse -File | ForEach-Object FullName)
        }
    }
    return @($Files | Sort-Object -Unique | ForEach-Object { Get-HashRecord $_ })
}

function Test-SnapshotEqual($Before,$After) {
    return (($Before | ConvertTo-Json -Depth 5 -Compress) -ceq ($After | ConvertTo-Json -Depth 5 -Compress))
}

function Get-OptionalHash([string]$Path) {
    if (Test-Path -LiteralPath $Path -PathType Leaf) { return Get-HashRecord $Path }
    return [ordered]@{ path=$Path; exists=$false; length=$null; sha256=$null }
}

foreach ($Required in @($Project,$Editor,$Python,$CaptureScript,$AnalysisScript,$PressMap,$BodyMap)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) { throw "Required file is missing: $Required" }
}
Assert-NoActiveUnrealProcess
if (Test-Path -LiteralPath $RunRoot) { throw "Refusing to reuse exact validation run directory: $RunRoot" }
New-Item -ItemType Directory -Force -Path $Logs | Out-Null
$Before = Get-ProtectedSnapshot
if ($PlaySettingsExisted) {
    Copy-Item -LiteralPath $PlaySettings -Destination $PlaySettingsBackup
}
$Failure = $null
$EditorExit = $null
$AnalysisExit = $null
$GateStatus = $null
$PlaySettingsRestored = $false

$env:LB_BODYSHOP_PERF_LOD_STAMP = $Stamp
Push-Location $Root
try {
    $UnrealScript = $CaptureScript.Replace('\','/')
    & $Editor $Project "-ExecutePythonScript=$UnrealScript" $PlaySettingOverrides -unattended -nop4 -nosplash `
        -windowed -ResX=1920 -ResY=1080 -csvGpuStats `
        -stdout -FullStdOutLogOutput *> $PieLog
    $EditorExit = $LASTEXITCODE
    if ($EditorExit -ne 0) { throw "Unreal performance/LOD capture exited $EditorExit" }
    if (-not (Test-Path -LiteralPath $RawReceipt -PathType Leaf)) {
        throw "Raw performance/LOD capture receipt is missing: $RawReceipt"
    }
    $Raw = Get-Content -Raw -LiteralPath $RawReceipt | ConvertFrom-Json
    if ([string]$Raw.status -cne 'PASS__BODY_SHOP_PERFORMANCE_LOD_RAW_CAPTURE_V001') {
        throw "Raw performance/LOD capture failed: $($Raw.status) :: $($Raw.detail)"
    }

    & $Python $AnalysisScript --raw-capture $RawReceipt --output $GateReceipt *> $AnalysisLog
    $AnalysisExit = $LASTEXITCODE
    if (-not (Test-Path -LiteralPath $GateReceipt -PathType Leaf)) {
        throw "Numeric performance/LOD gate receipt is missing: $GateReceipt"
    }
    $Gate = Get-Content -Raw -LiteralPath $GateReceipt | ConvertFrom-Json
    $GateStatus = [string]$Gate.status
    if ($AnalysisExit -ne 0 -or $GateStatus -cne 'PASS__BODY_SHOP_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V001') {
        throw "Numeric performance/LOD gate failed (exit=$AnalysisExit status=$GateStatus)"
    }
}
catch {
    $Failure = $_.Exception.Message
}
finally {
    Remove-Item Env:LB_BODYSHOP_PERF_LOD_STAMP -ErrorAction SilentlyContinue
    Pop-Location
    try {
        if ($PlaySettingsExisted) {
            Copy-Item -LiteralPath $PlaySettingsBackup -Destination $PlaySettings -Force
        }
        elseif (Test-Path -LiteralPath $PlaySettings -PathType Leaf) {
            Remove-Item -LiteralPath $PlaySettings -Force
        }
        $PlaySettingsRestored = $true
    }
    catch {
        $RestoreMessage = "Could not restore pre-run editor play settings: $($_.Exception.Message)"
        $Failure = if ($Failure) { "$Failure :: $RestoreMessage" } else { $RestoreMessage }
    }
}

$After = Get-ProtectedSnapshot
$ProtectedUnchanged = Test-SnapshotEqual $Before $After
if (-not $ProtectedUnchanged -and -not $Failure) {
    $Failure = 'Protected Press, Body Shop Content, Config, or gameplay source changed during read-only capture'
}
$Status = if (-not $Failure -and $ProtectedUnchanged -and
    $GateStatus -ceq 'PASS__BODY_SHOP_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V001') {
    'PASS__BODY_SHOP_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_VALIDATION_RUN_V001'
} else {
    'FAIL__BODY_SHOP_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_VALIDATION_RUN_V001'
}

[ordered]@{
    schema='cairnwell/body-shop/experimental-v001/performance-lod-validation-run/v1'
    generated_utc=(Get-Date).ToUniversalTime().ToString('o')
    status=$Status
    stamp=$Stamp
    failure=$Failure
    command_contract=[ordered]@{
        executable=$Editor
        project=$Project
        renderer='real RHI required'
        null_rhi=$false
        csv_gpu_stats=$true
        resolution=@(1920,1080)
        play_surface='new_editor_window_pie'
        viewport_size_authority='APlayerController.GetViewportSize'
        play_setting_overrides=$PlaySettingOverrides
        user_play_settings_restored=$PlaySettingsRestored
        build_or_ubt_launched=$false
    }
    exit_codes=[ordered]@{ unreal_editor=$EditorExit; analyzer=$AnalysisExit }
    raw_capture=Get-OptionalHash $RawReceipt
    gate_receipt=Get-OptionalHash $GateReceipt
    logs=@(
        (Get-OptionalHash $PieLog),
        (Get-OptionalHash $AnalysisLog)
    )
    scripts=@(
        (Get-HashRecord $CaptureScript),
        (Get-HashRecord $AnalysisScript),
        (Get-HashRecord $PSCommandPath)
    )
    protected_snapshot_unchanged=$ProtectedUnchanged
    protected_before=$Before
    protected_after=$After
} | ConvertTo-Json -Depth 9 | Set-Content -LiteralPath $Summary -Encoding utf8

if ($Failure) { throw $Failure }
Write-Output $Summary
