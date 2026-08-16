[CmdletBinding()]
param(
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8',
    [switch]$SkipEditorBuild
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Build = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
$Builder = Join-Path $Root 'Scripts\create_one_factory_shell_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_one_factory_shell_v001.py'
$Map = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Maps\LB_MoorcrossWorks_OneFactory_v001.umap'
$CreateReceipt = Join-Path $Root 'Saved\Audits\OneFactory\v001\one_factory_shell_create_v001.json'
$ValidationReceipt = Join-Path $Root 'Saved\Audits\OneFactory\v001\one_factory_shell_validation_v001.json'
$ExpectedBuilderSha256 = '4EE0A437A9BCC3A5431C39B2D27BB05067FA74F1A6A586B5C2DF05E412131728'
$ExpectedValidatorSha256 = '2043ED396DFD366CB857F208A38054EE9CCE4906A04EA53C4ABD86ADF1CB5E61'
$CreateStatus = 'PASS__ONE_FACTORY_NATIVE_HISM_SHELL_ONE_BOOTSTRAP_ONE_PRESS_AUTHORITY_ZERO_PRODUCTION_MACHINE_OR_WIP'
$ValidationStatus = 'PASS__FRESH_RELOAD_ONE_FACTORY_NATIVE_HISM_SHELL_EXACT_AUTHORITIES_ZERO_PRODUCTION_MACHINE_OR_WIP'

$CriticalProtected = [ordered]@{
    'Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap' = '26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6'
    'Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap' = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'
    'Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap' = '8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F'
    'Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap' = '2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069'
}

function Get-ProjectRelative([string]$Path) {
    $Full = [IO.Path]::GetFullPath($Path)
    $RootPrefix = $Root.TrimEnd('\') + '\'
    if (-not $Full.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the project root: $Full"
    }
    return $Full.Substring($RootPrefix.Length).Replace('\','/')
}

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
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
    $SaveRoot = Join-Path $Root 'Saved\SaveGames'
    if (Test-Path -LiteralPath $SaveRoot -PathType Container) {
        foreach ($Item in @(Get-ChildItem -LiteralPath $SaveRoot -File -Recurse | Sort-Object FullName)) {
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
    $BeforeJson = $Before | ConvertTo-Json -Depth 4 -Compress
    $AfterJson = $After | ConvertTo-Json -Depth 4 -Compress
    if ($BeforeJson -cne $AfterJson) {
        $Names = @($Before.Keys + $After.Keys | Sort-Object -Unique | Where-Object {
            [string]$Before[$_] -cne [string]$After[$_]
        })
        throw "$Stage changed protected Press/Body/Paint/Config/SaveGames files: $($Names -join ', ')"
    }
}

function Assert-ExactMarker([string]$Log, [string]$Marker) {
    if (-not (Test-Path -LiteralPath $Log -PathType Leaf)) {
        throw "Expected Unreal log is missing: $Log"
    }
    $Count = @(Select-String -LiteralPath $Log -SimpleMatch $Marker).Count
    if ($Count -ne 1) {
        throw "Expected exactly one '$Marker' marker in $Log; found $Count"
    }
}

foreach ($Required in @($Project,$Editor,$Build,$Builder,$Validator)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) {
        throw "One Factory shell prerequisite is missing: $Required"
    }
}
if ((Get-Sha256 $Builder) -cne $ExpectedBuilderSha256) {
    throw 'Frozen One Factory builder script hash drifted'
}
if ((Get-Sha256 $Validator) -cne $ExpectedValidatorSha256) {
    throw 'Frozen One Factory validator script hash drifted'
}
if (Test-Path -LiteralPath $Map) {
    throw "Refusing to overwrite protected One Factory destination: $Map"
}
if (Test-Path -LiteralPath $CreateReceipt) {
    throw "Refusing to overwrite One Factory creation receipt: $CreateReceipt"
}
if (Test-Path -LiteralPath $ValidationReceipt) {
    throw "Refusing to overwrite One Factory validation receipt: $ValidationReceipt"
}

$LiveUnreal = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -in @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool')
})
if ($LiveUnreal.Count -ne 0) {
    throw "Close active Unreal/build processes before the protected one-shot: $($LiveUnreal.ProcessName -join ', ')"
}

$Before = Get-ProtectedSnapshot
$DefaultEngineRelative = 'Config/DefaultEngine.ini'
$DefaultEngineBefore = [string]$Before[$DefaultEngineRelative]
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$RunRoot = Join-Path $Root "Saved\Audits\OneFactory\v001\Runs\$Stamp"
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
$BuildLog = Join-Path $RunRoot 'editor_build.log'
$BuilderLog = Join-Path $RunRoot 'shell_create.log'
$ValidatorLog = Join-Path $RunRoot 'shell_validation_fresh_process.log'

Push-Location $Root
try {
    if (-not $SkipEditorBuild) {
        & $Build LineBossCarFactoryEditor Win64 Development "-Project=$Project" `
            -WaitMutex -NoHotReloadFromIDE *> $BuildLog
        if ($LASTEXITCODE -ne 0) {
            throw "LineBossCarFactoryEditor build failed ($LASTEXITCODE); see $BuildLog"
        }
    }

    $BuilderCommand = $Builder.Replace('\','/')
    & $Editor $Project "-ExecutePythonScript=$BuilderCommand" -unattended -nop4 `
        -nosplash -NullRHI -stdout -FullStdOutLogOutput *> $BuilderLog
    if ($LASTEXITCODE -ne 0) {
        throw "One Factory shell creation failed ($LASTEXITCODE); see $BuilderLog"
    }
    Assert-ExactMarker $BuilderLog 'LINE_BOSS_ONE_FACTORY_SHELL_CREATE_V001_PASS'
    if (-not (Test-Path -LiteralPath $Map -PathType Leaf)) {
        throw "Builder reported PASS but did not write the destination map: $Map"
    }
    if (-not (Test-Path -LiteralPath $CreateReceipt -PathType Leaf)) {
        throw "Builder reported PASS but did not write the creation receipt: $CreateReceipt"
    }
    $Create = Get-Content -Raw -LiteralPath $CreateReceipt | ConvertFrom-Json
    if ([string]$Create.'$schema' -cne 'lineboss/audit/one-factory/shell-create-v001/v1' `
            -or [string]$Create.status -cne $CreateStatus `
            -or [string]$Create.builder_script_sha256 -cne $ExpectedBuilderSha256 `
            -or [string]$Create.map -cne '/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001' `
            -or [string]$Create.map_sha256 -cne (Get-Sha256 $Map) `
            -or [int]$Create.facts.nonfoundation_actor_count -ne 26 `
            -or [int]$Create.facts.map_authored_actor_count -ne 25 `
            -or [int]$Create.facts.engine_generated_navigation_actor_count -ne 1 `
            -or [int]$Create.facts.hism_actor_count -ne 10 `
            -or [int]$Create.facts.hism_instance_count -ne 1194 `
            -or [int]$Create.facts.production_machine_or_wip_actor_count -ne 0 `
            -or [bool]$Create.default_engine_modified) {
        throw 'Creation receipt did not prove the exact native HISM shell contract'
    }
    Assert-SameSnapshot $Before (Get-ProtectedSnapshot) 'One Factory shell creation'

    $ValidatorCommand = $Validator.Replace('\','/')
    & $Editor $Project "-ExecutePythonScript=$ValidatorCommand" -unattended -nop4 `
        -nosplash -NullRHI -stdout -FullStdOutLogOutput *> $ValidatorLog
    if ($LASTEXITCODE -ne 0) {
        throw "Fresh-process One Factory validation failed ($LASTEXITCODE); see $ValidatorLog"
    }
    Assert-ExactMarker $ValidatorLog 'LINE_BOSS_ONE_FACTORY_SHELL_VALIDATION_V001_PASS'
    if (-not (Test-Path -LiteralPath $ValidationReceipt -PathType Leaf)) {
        throw "Validator reported PASS but did not write its receipt: $ValidationReceipt"
    }
    $Validation = Get-Content -Raw -LiteralPath $ValidationReceipt | ConvertFrom-Json
    if ([string]$Validation.'$schema' -cne 'lineboss/audit/one-factory/shell-validation-v001/v1' `
            -or [string]$Validation.status -cne $ValidationStatus `
            -or [string]$Validation.builder_script_sha256 -cne $ExpectedBuilderSha256 `
            -or [string]$Validation.map_sha256 -cne [string]$Create.map_sha256 `
            -or @($Validation.failures).Count -ne 0 `
            -or [int]$Validation.facts.nonfoundation_actor_count -ne 26 `
            -or [int]$Validation.facts.map_authored_actor_count -ne 25 `
            -or [int]$Validation.facts.engine_generated_navigation_actor_count -ne 1 `
            -or [int]$Validation.facts.hism_actor_count -ne 10 `
            -or [int]$Validation.facts.hism_total_instance_count -ne 1194 `
            -or [int]$Validation.facts.production_machine_or_wip_actor_count -ne 0 `
            -or [bool]$Validation.writes_to_content_config_or_saves) {
        throw 'Fresh-process validation receipt did not prove the exact shell contract'
    }

    $After = Get-ProtectedSnapshot
    Assert-SameSnapshot $Before $After 'Fresh-process One Factory validation'
    if ([string]$After[$DefaultEngineRelative] -cne $DefaultEngineBefore) {
        throw 'DefaultEngine.ini changed; the One Factory map must use only its local GameMode override'
    }

    $Summary = [ordered]@{
        '$schema' = 'lineboss/audit/one-factory/shell-run-summary-v001/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__ONE_SHOT_BUILD_CREATE_AND_INDEPENDENT_FRESH_RELOAD_VALIDATION'
        map = '/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001'
        map_sha256 = Get-Sha256 $Map
        builder = [ordered]@{ path = Get-ProjectRelative $Builder; sha256 = $ExpectedBuilderSha256 }
        validator = [ordered]@{ path = Get-ProjectRelative $Validator; sha256 = $ExpectedValidatorSha256 }
        create_receipt = [ordered]@{ path = Get-ProjectRelative $CreateReceipt; sha256 = Get-Sha256 $CreateReceipt }
        validation_receipt = [ordered]@{ path = Get-ProjectRelative $ValidationReceipt; sha256 = Get-Sha256 $ValidationReceipt }
        protected_hashes = $After
        default_engine_unchanged = $true
        source_config_saves_or_protected_maps_changed = $false
        production_machine_or_wip_actor_count = 0
        logs = [ordered]@{
            build = if (Test-Path -LiteralPath $BuildLog) { Get-ProjectRelative $BuildLog } else { $null }
            creation = Get-ProjectRelative $BuilderLog
            validation = Get-ProjectRelative $ValidatorLog
        }
    }
    $SummaryPath = Join-Path $RunRoot 'one_factory_shell_run_summary_v001.json'
    $Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $SummaryPath -Encoding utf8
    Write-Host "PASS: One Factory shell created and independently validated."
    Write-Host "Map: $Map"
    Write-Host "Summary: $SummaryPath"
}
finally {
    Pop-Location
}
