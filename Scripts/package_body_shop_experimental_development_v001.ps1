[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateNotNullOrEmpty()][string]$ReleaseValidationSummary,
    [ValidateRange(25,180)][int]$SmokeSeconds = 45,
    [string]$ArtifactVolumeRoot = ''
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Engine = 'C:\Program Files\Epic Games\UE_5.8'
$UAT = Join-Path $Engine 'Engine\Build\BatchFiles\RunUAT.bat'
$UnrealPak = Join-Path $Engine 'Engine\Binaries\Win64\UnrealPak.exe'
$ManifestValidator = Join-Path $Root 'Scripts\validate_body_shop_release_candidate_manifest_v001.py'
$SupportContractScript = Join-Path $Root 'Scripts\body_shop_support_kit_native_v002_contract.py'
$MapPackage = '/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001'
$MapLeaf = 'LB_BodyShop_Prototype_v001'
$MapFile = Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001\Maps\LB_BodyShop_Prototype_v001.umap'
$Press = Join-Path $Root 'Content\LineBoss\Maps\LB_PressShop_RebuildFromLorry_v20260810_v913.umap'
$RestoredPress = Join-Path $Root 'Content\LineBoss\Maps\LB_PressShop_FullFactoryRestored_v001.umap'
$ExpectedRestoredPressSha256 = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'
$ExpectedDefaultGameSha256 = '4458BB41EE3A56B67B8ECDD6954A46B23FD038A9CB8294E9A79C48580A86852B'
$SupportCookDirectory = Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopSupportKitNative_v002'
$RunId = '{0}-{1}' -f (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'), ([Guid]::NewGuid().ToString('N').Substring(0,8))
$RunRoot = Join-Path $Root "Saved\Audits\BodyShop\Experimental_v001\PackageValidation\$RunId"
$PackageOutputRoot = if ([string]::IsNullOrWhiteSpace($ArtifactVolumeRoot)) {
    $Root
} else {
    [IO.Path]::GetFullPath($ArtifactVolumeRoot)
}
$Archive = Join-Path $PackageOutputRoot "Builds\BodyShopExperimental_v001\Development_$RunId"
$Stage = Join-Path $PackageOutputRoot "Saved\StagedBuilds\BodyShopExperimental_v001_$RunId"
$BuildLog = Join-Path $RunRoot 'buildcookrun.log'
$BuildReceipt = Join-Path $RunRoot 'buildcookrun_invocation_v001.json'
$ListingRoot = Join-Path $RunRoot 'ContainerListings'
$ListingToolLogRoot = Join-Path $RunRoot 'ContainerListingLogs'
$ListingReceipt = Join-Path $RunRoot 'container_listing_invocations_v001.json'
$ManifestReceipt = Join-Path $RunRoot 'package_manifest_validation_v002.json'
$ManifestValidatorLog = Join-Path $RunRoot 'package_manifest_validator.log'
$DevelopmentRegistryEvidence = Join-Path $RunRoot 'DevelopmentAssetRegistry.bin'
$PackageSummary = Join-Path $RunRoot 'development_package_summary_v002.json'
$ValidationUserDir = Join-Path $RunRoot 'PackagedUserDir'
$ManifestValidatorStdoutLog = Join-Path $RunRoot 'package_manifest_validator.stdout.log'
$ManifestValidatorStderrLog = Join-Path $RunRoot 'package_manifest_validator.stderr.log'
$Token = [Guid]::NewGuid().ToString('N')
$SavedDirSuffix = "BodyShopPackageValidation_$Token"
$ExperimentalSave = Join-Path $ValidationUserDir "Saved_$SavedDirSuffix\SaveGames\LineBoss_BodyShopExperimental_v001.sav"
$ExpectedSaveMarker = "LINE_BOSS_BODY_SHOP_PACKAGE_VALIDATION_V001 phase=SAVE token=$Token result=PASS stage=WELDING_UNDERBODY logical_wip=1 visible_wip=1 save_slot=LineBoss_BodyShopExperimental_v001"
$ExpectedLoadMarker = "LINE_BOSS_BODY_SHOP_PACKAGE_VALIDATION_V001 phase=LOAD token=$Token result=PASS stage=WELDING_UNDERBODY logical_wip=1 visible_wip=1 save_slot=LineBoss_BodyShopExperimental_v001"

function Assert-Leaf([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "$Label missing: $Path" }
}

function Assert-NoActiveBuildProcess {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $Names -contains $_.ProcessName -or $_.ProcessName -like 'LineBossCarFactory*'
    }
    if ($Active) {
        throw "Refusing package while Unreal/build/game processes are active: $($Active.ProcessName -join ', ')"
    }
}

function Hash([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Resolve-ProjectPath([string]$Path, [string]$Label) {
    $Candidate = if ([IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $Root $Path }
    $Resolved = [IO.Path]::GetFullPath($Candidate)
    $RootFull = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $RootPrefix = $RootFull + [IO.Path]::DirectorySeparatorChar
    if (-not $Resolved.Equals($RootFull, [StringComparison]::OrdinalIgnoreCase) -and
        -not $Resolved.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the project root: $Resolved"
    }
    return $Resolved
}

function Resolve-ProjectLeaf([string]$Path, [string]$Label) {
    $Resolved = Resolve-ProjectPath $Path $Label
    Assert-Leaf $Resolved $Label
    return $Resolved
}

function Resolve-Pass([string]$Path) {
    $Resolved = Resolve-ProjectLeaf $Path 'Required release validation summary'
    $Json = Get-Content -Raw -LiteralPath $Resolved | ConvertFrom-Json
    if ([string]$Json.schema -cne 'cairnwell/body-shop/experimental-v001/release-validation-run/v1' -or
            [string]$Json.status -cne 'PASS__BODY_SHOP_FULL_AUTOMATION_AND_ACTUAL_PLAYER_PIE') {
        throw "Release validation is not the exact current PASS contract: schema=$($Json.schema) status=$($Json.status)"
    }
    return $Resolved
}

function Get-ProtectedHashes([string]$ValidationPath, [string]$VisualValidationPath,
        [string]$ManagementValidationPath, [string]$NativeRobotValidationPath,
        [string]$NativeSupportValidationPath) {
    $BodyShopSourceHashes = @(Get-ChildItem -LiteralPath (Join-Path $Root 'Source\LineBossCarFactory') -File |
        Where-Object { $_.Name -like 'LBBodyShop*.h' -or $_.Name -like 'LBBodyShop*.cpp' } |
        Sort-Object FullName | ForEach-Object {
            [ordered]@{ path = $_.FullName; sha256 = Hash $_.FullName }
        })
    $ConfigHashes = @(Get-ChildItem -LiteralPath (Join-Path $Root 'Config') -Recurse -File |
        Sort-Object FullName | ForEach-Object {
            [ordered]@{ path = $_.FullName; sha256 = Hash $_.FullName }
        })
    $ProjectSaveHashes = @(Get-ChildItem -LiteralPath (Join-Path $Root 'Saved\SaveGames') -File `
        -Filter '*.sav' -ErrorAction SilentlyContinue | Sort-Object FullName | ForEach-Object {
            [ordered]@{ path = $_.FullName; sha256 = Hash $_.FullName }
        })
    $NativeRobotAssetHashes = @(Get-ChildItem -LiteralPath `
        (Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopRobotNative_v001') `
        -Recurse -File -Filter '*.uasset' -ErrorAction Stop | Sort-Object FullName | ForEach-Object {
            [ordered]@{ path = $_.FullName; sha256 = Hash $_.FullName }
        })
    if ($NativeRobotAssetHashes.Count -ne 8) {
        throw "Native robot namespace must contain exactly 8 uassets, found $($NativeRobotAssetHashes.Count)"
    }
    $NativeSupportAssetHashes = @(Get-ChildItem -LiteralPath $SupportCookDirectory `
        -Recurse -File -Filter '*.uasset' -ErrorAction Stop | Sort-Object FullName | ForEach-Object {
            [ordered]@{ path = $_.FullName; sha256 = Hash $_.FullName }
        })
    if ($NativeSupportAssetHashes.Count -ne 12) {
        throw "Native support-kit namespace must contain exactly 12 uassets, found $($NativeSupportAssetHashes.Count)"
    }
    return [ordered]@{
        body_shop_map = Hash $MapFile
        cream_material_v002 = Hash (Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001\Presentation\Materials_v002\MI_LB_BodyShop_CreamPaint_v002.uasset')
        body_shop_game_mode_cpp = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBBodyShopPrototypeGameMode.cpp')
        body_shop_game_mode_h = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBBodyShopPrototypeGameMode.h')
        body_shop_runtime_cpp = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBBodyShopPrototypeRuntime.cpp')
        body_shop_runtime_h = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBBodyShopPrototypeRuntime.h')
        body_shop_save_cpp = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBBodyShopExperimentalSaveGame.cpp')
        body_shop_save_h = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBBodyShopExperimentalSaveGame.h')
        press_v913 = Hash $Press
        press_full_factory_restored_v001 = Hash $RestoredPress
        legacy_cpp = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBBodyWeldLineActor.cpp')
        legacy_h = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBBodyWeldLineActor.h')
        campaign_game_mode_cpp = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBGameMode.cpp')
        campaign_game_mode_h = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBGameMode.h')
        press_save_cpp = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBPressShopSaveGame.cpp')
        press_save_h = Hash (Join-Path $Root 'Source\LineBossCarFactory\LBPressShopSaveGame.h')
        default_engine = Hash (Join-Path $Root 'Config\DefaultEngine.ini')
        default_game = Hash (Join-Path $Root 'Config\DefaultGame.ini')
        existing_body_shop_experimental_save = Hash (Join-Path $Root 'Saved\SaveGames\LineBoss_BodyShopExperimental_v001.sav')
        campaign_v18 = Hash (Join-Path $Root 'Saved\SaveGames\LineBossCampaign_v18.sav')
        release_validation_summary = Hash $ValidationPath
        visual_readability_v004_receipt = Hash $VisualValidationPath
        management_cutaway_v005_receipt = Hash $ManagementValidationPath
        native_robot_fresh_load_validation_receipt = Hash $NativeRobotValidationPath
        native_support_kit_v002_fresh_load_validation_receipt = Hash $NativeSupportValidationPath
        native_robot_assets = $NativeRobotAssetHashes
        native_support_kit_v002_assets = $NativeSupportAssetHashes
        all_body_shop_source = $BodyShopSourceHashes
        all_config_files = $ConfigHashes
        all_project_save_files = $ProjectSaveHashes
    }
}

function Test-HashesEqual($Left, $Right) {
    return (($Left | ConvertTo-Json -Depth 4 -Compress) -ceq
        ($Right | ConvertTo-Json -Depth 4 -Compress))
}

function Assert-ReleaseProtectedHashesCurrent($ReleaseSummary) {
    $Rows = @($ReleaseSummary.protected_hashes)
    if ($Rows.Count -eq 0) {
        throw 'Release validation summary has no protected-hash snapshot'
    }
    foreach ($Row in $Rows) {
        $Path = Resolve-ProjectPath ([string]$Row.path) 'Release protected path'
        $ExistsNow = Test-Path -LiteralPath $Path -PathType Leaf
        if ([bool]$Row.exists -ne $ExistsNow) {
            throw "Release-protected file existence changed after validation: $Path"
        }
        if ($ExistsNow -and (Hash $Path) -cne [string]$Row.sha256) {
            throw "Release-protected file hash changed after validation: $Path"
        }
    }
}

function Write-IoStoreListings([string]$PackageRoot, [string]$Scope) {
    $ScopeListingRoot = Join-Path $ListingRoot $Scope
    New-Item -ItemType Directory -Path $ScopeListingRoot | Out-Null
    $Containers = @(Get-ChildItem -LiteralPath $PackageRoot -Recurse -File -Filter '*.utoc' |
        Where-Object { $_.Name -ine 'global.utoc' } |
        Sort-Object FullName)
    if ($Containers.Count -eq 0) { throw "$Scope package contains no project IoStore container" }

    $Records = @()
    for ($Index = 0; $Index -lt $Containers.Count; ++$Index) {
        $Container = $Containers[$Index]
        $Ucas = [IO.Path]::ChangeExtension($Container.FullName, '.ucas')
        Assert-Leaf $Ucas "$Scope IoStore data container"
        $Csv = Join-Path $ScopeListingRoot ('{0:D3}_{1}.csv' -f $Index, $Container.Name)
        $ToolLog = Join-Path $ListingToolLogRoot ('{0}_{1:D3}_{2}.log' -f $Scope, $Index, $Container.Name)
        if ((Test-Path -LiteralPath $Csv) -or (Test-Path -LiteralPath $ToolLog)) {
            throw "Fresh IoStore evidence path unexpectedly exists: $Csv"
        }
        $StartedUtc = (Get-Date).ToUniversalTime()
        & $UnrealPak "-ListContainer=$($Container.FullName)" "-Csv=$Csv" -UTF8Output *> $ToolLog
        $ExitCode = [int]$LASTEXITCODE
        $FinishedUtc = (Get-Date).ToUniversalTime()
        if ($ExitCode -ne 0) {
            throw "UnrealPak failed to list exact $Scope container $($Container.FullName) ($ExitCode)"
        }
        Assert-Leaf $Csv "$Scope IoStore CSV"
        if ((Get-Item -LiteralPath $Csv).Length -le 0) {
            throw "$Scope IoStore CSV is empty: $Csv"
        }
        $Records += [ordered]@{
            scope = $Scope
            started_utc = $StartedUtc.ToString('o')
            finished_utc = $FinishedUtc.ToString('o')
            exit_code = $ExitCode
            container = $Container.FullName
            container_sha256 = Hash $Container.FullName
            ucas = $Ucas
            ucas_sha256 = Hash $Ucas
            csv = $Csv
            csv_sha256 = Hash $Csv
            tool_log = $ToolLog
            tool_log_sha256 = Hash $ToolLog
        }
    }
    return $Records
}

function Get-ExactLogText([string[]]$Paths) {
    $Parts = @()
    foreach ($Path in $Paths) {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            $Parts += Get-Content -Raw -LiteralPath $Path
        }
    }
    return ($Parts -join "`n")
}

function Invoke-PackagedValidationPhase([ValidateSet('SAVE','LOAD')][string]$Phase) {
    $LowerPhase = if ($Phase -eq 'SAVE') { 'Save' } else { 'Load' }
    $RunNumber = if ($Phase -eq 'SAVE') { 1 } else { 2 }
    $Stem = "run$($RunNumber)_$($Phase.ToLowerInvariant())"
    $Stdout = Join-Path $RunRoot "$Stem.stdout.log"
    $Stderr = Join-Path $RunRoot "$Stem.stderr.log"
    $EngineLog = Join-Path $RunRoot "$Stem.engine.log"
    $ExpectedMarker = if ($Phase -eq 'SAVE') { $ExpectedSaveMarker } else { $ExpectedLoadMarker }
    $ForbiddenPhase = if ($Phase -eq 'SAVE') { 'LOAD' } else { 'SAVE' }
    foreach ($Path in @($Stdout, $Stderr, $EngineLog)) {
        if (Test-Path -LiteralPath $Path) { throw "Fresh packaged process log unexpectedly exists: $Path" }
    }

    $Arguments = @(
        $MapPackage,
        "-LineBossBodyShopPackageValidation=$LowerPhase",
        "-LineBossBodyShopValidationToken=$Token",
        "-UserDir=`"$ValidationUserDir`"",
        "-saveddirsuffix=$SavedDirSuffix",
        "-AbsLog=`"$EngineLog`"",
        '-nullrhi',
        '-nosound',
        '-unattended',
        '-nosplash',
        '-stdout',
        '-FullStdOutLogOutput',
        '-NoHardwareBenchmark'
    )
    $StartedUtc = (Get-Date).ToUniversalTime()
    $Process = Start-Process -FilePath $PackagedExecutable -ArgumentList $Arguments `
        -WorkingDirectory $PackagedWorkingDirectory -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr
    # Windows PowerShell 5.1 can return a null ExitCode after WaitForExit when
    # Start-Process has not materialized the native process handle first.
    $null = $Process.Handle
    $TimedOut = -not $Process.WaitForExit($SmokeSeconds * 1000)
    if ($TimedOut) {
        $Process.Kill()
        $Process.WaitForExit()
    } else {
        # Flush asynchronous redirected stdout/stderr after the timed wait.
        $Process.WaitForExit()
    }
    $FinishedUtc = (Get-Date).ToUniversalTime()
    if ($TimedOut) { throw "Packaged $Phase process exceeded $SmokeSeconds seconds" }
    $ExitCode = $Process.ExitCode
    if ($null -eq $ExitCode) { throw "Packaged $Phase process did not expose an exit code" }
    if ($ExitCode -ne 0) { throw "Packaged $Phase process failed with exit code $ExitCode" }
    Assert-Leaf $EngineLog "Packaged $Phase engine log"

    $EngineText = Get-Content -Raw -LiteralPath $EngineLog
    $AllText = Get-ExactLogText @($EngineLog, $Stdout, $Stderr)
    if ($AllText -match 'Fatal error|Unhandled Exception|Assertion failed') {
        throw "Packaged $Phase logs contain a fatal error"
    }
    if ($EngineText.IndexOf($MapLeaf, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
        throw "Packaged $Phase log does not prove the explicit Body Shop map loaded"
    }
    if ($EngineText -notmatch 'LINE_BOSS_BODY_SHOP_PROTOTYPE.*valid=1') {
        throw "Packaged $Phase log does not prove isolated Body Shop bootstrap success"
    }
    $FinalMarkerLines = @($EngineText -split "`r?`n" | Where-Object {
        $_.Contains('LINE_BOSS_BODY_SHOP_PACKAGE_VALIDATION_V001 phase=')
    })
    if ($FinalMarkerLines.Count -ne 1) {
        throw "Packaged $Phase log must contain exactly one final tokened validation marker; found $($FinalMarkerLines.Count)"
    }
    if ($FinalMarkerLines[0].IndexOf($ExpectedMarker, [StringComparison]::Ordinal) -lt 0) {
        throw "Packaged $Phase final marker is not the exact tokened PASS contract"
    }
    if ($AllText -match "LINE_BOSS_BODY_SHOP_PACKAGE_VALIDATION_V001 phase=$ForbiddenPhase\b") {
        throw "Packaged $Phase process emitted a forbidden $ForbiddenPhase phase marker"
    }

    return [ordered]@{
        phase = $Phase
        started_utc = $StartedUtc.ToString('o')
        finished_utc = $FinishedUtc.ToString('o')
        exit_code = $Process.ExitCode
        expected_marker = $ExpectedMarker
        final_marker_line = $FinalMarkerLines[0]
        stdout = $Stdout
        stdout_sha256 = Hash $Stdout
        stderr = $Stderr
        stderr_sha256 = Hash $Stderr
        engine_log = $EngineLog
        engine_log_sha256 = Hash $EngineLog
    }
}

Assert-NoActiveBuildProcess
Assert-Leaf $Project 'Unreal project'
Assert-Leaf $UAT 'RunUAT'
Assert-Leaf $UnrealPak 'UnrealPak'
Assert-Leaf $ManifestValidator 'Package manifest validator'
Assert-Leaf $SupportContractScript 'Native support-kit contract validator'
Assert-Leaf $MapFile 'Body Shop prototype map'
Assert-Leaf $RestoredPress 'Full restored Press map'
if ((Hash $RestoredPress) -cne $ExpectedRestoredPressSha256) {
    throw "Full restored Press map hash drifted: $(Hash $RestoredPress)"
}
$Python = (Get-Command python -ErrorAction Stop).Source
$Validation = Resolve-Pass $ReleaseValidationSummary
$ReleaseGate = Get-Content -Raw -LiteralPath $Validation | ConvertFrom-Json
Assert-ReleaseProtectedHashesCurrent $ReleaseGate
$VisualValidationReference = [string]$ReleaseGate.prerequisites.visual_readability
if ([string]::IsNullOrWhiteSpace($VisualValidationReference)) {
    throw 'Release validation summary does not chain the visual-readability v004 receipt'
}
$ManagementValidationReference = [string]$ReleaseGate.prerequisites.management_cutaway
if ([string]::IsNullOrWhiteSpace($ManagementValidationReference)) {
    throw 'Release validation summary does not chain the management-cutaway v005 receipt'
}
$NativeRobotValidationReference = [string]$ReleaseGate.prerequisites.native_robot
if ([string]::IsNullOrWhiteSpace($NativeRobotValidationReference)) {
    throw 'Release validation summary does not chain the native six-axis robot fresh-load receipt'
}
$NativeSupportValidationReference = [string]$ReleaseGate.prerequisites.native_support_kit_v002
if ([string]::IsNullOrWhiteSpace($NativeSupportValidationReference)) {
    throw 'Release validation summary does not chain the native support-kit v002 receipt'
}
$VisualValidation = Resolve-ProjectLeaf $VisualValidationReference 'Visual-readability v004 receipt'
$ManagementValidation = Resolve-ProjectLeaf $ManagementValidationReference 'Management-cutaway v005 receipt'
$NativeRobotValidation = Resolve-ProjectLeaf $NativeRobotValidationReference 'Native robot fresh-load receipt'
$NativeSupportValidation = Resolve-ProjectLeaf $NativeSupportValidationReference 'Native support-kit v002 fresh-load receipt'
$SupportContractText = (& $Python $SupportContractScript --project-root $Root `
    --validation-receipt $NativeSupportValidation 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) { throw "Native support-kit v002 contract failed: $SupportContractText" }
$SupportContract = $SupportContractText | ConvertFrom-Json
if ([int]$SupportContract.asset_count -ne 12 `
        -or [int]$SupportContract.lod_count_per_asset -ne 3 `
        -or (@($SupportContract.lod_triangle_totals) -join ',') -cne '20408,7580,1780' `
        -or @($SupportContract.packages.psobject.Properties).Count -ne 12) {
    throw 'Native support-kit v002 receipt/package/LOD authority drifted'
}
$ExpectedNativeRunRoot = Join-Path $Root 'Saved\Audits\BodyShop\RobotNative_v001\UnrealImportLane\20260814T204134Z-19e41ca7'
$ExpectedNativeLaneSummary = Join-Path $ExpectedNativeRunRoot 'lane_summary_v001.json'
$ExpectedNativeImportReceipt = Join-Path $ExpectedNativeRunRoot 'import_receipt_v001.json'
$ExpectedNativeValidationReceipt = Join-Path $ExpectedNativeRunRoot 'fresh_load_validation_receipt_v001.json'
$ExpectedNativeLaneSummarySha256 = 'B1AFEDB019C28B04082497F46B954C29262D0A30B19854D00CF1168537AA2F73'
$ExpectedNativeImportReceiptSha256 = 'B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF'
$ExpectedNativeValidationReceiptSha256 = '9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA'
$ExpectedNativeBaselineSha256 = 'D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31'
$ExpectedNativeCleanDispositionContractSha256 = 'E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3'
$ExpectedNativeTriangleTotals = @(2628,1964,1356)
$VisualGate = Get-Content -Raw -LiteralPath $VisualValidation | ConvertFrom-Json
$ManagementGate = Get-Content -Raw -LiteralPath $ManagementValidation | ConvertFrom-Json
$NativeRobotGate = Get-Content -Raw -LiteralPath $NativeRobotValidation | ConvertFrom-Json
if ([string]$VisualGate.'$schema' -cne 'lineboss/audit/bodyshop/visual-readability-v004-validation/v1' -or
        [string]$VisualGate.status -cne 'PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V004') {
    throw "Visual-readability v004 receipt is not the exact PASS gate: $($VisualGate.status)"
}
$ExpectedVisualCreamHash = [string]$VisualGate.cream_material.sha256
if ([string]::IsNullOrWhiteSpace($ExpectedVisualCreamHash)) {
    throw 'Visual-readability v004 receipt does not bind the cream hash'
}
$VisualValidationHash = Hash $VisualValidation
if ([string]$ManagementGate.'$schema' -cne 'lineboss/audit/bodyshop/management-cutaway-v005-validation/v1' -or
        [string]$ManagementGate.status -cne 'PASS__FRESH_RELOAD_BODYSHOP_MANAGEMENT_CUTAWAY_V005' -or
        @($ManagementGate.failures).Count -ne 0 -or
        [string]$ManagementGate.prerequisites.visual_readability_v004_validation.sha256 -cne $VisualValidationHash -or
        -not [bool]$ManagementGate.map.read_only_fresh_load_hash_unchanged) {
    throw "Management-cutaway v005 receipt is not the exact current PASS gate: $($ManagementGate.status)"
}
$ExpectedManagementMapHash = [string]$ManagementGate.map.sha256
if ([string]::IsNullOrWhiteSpace($ExpectedManagementMapHash)) {
    throw 'Management-cutaway v005 receipt does not bind the current map hash'
}
$NativeLane = Get-Content -Raw -LiteralPath (Resolve-ProjectLeaf $ExpectedNativeLaneSummary 'Final native robot lane summary') | ConvertFrom-Json
$NativeImport = Get-Content -Raw -LiteralPath (Resolve-ProjectLeaf $ExpectedNativeImportReceipt 'Final native robot import receipt') | ConvertFrom-Json
if ($NativeRobotValidation -cne [IO.Path]::GetFullPath($ExpectedNativeValidationReceipt) -or
        (Hash $NativeRobotValidation) -cne $ExpectedNativeValidationReceiptSha256 -or
        (Hash $ExpectedNativeLaneSummary) -cne $ExpectedNativeLaneSummarySha256 -or
        (Hash $ExpectedNativeImportReceipt) -cne $ExpectedNativeImportReceiptSha256 -or
        [string]$NativeLane.status -cne 'PASS__INCIDENT_ARCHIVED_NAMESPACE_MOVED_CLEAN_IMPORT_AND_INDEPENDENT_FRESH_LOAD_BODYSHOP_ROBOT_NATIVE_V001' -or
        [string]$NativeLane.import_receipt.sha256 -cne $ExpectedNativeImportReceiptSha256 -or
        [string]$NativeLane.validation_receipt.sha256 -cne $ExpectedNativeValidationReceiptSha256 -or
        -not [bool]$NativeLane.no_ubt_invoked -or $null -ne $NativeLane.error -or
        [string]$NativeImport.status -cne 'PASS__INCIDENT_ARCHIVED_AND_INVALID_NAMESPACE_MOVED__FRESH_8_ASSET_3_LOD_HIGH_ELBOW_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001_IMPORT' -or
        [string]$NativeImport.baseline_sha256 -cne $ExpectedNativeBaselineSha256 -or
        [string]$NativeImport.clean_disposition_contract_sha256 -cne $ExpectedNativeCleanDispositionContractSha256 -or
        [string]$NativeRobotGate.'$schema' -cne 'lineboss/audit/bodyshop-robot-native-v001-fresh-load-validation/v1' -or
        [string]$NativeRobotGate.status -cne 'PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001' -or
        [string]$NativeRobotGate.baseline_sha256 -cne $ExpectedNativeBaselineSha256 -or
        [string]$NativeRobotGate.clean_disposition_contract_sha256 -cne $ExpectedNativeCleanDispositionContractSha256 -or
        [string]$NativeRobotGate.import_receipt_sha256 -cne $ExpectedNativeImportReceiptSha256 -or
        [string]$NativeRobotGate.destination_namespace -cne '/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001' -or
        [int]$NativeRobotGate.asset_count -ne 8 -or [int]$NativeRobotGate.lod_count_per_asset -ne 3 -or
        [int]$NativeRobotGate.source_fbx_count -ne 24 -or
        -not [bool]$NativeRobotGate.fresh_process_proof.distinct -or
        -not [bool]$NativeRobotGate.target_package_hashes_unchanged_by_fresh_load -or
        -not [bool]$NativeRobotGate.config_and_existing_promoted_asset_hashes_unchanged -or
        -not [bool]$NativeRobotGate.strict_per_asset_triangle_monotonicity -or
        -not [bool]$NativeRobotGate.exactly_one_uv_channel_on_all_24_lods -or
        -not [bool]$NativeRobotGate.manual_lod_screen_sizes_persisted_after_fresh_process_load -or
        [string]$NativeRobotGate.press_v913_map_sha256_unchanged -cne '26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6' -or
        @($NativeRobotGate.failures).Count -ne 0) {
    throw "Native robot receipt is not the exact current 8-asset/3-LOD PASS gate: $($NativeRobotGate.status)"
}
$ExpectedNativeAssets = [ordered]@{
    Base = 'Robot/SM_LB_BodyShopRobotNative_Base_v001'
    J1 = 'Robot/SM_LB_BodyShopRobotNative_J1_v001'
    J2 = 'Robot/SM_LB_BodyShopRobotNative_J2_v001'
    J3 = 'Robot/SM_LB_BodyShopRobotNative_J3_v001'
    J4 = 'Robot/SM_LB_BodyShopRobotNative_J4_v001'
    J5 = 'Robot/SM_LB_BodyShopRobotNative_J5_v001'
    J6 = 'Robot/SM_LB_BodyShopRobotNative_J6_v001'
    CGun = 'Tools/SM_LB_BodyShopToolNative_OpenCGun_v001'
}
$ExpectedNativePackageHashesByKey = [ordered]@{
    Base = 'EB7975C71866AD9531FE8EBA93CAA14EDE06CC4333CCFBF88F965DF5E52E7000'
    J1 = '50C2A7065808D59C6666D52CC44F4BDB045E0B929350D9F821E5DEF027AE54C7'
    J2 = 'E6D5FA37E12B14279FE23042C940B3EF2FB33F3D6EE9D7E0D659526F5A471230'
    J3 = '02D873DD7E6688AC60DD2E4D367A78742D6524CEDF80CABA876E20FD5B2D44C5'
    J4 = 'A9F887F6B8FF3955CD48FA3BF132F6F24A00DAED1765194442AD7999048E997C'
    J5 = 'EE26BCDD02B6F43132B5C2CCDB8F216B01CEDFA163748E8AC05A0CF5397D116F'
    J6 = '832AC4BAD232E5BDBC1675A1E46B64BDFA4A833C5CAF1B4478A8E9492BBA0D10'
    CGun = '7473FA6260B17333ABC5D2833736A657D093458CFA004DD862876096F407EFE1'
}
$NativeRows = @($NativeRobotGate.assets.psobject.Properties)
$NativeTriangleTotals = @(0,0,0)
if ($NativeRows.Count -ne $ExpectedNativeAssets.Count) {
    throw "Native robot receipt asset inventory count drifted: $($NativeRows.Count)"
}
foreach ($Key in $ExpectedNativeAssets.Keys) {
    $Rows = @($NativeRows | Where-Object { $_.Name -ceq $Key })
    if ($Rows.Count -ne 1) { throw "Native robot receipt is missing exact asset key: $Key" }
    $Row = $Rows[0].Value
    $ExpectedPackage = "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/$($ExpectedNativeAssets[$Key])"
    $ExpectedObject = "$ExpectedPackage.$([IO.Path]::GetFileName($ExpectedNativeAssets[$Key]))"
    $Disk = Resolve-ProjectLeaf ([string]$Row.package_after_load.path) "Native robot $Key package"
    if ([string]$Row.package_path -cne $ExpectedPackage -or
            [string]$Row.object_path -cne $ExpectedObject -or
            [int]$Row.lod_count -ne 3 -or @($Row.lods).Count -ne 3 -or
            -not [bool]$Row.package_hash_unchanged_by_fresh_load -or
            [string]$Row.package_after_load.sha256 -cne [string]$ExpectedNativePackageHashesByKey[$Key] -or
            (Hash $Disk) -cne [string]$Row.package_after_load.sha256) {
        throw "Native robot receipt/package contract drifted: $Key"
    }
    for ($LodIndex = 0; $LodIndex -lt 3; ++$LodIndex) {
        if ([int]$Row.lods[$LodIndex].uv_channels -ne 1) {
            throw "Native robot receipt UV-channel contract drifted: $Key LOD$LodIndex"
        }
        $NativeTriangleTotals[$LodIndex] += [int]$Row.lods[$LodIndex].triangles
    }
}
if (($NativeTriangleTotals -join ',') -cne ($ExpectedNativeTriangleTotals -join ',')) {
    throw "Native robot aggregate triangle totals drifted: $($NativeTriangleTotals -join '/')"
}
if ((Hash $MapFile) -cne $ExpectedManagementMapHash) {
    throw 'Current Body Shop map no longer matches the chained management-cutaway v005 receipt'
}
if ((Hash (Join-Path $Root 'Config\DefaultGame.ini')) -cne $ExpectedDefaultGameSha256) {
    throw 'DefaultGame.ini native support/robot cook-root authority drifted'
}
$CreamMaterial = Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001\Presentation\Materials_v002\MI_LB_BodyShop_CreamPaint_v002.uasset'
if ((Hash $CreamMaterial) -cne $ExpectedVisualCreamHash) {
    throw 'Current Body Shop cream material no longer matches the chained visual-readability v004 receipt'
}
if ((Test-Path -LiteralPath $RunRoot) -or (Test-Path -LiteralPath $Archive) -or
    (Test-Path -LiteralPath $Stage)) {
    throw 'Fresh audit/archive/stage path unexpectedly exists'
}
New-Item -ItemType Directory -Path $RunRoot | Out-Null
New-Item -ItemType Directory -Path $ListingRoot | Out-Null
New-Item -ItemType Directory -Path $ListingToolLogRoot | Out-Null
New-Item -ItemType Directory -Path $ValidationUserDir | Out-Null

$Before = Get-ProtectedHashes $Validation $VisualValidation $ManagementValidation `
    $NativeRobotValidation $NativeSupportValidation
$After = $null
$ProtectedUnchanged = $false
$PackageSucceeded = $false
$FailureMessage = $null
$BuildStartedUtc = $null
$BuildFinishedUtc = $null
$BuildExitCode = $null
$ArchiveListings = @()
$StageListings = @()
$DevelopmentRegistrySource = $null
$ManifestValidatorExitCode = $null
$Run1 = $null
$Run2 = $null
$SaveHashAfterRun1 = $null
$SaveHashAfterRun2 = $null

try {
    $BuildCookRunArgs = @(
        'BuildCookRun',
        "-project=$Project",
        '-noP4',
        '-platform=Win64',
        '-clientconfig=Development',
        '-build',
        '-cook',
        "-map=$MapPackage",
        "-CookDir=$SupportCookDirectory",
        '-stage',
        '-pak',
        '-iostore',
        '-archive',
        "-archivedirectory=$Archive",
        "-stagingdirectory=$Stage",
        '-utf8output',
        '-unattended'
    )
    $BuildStartedUtc = (Get-Date).ToUniversalTime()
    try {
        & $UAT @BuildCookRunArgs *> $BuildLog
        $BuildExitCode = [int]$LASTEXITCODE
    }
    finally {
        $BuildFinishedUtc = (Get-Date).ToUniversalTime()
        [ordered]@{
            schema = 'cairnwell/body-shop/experimental-v001/buildcookrun-invocation/v1'
            started_utc = $BuildStartedUtc.ToString('o')
            finished_utc = $BuildFinishedUtc.ToString('o')
            exit_code = $BuildExitCode
            configuration = 'Development'
            map_package = $MapPackage
            archive_root = $Archive
            stage_root = $Stage
            log = $BuildLog
            log_sha256 = Hash $BuildLog
            command = $UAT
            command_args = $BuildCookRunArgs
        } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $BuildReceipt -Encoding utf8
    }
    if ($BuildExitCode -ne 0) { throw "Development BuildCookRun failed ($BuildExitCode)" }

    $ArchiveListings = @(Write-IoStoreListings $Archive 'archive')
    $StageListings = @(Write-IoStoreListings $Stage 'stage')
    [ordered]@{
        schema = 'cairnwell/body-shop/experimental-v001/iostore-listing-invocations/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        archive_root = $Archive
        stage_root = $Stage
        records = @($ArchiveListings + $StageListings)
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ListingReceipt -Encoding utf8

    $RegistrySearchRoots = @($Stage, (Join-Path $Root 'Saved\Cooked\Windows')) |
        Where-Object { Test-Path -LiteralPath $_ -PathType Container }
    if ($RegistrySearchRoots.Count -gt 0) {
        $FreshFloor = $BuildStartedUtc.AddSeconds(-2)
        $FreshCeiling = $BuildFinishedUtc.AddSeconds(120)
        $DevelopmentRegistrySource = @(Get-ChildItem -LiteralPath $RegistrySearchRoots -Recurse -File `
            -Filter 'DevelopmentAssetRegistry.bin' -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTimeUtc -ge $FreshFloor -and $_.LastWriteTimeUtc -le $FreshCeiling } |
            Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1)
        if ($DevelopmentRegistrySource.Count -gt 0) {
            $DevelopmentRegistrySource = $DevelopmentRegistrySource[0]
            Copy-Item -LiteralPath $DevelopmentRegistrySource.FullName -Destination $DevelopmentRegistryEvidence
            (Get-Item -LiteralPath $DevelopmentRegistryEvidence).LastWriteTimeUtc = $DevelopmentRegistrySource.LastWriteTimeUtc
        } else {
            $DevelopmentRegistrySource = $null
        }
    }

    $ManifestArgs = @(
        ('"{0}"' -f $ManifestValidator),
        '--project-root', ('"{0}"' -f $Root),
        '--archive-root', ('"{0}"' -f $Archive),
        '--stage-root', ('"{0}"' -f $Stage),
        '--build-receipt', ('"{0}"' -f $BuildReceipt),
        '--buildcookrun-log', ('"{0}"' -f $BuildLog),
        '--container-listing-root', ('"{0}"' -f $ListingRoot),
        '--container-listing-receipt', ('"{0}"' -f $ListingReceipt),
        '--native-robot-validation-receipt', ('"{0}"' -f $NativeRobotValidation),
        '--native-support-validation-receipt', ('"{0}"' -f $NativeSupportValidation),
        '--output', ('"{0}"' -f $ManifestReceipt)
    )
    if ($DevelopmentRegistrySource) {
        $ManifestArgs += @('--development-asset-registry', ('"{0}"' -f $DevelopmentRegistryEvidence))
    }
    $ManifestProcess = Start-Process -FilePath $Python -ArgumentList $ManifestArgs `
        -WorkingDirectory $Root -RedirectStandardOutput $ManifestValidatorStdoutLog `
        -RedirectStandardError $ManifestValidatorStderrLog -NoNewWindow -Wait -PassThru
    $ManifestValidatorExitCode = [int]$ManifestProcess.ExitCode
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $ManifestStdout = if (Test-Path -LiteralPath $ManifestValidatorStdoutLog -PathType Leaf) {
        [IO.File]::ReadAllText($ManifestValidatorStdoutLog)
    } else { '' }
    $ManifestStderr = if (Test-Path -LiteralPath $ManifestValidatorStderrLog -PathType Leaf) {
        [IO.File]::ReadAllText($ManifestValidatorStderrLog)
    } else { '' }
    [IO.File]::WriteAllText(
        $ManifestValidatorLog,
        "=== stdout ===`r`n$ManifestStdout`r`n=== stderr ===`r`n$ManifestStderr",
        $Utf8NoBom
    )
    if ($ManifestValidatorExitCode -ne 0) {
        throw "Exact current-run package manifest validation failed ($ManifestValidatorExitCode); full stdout/stderr: $ManifestValidatorStdoutLog ; $ManifestValidatorStderrLog"
    }
    $Manifest = Get-Content -Raw -LiteralPath $ManifestReceipt | ConvertFrom-Json
    if ([string]$Manifest.status -cne 'PASS__BODY_SHOP_DEVELOPMENT_PACKAGE_MANIFEST_EXACT_CONTAINER_V002') {
        throw "Package manifest did not return the exact PASS contract: $($Manifest.status)"
    }

    $PackagedWorkingDirectory = Join-Path $Archive 'Windows'
    $PackagedExecutable = Join-Path $PackagedWorkingDirectory 'LineBossCarFactory\Binaries\Win64\LineBossCarFactory.exe'
    Assert-Leaf $PackagedExecutable 'Exact packaged Development executable'
    if (Test-Path -LiteralPath $ExperimentalSave) {
        throw "Fresh package-validation user directory already contains the experimental save: $ExperimentalSave"
    }

    $Run1 = Invoke-PackagedValidationPhase 'SAVE'
    Assert-Leaf $ExperimentalSave 'Run-1 isolated Body Shop experimental save'
    if ((Get-Item -LiteralPath $ExperimentalSave).Length -le 0) {
        throw 'Run-1 isolated Body Shop experimental save is empty'
    }
    $SaveHashAfterRun1 = Hash $ExperimentalSave

    $Run2 = Invoke-PackagedValidationPhase 'LOAD'
    Assert-Leaf $ExperimentalSave 'Run-2 isolated Body Shop experimental save'
    $SaveHashAfterRun2 = Hash $ExperimentalSave
    if ($SaveHashAfterRun2 -cne $SaveHashAfterRun1) {
        throw 'Run-2 load mutated or replaced the run-1 experimental save'
    }

    $After = Get-ProtectedHashes $Validation $VisualValidation $ManagementValidation `
        $NativeRobotValidation $NativeSupportValidation
    $ProtectedUnchanged = Test-HashesEqual $Before $After
    if (-not $ProtectedUnchanged) {
        throw 'Protected Body Shop/Press/campaign/config/release-evidence hashes changed during packaging validation'
    }
    $PackageSucceeded = $true
}
catch {
    $FailureMessage = $_.Exception.Message
    throw
}
finally {
    if ($null -eq $After) {
        $After = Get-ProtectedHashes $Validation $VisualValidation $ManagementValidation `
            $NativeRobotValidation $NativeSupportValidation
    }
    $ProtectedUnchanged = Test-HashesEqual $Before $After
    $ProtectedChangedAfterGate = $PackageSucceeded -and -not $ProtectedUnchanged
    if ($ProtectedChangedAfterGate) {
        $PackageSucceeded = $false
        $FailureMessage = 'Protected hashes changed after the final package gate'
    }
    [ordered]@{
        schema = 'cairnwell/body-shop/experimental-v001/development-package-run/v2'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = if ($PackageSucceeded) {
            'PASS__BODY_SHOP_DEVELOPMENT_PACKAGE_TWO_PROCESS_V002'
        } else {
            'FAIL__BODY_SHOP_DEVELOPMENT_PACKAGE_TWO_PROCESS_V002'
        }
        failure = $FailureMessage
        configuration = 'Development'
        shipping_requested = $false
        explicit_map = $MapPackage
        default_map_changed = $false
        release_validation_summary = $Validation
        release_validation_summary_sha256 = Hash $Validation
        visual_readability_v004_receipt = $VisualValidation
        visual_readability_v004_receipt_sha256 = Hash $VisualValidation
        management_cutaway_v005_receipt = $ManagementValidation
        management_cutaway_v005_receipt_sha256 = Hash $ManagementValidation
        native_robot_fresh_load_validation_receipt = $NativeRobotValidation
        native_robot_fresh_load_validation_receipt_sha256 = Hash $NativeRobotValidation
        native_support_kit_v002_fresh_load_validation_receipt = $NativeSupportValidation
        native_support_kit_v002_fresh_load_validation_receipt_sha256 = Hash $NativeSupportValidation
        native_support_kit_v002_authority = $SupportContract
        native_support_kit_v002_explicit_cook_directory = $SupportCookDirectory
        expected_management_map_sha256 = $ExpectedManagementMapHash
        expected_visual_cream_sha256 = $ExpectedVisualCreamHash
        archive = $Archive
        stage = $Stage
        build_receipt = $BuildReceipt
        build_receipt_sha256 = Hash $BuildReceipt
        manifest_receipt = $ManifestReceipt
        manifest_receipt_sha256 = Hash $ManifestReceipt
        manifest_validator_exit_code = $ManifestValidatorExitCode
        manifest_validator_log = $ManifestValidatorLog
        manifest_validator_log_sha256 = Hash $ManifestValidatorLog
        manifest_validator_stdout = $ManifestValidatorStdoutLog
        manifest_validator_stdout_sha256 = Hash $ManifestValidatorStdoutLog
        manifest_validator_stderr = $ManifestValidatorStderrLog
        manifest_validator_stderr_sha256 = Hash $ManifestValidatorStderrLog
        container_listing_receipt = $ListingReceipt
        container_listing_receipt_sha256 = Hash $ListingReceipt
        archive_container_listings = $ArchiveListings
        stage_container_listings = $StageListings
        development_asset_registry_source = if ($DevelopmentRegistrySource) { $DevelopmentRegistrySource.FullName } else { $null }
        development_asset_registry_evidence = if (Test-Path -LiteralPath $DevelopmentRegistryEvidence) { $DevelopmentRegistryEvidence } else { $null }
        validation_token = $Token
        packaged_saved_dir_suffix = $SavedDirSuffix
        packaged_run1_save = $Run1
        packaged_run2_load = $Run2
        isolated_experimental_save = $ExperimentalSave
        isolated_experimental_save_sha256_after_run1 = $SaveHashAfterRun1
        isolated_experimental_save_sha256_after_run2 = $SaveHashAfterRun2
        protected_before = $Before
        protected_after = $After
        protected_unchanged = $ProtectedUnchanged
        packaged_save_restart_load = if ($PackageSucceeded) {
            'PASS__EXACT_TOKENED_RUN1_SAVE_AND_RUN2_LOAD'
        } else {
            'FAIL__EXACT_TOKENED_RUN1_SAVE_AND_RUN2_LOAD_NOT_PROVEN'
        }
    } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $PackageSummary -Encoding utf8
    if ($PackageSucceeded) {
        Write-Output "PASS__BODY_SHOP_DEVELOPMENT_PACKAGE_TWO_PROCESS_V002"
        Write-Output $PackageSummary
    }
    if ($ProtectedChangedAfterGate) {
        throw 'Protected hashes changed after the final package gate'
    }
}
