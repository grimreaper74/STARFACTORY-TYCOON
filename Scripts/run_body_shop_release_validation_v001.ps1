[CmdletBinding()]
param(
    [string]$EnvironmentReceipt = 'Saved\Audits\BodyShop\Experimental_v001\environment_lod_release_candidate_validation_v001.json',
    [Parameter(Mandatory=$true)][string]$MaterialReceipt,
    [Parameter(Mandatory=$true)][string]$NativeRobotValidationReceipt,
    [Parameter(Mandatory=$true)][string]$SupportKitValidationReceipt,
    [string]$HismUsageReceipt = 'Saved\Audits\BodyShop\Experimental_v001\presentation_materials_v002_functional_hism_usage_validation_summary_v004.json',
    [string]$VisualReadabilityReceipt = 'Saved\Audits\BodyShop\Experimental_v001\visual_readability_v004_validation.json',
    [string]$ManagementCutawayReceipt = 'Saved\Audits\BodyShop\Experimental_v001\management_cutaway_v005_validation.json',
    [switch]$SkipEditorBuild
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Engine = 'C:\Program Files\Epic Games\UE_5.8'
$Editor = Join-Path $Engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Build = Join-Path $Engine 'Engine\Build\BatchFiles\Build.bat'
$Python = Join-Path $Engine 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$TonalPython = 'C:\Users\greg_\AppData\Local\Programs\Python\Python313\python.exe'
$TonalPythonDll = 'C:\Users\greg_\AppData\Local\Programs\Python\Python313\python313.dll'
$ExpectedTonalPythonVersion = '3.13.3'
$ExpectedTonalPythonSha256 = 'D87063E5597F257004C731B66C59C56C91038861C6877B1A3DCA6B8C4E919125'
$ExpectedTonalPythonDllSha256 = '69FD86EA29370697C203F7E12830084F920F490766A8E3045AF52C036A9AD529'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$RunRoot = Join-Path $Root "Saved\Audits\BodyShop\Experimental_v001\ReleaseValidation\$Stamp"
$Logs = Join-Path $RunRoot 'Logs'
$Automation = Join-Path $Root "Saved\Automation\BodyShop\Experimental_v001\ReleaseValidation_$Stamp"
$LiveReceipt = Join-Path $RunRoot 'live_pie_release_validation_v003.json'
$CaptureDir = Join-Path $Root "Saved\ValidationScreenshots\BodyShop\Experimental_v001\ReleaseValidation\$Stamp"
$TonalReceipt = Join-Path $RunRoot 'visual_readability_v004_tonal_analysis.json'
$Map = Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001\Maps\LB_BodyShop_Prototype_v001.umap'
$CreamMaterial = Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001\Presentation\Materials_v002\MI_LB_BodyShop_CreamPaint_v002.uasset'
$Press = Join-Path $Root 'Content\LineBoss\Maps\LB_PressShop_RebuildFromLorry_v20260810_v913.umap'
$RestoredPress = Join-Path $Root 'Content\LineBoss\Maps\LB_PressShop_FullFactoryRestored_v001.umap'
$LegacySource = Join-Path $Root 'Source\LineBossCarFactory\LBBodyWeldLineActor.cpp'
$LegacyHeader = Join-Path $Root 'Source\LineBossCarFactory\LBBodyWeldLineActor.h'
$CampaignSaveCandidates = @(
    (Join-Path $Root 'Saved\SaveGames\LineBossCampaign_v18.sav'),
    (Join-Path $Root 'Saved\SaveGames\LineBoss_Campaign_v18.sav')
)
$ExpectedVisualV004ReceiptSha256 = '956E08511F2AA840D71B94E07217DBA357EA955B701BA3A8C9F744AAAC11757E'
$ExpectedManagementV005PatchSha256 = '8A305B26C838567FC3F26063B28F9D7FA65382F9A932F762A8CC3C4DD7F7ED50'
$ExpectedManagementV005ReceiptSha256 = 'DCDBCBFA4D47FEBF21A22FD98F30ADC880D037519EBDBC6AE34BD7D4CE9F88D8'
$ExpectedManagementV005MapSha256 = '8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F'
$ExpectedRestoredPressSha256 = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'
$ExpectedDefaultGameSha256 = '4458BB41EE3A56B67B8ECDD6954A46B23FD038A9CB8294E9A79C48580A86852B'
$SupportContractScript = Join-Path $Root 'Scripts\body_shop_support_kit_native_v002_contract.py'

function Assert-NoActiveBuildProcess {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName }
    if ($Active) { throw "Refusing validation while Unreal/build processes are active: $($Active.ProcessName -join ', ')" }
}

function Get-HashRecord([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return [ordered]@{ path=$Path; exists=$false; sha256=$null } }
    return [ordered]@{ path=$Path; exists=$true; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash }
}

function Get-ProtectedSnapshot {
    $Rows = @()
    $Configs = Get-ChildItem -LiteralPath (Join-Path $Root 'Config') -Recurse -File | Sort-Object FullName
    $BodyShopSources = Get-ChildItem -LiteralPath (Join-Path $Root 'Source\LineBossCarFactory') -File |
        Where-Object { $_.Name -like 'LBBodyShop*.h' -or $_.Name -like 'LBBodyShop*.cpp' } |
        Sort-Object FullName
    $NonBodyShopSaves = Get-ChildItem -LiteralPath (Join-Path $Root 'Saved\SaveGames') -File -Filter *.sav -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne 'LineBoss_BodyShopExperimental_v001.sav' } | Sort-Object FullName
    $NativeRobotAssets = Get-ChildItem -LiteralPath (Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopRobotNative_v001') `
        -Recurse -File -Filter '*.uasset' -ErrorAction Stop | Sort-Object FullName
    if (@($NativeRobotAssets).Count -ne 8) {
        throw "Native robot namespace must contain exactly 8 uassets, found $(@($NativeRobotAssets).Count)"
    }
    $NativeSupportAssets = Get-ChildItem -LiteralPath (Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopSupportKitNative_v002') `
        -Recurse -File -Filter '*.uasset' -ErrorAction Stop | Sort-Object FullName
    if (@($NativeSupportAssets).Count -ne 12) {
        throw "Native support-kit namespace must contain exactly 12 uassets, found $(@($NativeSupportAssets).Count)"
    }
    foreach ($Path in @($Press,$RestoredPress,$LegacySource,$LegacyHeader) + $CampaignSaveCandidates + @($BodyShopSources.FullName) + @($Configs.FullName) + @($NonBodyShopSaves.FullName)) {
        $Rows += Get-HashRecord $Path
    }
    foreach ($Path in @($NativeRobotAssets.FullName)) { $Rows += Get-HashRecord $Path }
    foreach ($Path in @($NativeSupportAssets.FullName)) { $Rows += Get-HashRecord $Path }
    return $Rows
}

function Assert-PassReceipt([string]$Path,[string]$Label) {
    $Resolved = if ([IO.Path]::IsPathRooted($Path)) { [IO.Path]::GetFullPath($Path) } else { [IO.Path]::GetFullPath((Join-Path $Root $Path)) }
    if (-not (Test-Path -LiteralPath $Resolved -PathType Leaf)) { throw "$Label receipt is missing: $Resolved" }
    $Json = Get-Content -Raw -LiteralPath $Resolved | ConvertFrom-Json
    if ([string]$Json.status -notlike 'PASS*') { throw "$Label receipt is not PASS: $($Json.status)" }
    return $Resolved
}

function Resolve-ProjectLeaf([string]$Path,[string]$Label) {
    $Candidate = if ([IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $Root $Path }
    $Resolved = [IO.Path]::GetFullPath($Candidate)
    $RootFull = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $RootPrefix = $RootFull + [IO.Path]::DirectorySeparatorChar
    if (-not $Resolved.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the project root: $Resolved"
    }
    if (-not (Test-Path -LiteralPath $Resolved -PathType Leaf)) {
        throw "$Label is missing: $Resolved"
    }
    return $Resolved
}

function Assert-AutomationPass([string]$Path) {
    $ExpectedTests = @(
        'LineBoss.BodyShop.Experimental.ApprovedUnderbodyLayoutGridAndPorts',
        'LineBoss.BodyShop.Experimental.FixtureRobotSlotValidation',
        'LineBoss.BodyShop.Experimental.Isolation.BootstrapFlags',
        'LineBoss.BodyShop.Experimental.Isolation.CameraAndHUD',
        'LineBoss.BodyShop.Experimental.Isolation.Contract',
        'LineBoss.BodyShop.Experimental.Isolation.LegacyNameGate',
        'LineBoss.BodyShop.Experimental.Isolation.RuntimeBootstrapOnly',
        'LineBoss.BodyShop.Experimental.Isolation.RuntimeCommissioningRequired',
        'LineBoss.BodyShop.Experimental.PackagedPerformance.CommandLineGate',
        'LineBoss.BodyShop.Experimental.PackagedPerformance.ExactTokenedMarkers',
        'LineBoss.BodyShop.Experimental.PackagedPerformance.TargetCounts',
        'LineBoss.BodyShop.Experimental.PackageValidation.CommandLineGate',
        'LineBoss.BodyShop.Experimental.PackageValidation.ExactTokenedMarkers',
        'LineBoss.BodyShop.Experimental.PilotSkidSourceContract',
        'LineBoss.BodyShop.Experimental.Placement.GridAndQuarterTurnPreview',
        'LineBoss.BodyShop.Experimental.Presentation.AutomaticSkidConveyorDressing',
        'LineBoss.BodyShop.Experimental.Presentation.DedicatedRuntimeArtAndOpenSafetyRails',
        'LineBoss.BodyShop.Experimental.Presentation.MaterialsV002.FinalMeshBindings',
        'LineBoss.BodyShop.Experimental.Presentation.MaterialsV002.PathsAndParameters',
        'LineBoss.BodyShop.Experimental.Robot.AuthoredPoseAndEightCupContract',
        'LineBoss.BodyShop.Experimental.Robot.MaterialsV002RobotEOATAndProtectedCGun',
        'LineBoss.BodyShop.Experimental.RobotConfiguration.AuthoredInventoryAndEnvelopes',
        'LineBoss.BodyShop.Experimental.RobotConfiguration.ValidatedAddReplaceRemove',
        'LineBoss.BodyShop.Experimental.ServiceDressing.UnconditionalNativeV002SpawnContract',
        'LineBoss.BodyShop.Experimental.ServiceDressing.ExactInventoryRolesAndAssets',
        'LineBoss.BodyShop.Experimental.ServiceDressing.FailClosedContract',
        'LineBoss.BodyShop.Experimental.ServiceDressing.FiniteLayoutAndProcessClearance',
        'LineBoss.BodyShop.Experimental.ServiceDressing.NonWIPVisualOnlyPresentation',
        'LineBoss.BodyShop.Experimental.Runtime.DeterministicContinuousWIPMotion',
        'LineBoss.BodyShop.Experimental.Runtime.DeterministicStageContract',
        'LineBoss.BodyShop.Experimental.Runtime.FixtureWIPPresentationOwnership',
        'LineBoss.BodyShop.Experimental.Runtime.PilotRobotBindingContract',
        'LineBoss.BodyShop.Experimental.Runtime.SaveReloadNoDuplicateWIPContract',
        'LineBoss.BodyShop.Experimental.SaveGameV1Isolation',
        'LineBoss.BodyShop.Experimental.SaveV1AtomicContract',
        'LineBoss.BodyShop.Experimental.StableIdsAndCanonicalDefinitions',
        'LineBoss.BodyShop.Experimental.UI.UMGOnlyOperatorShell',
        'LineBoss.BodyShop.Experimental.UnderbodyProcess.FixtureProcessV1',
        'LineBoss.BodyShop.Experimental.UnderbodyProcess.KitSelectionV1',
        'LineBoss.BodyShop.Experimental.UnderbodyProcess.StableCatalogV1',
        'LineBoss.BodyShop.Experimental.UnderbodyExpansionV2.ApprovedTopology',
        'LineBoss.BodyShop.Experimental.UnderbodyExpansionV2.FailClosed',
        'LineBoss.BodyShop.Experimental.UnderbodyExpansionV2.StableCatalog'
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Automation index missing: $Path" }
    $Report = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    # UE reports warning-bearing successful leaves separately from plain successes.
    # Both categories must sum to the exact successful leaf inventory gated below.
    $CompletedSuccesses = [int]$Report.succeeded + [int]$Report.succeededWithWarnings
    if ($Report.failed -ne 0 -or $Report.notRun -ne 0 -or $Report.inProcess -ne 0 -or $Report.totalDuration -le 0 -or $CompletedSuccesses -ne $ExpectedTests.Count) {
        throw "Body Shop automation failed or incomplete: succeeded=$($Report.succeeded) succeededWithWarnings=$($Report.succeededWithWarnings) failed=$($Report.failed) notRun=$($Report.notRun)"
    }
    $ActualTests = @($Report.tests | Where-Object { $_.state -in @('Success','SuccessWithWarnings') } | ForEach-Object { [string]$_.fullTestPath } | Sort-Object -Unique)
    $MissingTests = @($ExpectedTests | Where-Object { $_ -notin $ActualTests })
    $UnexpectedTests = @($ActualTests | Where-Object { $_ -notin $ExpectedTests })
    if ($ActualTests.Count -ne $ExpectedTests.Count -or $MissingTests.Count -ne 0 -or $UnexpectedTests.Count -ne 0) {
        throw "Body Shop automation test inventory mismatch: expected=$($ExpectedTests.Count) actual=$($ActualTests.Count) missing=$($MissingTests -join ',') unexpected=$($UnexpectedTests -join ',')"
    }
}

function Assert-ProtectedUnchanged($Before,$After) {
    $BeforeJson = $Before | ConvertTo-Json -Depth 4 -Compress
    $AfterJson = $After | ConvertTo-Json -Depth 4 -Compress
    if ($BeforeJson -cne $AfterJson) { throw 'Protected Press v913/full-restored Press, legacy Body Weld, campaign-save or Config hash changed' }
}

function Wait-StableLeaf([string]$Path,[Int64]$MinimumBytes = 1,[string]$ExpectedSha256 = '') {
    $PreviousSignature = $null
    $LastProblem = 'not checked'
    for ($Attempt = 1; $Attempt -le 20; $Attempt++) {
        try {
            if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
                $LastProblem = 'missing'
                $PreviousSignature = $null
            } else {
                $Item = Get-Item -LiteralPath $Path
                $Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
                if ($Item.Length -lt $MinimumBytes) {
                    $LastProblem = "too small ($($Item.Length) bytes)"
                    $PreviousSignature = $null
                } elseif (-not [string]::IsNullOrWhiteSpace($ExpectedSha256) -and $Hash -cne $ExpectedSha256) {
                    $LastProblem = "hash differs from live receipt ($Hash)"
                    $PreviousSignature = $null
                } else {
                    $Signature = "$($Item.Length)|$($Item.LastWriteTimeUtc.Ticks)|$Hash"
                    if ($Signature -ceq $PreviousSignature) { return $Hash }
                    $PreviousSignature = $Signature
                    $LastProblem = 'awaiting a second identical size/time/hash sample'
                }
            }
        } catch {
            $LastProblem = $_.Exception.Message
            $PreviousSignature = $null
        }
        Start-Sleep -Milliseconds 250
    }
    throw "File did not become stable and readable before tonal analysis: $Path ($LastProblem)"
}

function Assert-TonalInputsStable($Live,[string]$StableLiveReceiptSha256) {
    $CaptureRoot = [IO.Path]::GetFullPath($CaptureDir).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $ScreenshotRecords = @($Live.screenshots)
    if ($ScreenshotRecords.Count -ne 6) { throw "Expected six screenshot records before tonal analysis, found $($ScreenshotRecords.Count)" }
    foreach ($Record in $ScreenshotRecords) {
        $Screenshot = [IO.Path]::GetFullPath([string]$Record.path)
        if (-not [IO.Path]::GetDirectoryName($Screenshot).Equals($CaptureRoot, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Tonal-analysis screenshot escapes the fresh capture directory: $Screenshot"
        }
        $ExpectedHash = [string]$Record.sha256
        if ([string]::IsNullOrWhiteSpace($ExpectedHash)) { throw "Screenshot record has no hash: $Screenshot" }
        [void](Wait-StableLeaf $Screenshot 1024 $ExpectedHash)
    }
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $LiveReceipt).Hash -cne $StableLiveReceiptSha256) {
        throw 'Live PIE receipt changed while its screenshot set was stabilizing'
    }
}

function Invoke-TonalAnalyzer([string]$Analyzer,[string]$OutputReceipt) {
    $StdoutLog = Join-Path $Logs 'visual_readability_v004_tonal_analysis.stdout.log'
    $StderrLog = Join-Path $Logs 'visual_readability_v004_tonal_analysis.stderr.log'
    $CombinedLog = Join-Path $Logs 'visual_readability_v004_tonal_analysis.log'
    $Arguments = @(
        ('"{0}"' -f $Analyzer),
        '--capture-dir', ('"{0}"' -f $CaptureDir),
        '--live-receipt', ('"{0}"' -f $LiveReceipt),
        '--output', ('"{0}"' -f $OutputReceipt)
    )
    $Process = Start-Process -FilePath $TonalPython -ArgumentList $Arguments -WorkingDirectory $Root `
        -RedirectStandardOutput $StdoutLog -RedirectStandardError $StderrLog -NoNewWindow -Wait -PassThru
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $Stdout = if (Test-Path -LiteralPath $StdoutLog -PathType Leaf) { [IO.File]::ReadAllText($StdoutLog) } else { '' }
    $Stderr = if (Test-Path -LiteralPath $StderrLog -PathType Leaf) { [IO.File]::ReadAllText($StderrLog) } else { '' }
    [IO.File]::WriteAllText($CombinedLog, "=== stdout ===`r`n$Stdout`r`n=== stderr ===`r`n$Stderr", $Utf8NoBom)
    if ($Process.ExitCode -ne 0) {
        throw "Visual-readability v004 tonal analysis failed ($($Process.ExitCode)); full stdout/stderr: $StdoutLog ; $StderrLog"
    }
}

Assert-NoActiveBuildProcess
if (-not (Test-Path -LiteralPath $TonalPython -PathType Leaf)) {
    throw "Pinned tonal-analysis Python is missing: $TonalPython"
}
$TonalPythonSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $TonalPython).Hash
if ($TonalPythonSha256 -cne $ExpectedTonalPythonSha256) {
    throw "Pinned tonal-analysis Python hash drifted: $TonalPythonSha256"
}
if (-not (Test-Path -LiteralPath $TonalPythonDll -PathType Leaf)) {
    throw "Pinned tonal-analysis Python runtime library is missing: $TonalPythonDll"
}
$TonalPythonDllSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $TonalPythonDll).Hash
if ($TonalPythonDllSha256 -cne $ExpectedTonalPythonDllSha256) {
    throw "Pinned tonal-analysis Python runtime library hash drifted: $TonalPythonDllSha256"
}
$TonalPythonVersion = (& $TonalPython -c 'import platform; print(platform.python_version())' 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0 -or $TonalPythonVersion.Trim() -cne $ExpectedTonalPythonVersion) {
    throw "Pinned tonal-analysis Python version drifted: $TonalPythonVersion"
}
if (-not (Test-Path -LiteralPath $Map -PathType Leaf)) { throw "Body Shop map missing: $Map" }
$Prerequisites = [ordered]@{
    prototype_map = Assert-PassReceipt 'Saved\Audits\BodyShop\v001\body_shop_prototype_map_validation_v001.json' 'Prototype map'
    art = Assert-PassReceipt 'Saved\Audits\BodyShop\Experimental_v001\validate_underbody_slice_art_receipt_v001.json' 'Underbody art'
    environment_patch = Assert-PassReceipt 'Saved\Audits\BodyShop\Experimental_v001\environment_lod_release_candidate_patch_v001.json' 'Environment/map patch'
    environment = Assert-PassReceipt $EnvironmentReceipt 'Environment/map patch'
    materials = Assert-PassReceipt $MaterialReceipt 'Materials'
    native_robot = Assert-PassReceipt $NativeRobotValidationReceipt 'Native six-axis robot fresh-load validation'
    native_support_kit_v002 = Assert-PassReceipt $SupportKitValidationReceipt 'Native support-kit v002 fresh-load validation'
    material_hism_usage = Assert-PassReceipt $HismUsageReceipt 'Materials HISM usage'
    visual_readability = Assert-PassReceipt $VisualReadabilityReceipt 'Visual readability v004'
    management_cutaway = Assert-PassReceipt $ManagementCutawayReceipt 'Management cutaway v005'
}
$SupportContractText = (& $Python $SupportContractScript --project-root $Root `
    --validation-receipt $Prerequisites.native_support_kit_v002 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) { throw "Native support-kit v002 contract failed: $SupportContractText" }
$SupportContract = $SupportContractText | ConvertFrom-Json
if ([int]$SupportContract.asset_count -ne 12 `
        -or [int]$SupportContract.lod_count_per_asset -ne 3 `
        -or (@($SupportContract.lod_triangle_totals) -join ',') -cne '20408,7580,1780' `
        -or @($SupportContract.packages.psobject.Properties).Count -ne 12) {
    throw 'Native support-kit v002 exact receipt/package/LOD contract drifted'
}
$ExpectedServiceHism = [ordered]@{
    EmptyReturnCartNativeV002Instances = [ordered]@{
        mesh = '/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_EmptyReturnCart_v002.SM_LB_BodyShopSupport_EmptyReturnCart_v002'
        instance_count = 6
    }
    ComponentServicePalletNativeV002Instances = [ordered]@{
        mesh = '/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_ComponentServicePallet_v002.SM_LB_BodyShopSupport_ComponentServicePallet_v002'
        instance_count = 3
    }
    EmptySmallPartsCrateNativeV002Instances = [ordered]@{
        mesh = '/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002.SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002'
        instance_count = 3
    }
}
$NativeGate = Get-Content -Raw -LiteralPath $Prerequisites.native_robot | ConvertFrom-Json
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
$ExpectedNativeNamespace = '/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001'
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
$NativeLane = Get-Content -Raw -LiteralPath (Resolve-ProjectLeaf $ExpectedNativeLaneSummary 'Final native robot lane summary') | ConvertFrom-Json
$NativeImport = Get-Content -Raw -LiteralPath (Resolve-ProjectLeaf $ExpectedNativeImportReceipt 'Final native robot import receipt') | ConvertFrom-Json
if ($Prerequisites.native_robot -cne [IO.Path]::GetFullPath($ExpectedNativeValidationReceipt) `
        -or (Get-FileHash -Algorithm SHA256 -LiteralPath $Prerequisites.native_robot).Hash -cne $ExpectedNativeValidationReceiptSha256 `
        -or (Get-FileHash -Algorithm SHA256 -LiteralPath $ExpectedNativeLaneSummary).Hash -cne $ExpectedNativeLaneSummarySha256 `
        -or (Get-FileHash -Algorithm SHA256 -LiteralPath $ExpectedNativeImportReceipt).Hash -cne $ExpectedNativeImportReceiptSha256 `
        -or [string]$NativeLane.status -cne 'PASS__INCIDENT_ARCHIVED_NAMESPACE_MOVED_CLEAN_IMPORT_AND_INDEPENDENT_FRESH_LOAD_BODYSHOP_ROBOT_NATIVE_V001' `
        -or [string]$NativeLane.import_receipt.sha256 -cne $ExpectedNativeImportReceiptSha256 `
        -or [string]$NativeLane.validation_receipt.sha256 -cne $ExpectedNativeValidationReceiptSha256 `
        -or -not [bool]$NativeLane.no_ubt_invoked `
        -or $null -ne $NativeLane.error `
        -or [string]$NativeImport.status -cne 'PASS__INCIDENT_ARCHIVED_AND_INVALID_NAMESPACE_MOVED__FRESH_8_ASSET_3_LOD_HIGH_ELBOW_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001_IMPORT' `
        -or [string]$NativeImport.baseline_sha256 -cne $ExpectedNativeBaselineSha256 `
        -or [string]$NativeImport.clean_disposition_contract_sha256 -cne $ExpectedNativeCleanDispositionContractSha256) {
    throw 'Native robot prerequisite is not the exact final 204134 clean-import evidence chain'
}
if ([string]$NativeGate.'$schema' -cne 'lineboss/audit/bodyshop-robot-native-v001-fresh-load-validation/v1' `
        -or [string]$NativeGate.status -cne 'PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001' `
        -or [string]$NativeGate.baseline_sha256 -cne $ExpectedNativeBaselineSha256 `
        -or [string]$NativeGate.clean_disposition_contract_sha256 -cne $ExpectedNativeCleanDispositionContractSha256 `
        -or [string]$NativeGate.import_receipt_sha256 -cne $ExpectedNativeImportReceiptSha256 `
        -or [string]$NativeGate.destination_namespace -cne $ExpectedNativeNamespace `
        -or [int]$NativeGate.asset_count -ne 8 `
        -or [int]$NativeGate.lod_count_per_asset -ne 3 `
        -or [int]$NativeGate.source_fbx_count -ne 24 `
        -or -not [bool]$NativeGate.fresh_process_proof.distinct `
        -or -not [bool]$NativeGate.target_package_hashes_unchanged_by_fresh_load `
        -or -not [bool]$NativeGate.config_and_existing_promoted_asset_hashes_unchanged `
        -or -not [bool]$NativeGate.strict_per_asset_triangle_monotonicity `
        -or -not [bool]$NativeGate.exactly_one_uv_channel_on_all_24_lods `
        -or -not [bool]$NativeGate.manual_lod_screen_sizes_persisted_after_fresh_process_load `
        -or @($NativeGate.failures).Count -ne 0 `
        -or [string]$NativeGate.press_v913_map_sha256_unchanged -cne '26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6') {
    throw 'Native robot prerequisite is not the exact independent 8-asset/3-LOD PASS gate'
}
$NativeProperties = @($NativeGate.assets.psobject.Properties)
$ExpectedNativePackageHashes = [ordered]@{}
$NativeTriangleTotals = @(0,0,0)
if ($NativeProperties.Count -ne $ExpectedNativeAssets.Count) {
    throw "Native robot receipt asset count drifted: $($NativeProperties.Count)"
}
foreach ($Key in $ExpectedNativeAssets.Keys) {
    $Rows = @($NativeProperties | Where-Object { $_.Name -ceq $Key })
    if ($Rows.Count -ne 1) { throw "Native robot receipt is missing exact asset key: $Key" }
    $Row = $Rows[0].Value
    $ExpectedPackage = "$ExpectedNativeNamespace/$($ExpectedNativeAssets[$Key])"
    $ExpectedObject = "$ExpectedPackage.$([IO.Path]::GetFileName($ExpectedNativeAssets[$Key]))"
    $Disk = Resolve-ProjectLeaf ([string]$Row.package_after_load.path) "Native robot $Key package"
    if ([string]$Row.package_path -cne $ExpectedPackage `
            -or [string]$Row.object_path -cne $ExpectedObject `
            -or [int]$Row.lod_count -ne 3 `
            -or @($Row.lods).Count -ne 3 `
            -or -not [bool]$Row.package_hash_unchanged_by_fresh_load `
            -or [string]$Row.package_after_load.sha256 -cne [string]$ExpectedNativePackageHashesByKey[$Key] `
            -or (Get-FileHash -Algorithm SHA256 -LiteralPath $Disk).Hash -cne [string]$Row.package_after_load.sha256) {
        throw "Native robot receipt/package contract drifted: $Key"
    }
    for ($LodIndex = 0; $LodIndex -lt 3; ++$LodIndex) {
        if ([int]$Row.lods[$LodIndex].uv_channels -ne 1) {
            throw "Native robot receipt UV-channel contract drifted: $Key LOD$LodIndex"
        }
        $NativeTriangleTotals[$LodIndex] += [int]$Row.lods[$LodIndex].triangles
    }
    $ExpectedNativePackageHashes[$ExpectedPackage] = [string]$Row.package_after_load.sha256
}
if (($NativeTriangleTotals -join ',') -cne ($ExpectedNativeTriangleTotals -join ',')) {
    throw "Native robot aggregate triangle totals drifted: $($NativeTriangleTotals -join '/')"
}
$MaterialGate = Get-Content -Raw -LiteralPath $Prerequisites.materials | ConvertFrom-Json
if ([string]$MaterialGate.'$schema' -cne 'lineboss/audit/bodyshop/presentation-materials-v002-native-robot-support-kit-validation-v004/v1' `
        -or [string]$MaterialGate.status -cne 'PASS__FRESH_RELOAD_BODYSHOP_PRESENTATION_MATERIALS_NATIVE_ROBOT_SUPPORT_KIT_V004' `
        -or -not [bool]$MaterialGate.functional_master_usage.used_with_instanced_static_meshes `
        -or @($MaterialGate.assets).Count -ne 14 `
        -or @($MaterialGate.exact_material_namespace_hashes.psobject.Properties).Count -ne 14 `
        -or @($MaterialGate.active_procedural_material_build_meshes.psobject.Properties).Count -ne 3 `
        -or [int]$MaterialGate.historical_robot_material_build_rows_excluded_from_current_release -ne 6 `
        -or [string]$MaterialGate.visual_readability_v004_validation_receipt_sha256 -cne $ExpectedVisualV004ReceiptSha256 `
        -or [string]$MaterialGate.management_cutaway_v005_patch_receipt_sha256 -cne $ExpectedManagementV005PatchSha256 `
        -or [string]$MaterialGate.management_cutaway_v005_validation_receipt_sha256 -cne $ExpectedManagementV005ReceiptSha256 `
        -or [string]$MaterialGate.map_sha256_unchanged -cne $ExpectedManagementV005MapSha256 `
        -or [string]$MaterialGate.protected_full_restored_press_sha256_unchanged -cne $ExpectedRestoredPressSha256) {
    throw 'Materials receipt is not the current full 14-asset/native-robot/support-kit v004 validation'
}
$MaterialNative = $MaterialGate.native_six_axis_robot
$MaterialNativeReceipt = Resolve-ProjectLeaf ([string]$MaterialNative.receipt) 'Materials-linked native robot receipt'
if ($MaterialNativeReceipt -cne $Prerequisites.native_robot `
        -or (Get-FileHash -Algorithm SHA256 -LiteralPath $MaterialNativeReceipt).Hash -cne [string]$MaterialNative.receipt_sha256 `
        -or [string]$MaterialNative.receipt_sha256 -cne $ExpectedNativeValidationReceiptSha256 `
        -or (Resolve-ProjectLeaf ([string]$MaterialNative.lane_summary) 'Materials-linked native robot lane summary') -cne [IO.Path]::GetFullPath($ExpectedNativeLaneSummary) `
        -or [string]$MaterialNative.lane_summary_sha256 -cne $ExpectedNativeLaneSummarySha256 `
        -or (Resolve-ProjectLeaf ([string]$MaterialNative.import_receipt) 'Materials-linked native robot import receipt') -cne [IO.Path]::GetFullPath($ExpectedNativeImportReceipt) `
        -or [string]$MaterialNative.import_receipt_sha256 -cne $ExpectedNativeImportReceiptSha256 `
        -or [string]$MaterialNative.baseline_sha256 -cne $ExpectedNativeBaselineSha256 `
        -or [string]$MaterialNative.clean_disposition_contract_sha256 -cne $ExpectedNativeCleanDispositionContractSha256 `
        -or (@($MaterialNative.lod_triangle_totals) -join ',') -cne ($ExpectedNativeTriangleTotals -join ',')) {
    throw 'Materials receipt is not hash-bound to the exact final native robot evidence chain'
}
$MaterialNativePackages = @($MaterialNative.packages.psobject.Properties)
if ($MaterialNativePackages.Count -ne $ExpectedNativePackageHashes.Count) {
    throw 'Materials receipt native robot package inventory count drifted'
}
foreach ($ExpectedPackage in $ExpectedNativePackageHashes.Keys) {
    $Rows = @($MaterialNativePackages | Where-Object { $_.Name -ceq $ExpectedPackage })
    if ($Rows.Count -ne 1 -or [string]$Rows[0].Value -cne [string]$ExpectedNativePackageHashes[$ExpectedPackage]) {
        throw "Materials receipt native robot package hash drifted: $ExpectedPackage"
    }
}
$MaterialSupport = $MaterialGate.native_support_kit_v002
if ([string]$MaterialSupport.validation_receipt.sha256 -cne `
        [string]$SupportContract.validation_receipt.sha256 `
        -or [string]$MaterialSupport.lane_summary.sha256 -cne `
            [string]$SupportContract.lane_summary.sha256 `
        -or [string]$MaterialSupport.import_receipt.sha256 -cne `
            [string]$SupportContract.import_receipt.sha256 `
        -or [string]$MaterialSupport.recovery_receipt.sha256 -cne `
            [string]$SupportContract.recovery_receipt.sha256 `
        -or (@($MaterialSupport.lod_triangle_totals) -join ',') -cne '20408,7580,1780' `
        -or [int]$MaterialSupport.asset_count -ne 12 `
        -or @($MaterialSupport.packages.psobject.Properties).Count -ne 12) {
    throw 'Materials receipt is not hash-bound to the exact native support-kit v002 authority'
}
foreach ($PackageRow in @($SupportContract.packages.psobject.Properties)) {
    $Matches = @($MaterialSupport.packages.psobject.Properties | Where-Object {
        $_.Name -ceq $PackageRow.Name
    })
    if ($Matches.Count -ne 1 -or [string]$Matches[0].Value -cne [string]$PackageRow.Value) {
        throw "Materials receipt native support-kit package hash drifted: $($PackageRow.Name)"
    }
}
$HismGate = Get-Content -Raw -LiteralPath $Prerequisites.material_hism_usage | ConvertFrom-Json
if ([string]$HismGate.'$schema' -cne 'lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-summary-v004/v1' `
        -or [string]$HismGate.status -cne 'PASS__FRESH_LIVE_PIE_12_CONVEYOR_2_FLOOR_3_SERVICE_BATCH_12_SERVICE_INSTANCE_HISM_NATIVE_PROTECTED_V004' `
        -or [int]$HismGate.editor_exit_code -ne 0 `
        -or [int]$HismGate.missing_instanced_static_mesh_usage_warning_count -ne 0 `
        -or [int]$HismGate.pass_marker_count -ne 1 `
        -or [bool]$HismGate.source_tree.changed `
        -or [bool]$HismGate.config_tree.changed `
        -or @($HismGate.failures).Count -ne 0 `
        -or [bool]$HismGate.maps_materials_meshes_native_robot_press_changed `
        -or $null -eq $HismGate.PSObject.Properties['maps_materials_meshes_native_robot_support_kit_press_changed'] `
        -or [bool]$HismGate.maps_materials_meshes_native_robot_support_kit_press_changed) {
    throw 'Independent live-PIE HISM summary is not the exact conveyor/floor/service native-v004 PASS gate'
}
$HismUeReceipt = Resolve-ProjectLeaf ([string]$HismGate.ue_receipt) 'Linked HISM UE receipt'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $HismUeReceipt).Hash -cne [string]$HismGate.ue_receipt_sha256) {
    throw 'Linked HISM UE receipt hash differs from the v004 summary'
}
$HismUe = Get-Content -Raw -LiteralPath $HismUeReceipt | ConvertFrom-Json
if ([string]$HismUe.'$schema' -cne 'lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-v004/v1' `
        -or [string]$HismUe.status -cne 'PASS__FRESH_PROCESS_LIVE_PIE_BODYSHOP_FUNCTIONAL_HISM_NATIVE_ROBOT_SUPPORT_KIT_PROTECTION_V004' `
        -or @($HismUe.failures).Count -ne 0 `
        -or -not [bool]$HismUe.live_pie.passed `
        -or [int]$HismUe.live_pie.conveyor_cell_count -ne 4 `
        -or [int]$HismUe.live_pie.exercised_conveyor_hism_component_count -ne 12 `
        -or [int]$HismUe.live_pie.floor_cell_count -ne 1 `
        -or [int]$HismUe.live_pie.exercised_floor_hism_component_count -ne 2 `
        -or [int]$HismUe.live_pie.service_dressing_actor_count -ne 1 `
        -or [int]$HismUe.live_pie.service_hism_batch_count -ne 3 `
        -or [int]$HismUe.live_pie.service_hism_instance_count -ne 12 `
        -or [string]$HismUe.protected_hashes_before.body_shop_map -cne $ExpectedManagementV005MapSha256 `
        -or [string]$HismUe.protected_hashes_after.body_shop_map -cne $ExpectedManagementV005MapSha256 `
        -or [string]$HismUe.protected_hashes_before.press_full_factory_restored_v001_map -cne $ExpectedRestoredPressSha256 `
        -or [string]$HismUe.protected_hashes_after.press_full_factory_restored_v001_map -cne $ExpectedRestoredPressSha256 `
        -or [bool]$HismUe.maps_meshes_materials_native_robot_press_changed `
        -or $null -eq $HismUe.PSObject.Properties['maps_materials_meshes_native_robot_support_kit_press_changed'] `
        -or [bool]$HismUe.maps_materials_meshes_native_robot_support_kit_press_changed) {
    throw 'Linked HISM UE receipt does not prove exact 12-conveyor/2-floor/native-service-6-3-3 contract'
}
$HismServiceActor = $HismUe.live_pie.service_dressing_actor
$HismServiceTags = @($HismServiceActor.tags)
if ([string]$HismServiceActor.name -cne 'LB_BodyShop_ServiceDressing_v002' `
        -or -not [bool]$HismServiceActor.active `
        -or -not [bool]$HismServiceActor.valid_contract `
        -or [bool]$HismServiceActor.represents_process_wip `
        -or $HismServiceTags -cnotcontains 'LB.BodyShop.ServiceDressing.v002' `
        -or $HismServiceTags -cnotcontains 'LB.Asset.CleanRoomNative.v002' `
        -or $HismServiceTags -cnotcontains 'LB.NotProcessWIP') {
    throw 'Linked HISM UE receipt service actor identity/tag/non-WIP contract drifted'
}
$HismServiceRows = @($HismUe.live_pie.service_hism_components)
if ($HismServiceRows.Count -ne $ExpectedServiceHism.Count) {
    throw "Linked HISM UE receipt service HISM row count drifted: $($HismServiceRows.Count)"
}
foreach ($ExpectedComponent in $ExpectedServiceHism.Keys) {
    $Matches = @($HismServiceRows | Where-Object {
        [string]$_.component -ceq $ExpectedComponent
    })
    $Expected = $ExpectedServiceHism[$ExpectedComponent]
    if ($Matches.Count -ne 1 `
            -or [string]$Matches[0].mesh -cne [string]$Expected.mesh `
            -or [int]$Matches[0].instance_count -ne [int]$Expected.instance_count) {
        throw "Linked HISM UE receipt service HISM path/count drifted: $ExpectedComponent"
    }
}
$HismNativeBefore = $HismUe.protected_hashes_before.native_six_axis_robot
$HismNativeAfter = $HismUe.protected_hashes_after.native_six_axis_robot
foreach ($HismNative in @($HismNativeBefore,$HismNativeAfter)) {
    $HismNativeReceipt = Resolve-ProjectLeaf ([string]$HismNative.receipt) 'HISM-linked native robot receipt'
    if ($HismNativeReceipt -cne $Prerequisites.native_robot `
            -or (Get-FileHash -Algorithm SHA256 -LiteralPath $HismNativeReceipt).Hash -cne [string]$HismNative.receipt_sha256 `
            -or [string]$HismNative.receipt_sha256 -cne $ExpectedNativeValidationReceiptSha256 `
            -or (Resolve-ProjectLeaf ([string]$HismNative.lane_summary) 'HISM-linked native robot lane summary') -cne [IO.Path]::GetFullPath($ExpectedNativeLaneSummary) `
            -or [string]$HismNative.lane_summary_sha256 -cne $ExpectedNativeLaneSummarySha256 `
            -or (Resolve-ProjectLeaf ([string]$HismNative.import_receipt) 'HISM-linked native robot import receipt') -cne [IO.Path]::GetFullPath($ExpectedNativeImportReceipt) `
            -or [string]$HismNative.import_receipt_sha256 -cne $ExpectedNativeImportReceiptSha256 `
            -or [string]$HismNative.baseline_sha256 -cne $ExpectedNativeBaselineSha256 `
            -or [string]$HismNative.clean_disposition_contract_sha256 -cne $ExpectedNativeCleanDispositionContractSha256 `
            -or (@($HismNative.lod_triangle_totals) -join ',') -cne ($ExpectedNativeTriangleTotals -join ',')) {
        throw 'Linked HISM UE receipt is not hash-bound to the exact final native robot evidence chain'
    }
    $HismNativePackages = @($HismNative.packages.psobject.Properties)
    if ($HismNativePackages.Count -ne $ExpectedNativePackageHashes.Count) {
        throw 'Linked HISM UE receipt native robot package inventory count drifted'
    }
    foreach ($ExpectedPackage in $ExpectedNativePackageHashes.Keys) {
        $Rows = @($HismNativePackages | Where-Object { $_.Name -ceq $ExpectedPackage })
        if ($Rows.Count -ne 1 -or [string]$Rows[0].Value -cne [string]$ExpectedNativePackageHashes[$ExpectedPackage]) {
            throw "Linked HISM UE receipt native robot package hash drifted: $ExpectedPackage"
        }
    }
}
$HismSupportBefore = $HismUe.protected_hashes_before.native_support_kit_v002
$HismSupportAfter = $HismUe.protected_hashes_after.native_support_kit_v002
foreach ($HismSupport in @($HismSupportBefore,$HismSupportAfter)) {
    if ([string]$HismSupport.validation_receipt.sha256 -cne `
            [string]$SupportContract.validation_receipt.sha256 `
            -or (@($HismSupport.lod_triangle_totals) -join ',') -cne '20408,7580,1780' `
            -or [int]$HismSupport.asset_count -ne 12 `
            -or @($HismSupport.packages.psobject.Properties).Count -ne 12) {
        throw 'Linked HISM UE receipt is not hash-bound to native support-kit v002'
    }
    foreach ($ExpectedPackage in @($SupportContract.packages.psobject.Properties)) {
        $Matches = @($HismSupport.packages.psobject.Properties | Where-Object {
            $_.Name -ceq $ExpectedPackage.Name
        })
        if ($Matches.Count -ne 1 `
                -or [string]$Matches[0].Value -cne [string]$ExpectedPackage.Value) {
            throw "Linked HISM UE receipt native support package hash drifted: $($ExpectedPackage.Name)"
        }
    }
}
$VisualGate = Get-Content -Raw -LiteralPath $Prerequisites.visual_readability | ConvertFrom-Json
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Prerequisites.visual_readability).Hash -cne $ExpectedVisualV004ReceiptSha256 `
        -or [string]$VisualGate.'$schema' -cne 'lineboss/audit/bodyshop/visual-readability-v004-validation/v1' `
        -or [string]$VisualGate.status -cne 'PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V004') {
    throw 'Visual readability receipt is not the exact independent v004 validation gate'
}
$ExpectedVisualCreamHash = [string]$VisualGate.cream_material.sha256
if ([string]::IsNullOrWhiteSpace($ExpectedVisualCreamHash)) {
    throw 'Visual readability receipt does not bind the cream material hash'
}
$ManagementGate = Get-Content -Raw -LiteralPath $Prerequisites.management_cutaway | ConvertFrom-Json
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Prerequisites.management_cutaway).Hash -cne $ExpectedManagementV005ReceiptSha256 `
        -or [string]$ManagementGate.'$schema' -cne 'lineboss/audit/bodyshop/management-cutaway-v005-validation/v1' `
        -or [string]$ManagementGate.status -cne 'PASS__FRESH_RELOAD_BODYSHOP_MANAGEMENT_CUTAWAY_V005' `
        -or @($ManagementGate.failures).Count -ne 0 `
        -or [string]$ManagementGate.prerequisites.visual_readability_v004_validation.sha256 -cne $ExpectedVisualV004ReceiptSha256 `
        -or [string]$ManagementGate.prerequisites.management_cutaway_v005_patch.sha256 -cne $ExpectedManagementV005PatchSha256 `
        -or [string]$ManagementGate.map.sha256 -cne $ExpectedManagementV005MapSha256 `
        -or -not [bool]$ManagementGate.map.read_only_fresh_load_hash_unchanged) {
    throw 'Management cutaway receipt is not the exact independent v005 validation gate'
}
$V005CreamRecord = @($ManagementGate.protected_hashes.psobject.Properties | Where-Object { $_.Name -ceq $CreamMaterial })
if ($V005CreamRecord.Count -ne 1 -or -not [bool]$V005CreamRecord[0].Value.exists `
        -or [string]$V005CreamRecord[0].Value.sha256 -cne $ExpectedVisualCreamHash) {
    throw 'Management cutaway v005 receipt does not preserve the exact v004 cream material'
}
$CurrentMapHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Map).Hash
if ($CurrentMapHash -cne $ExpectedManagementV005MapSha256) { throw "Body Shop map hash is not the independently validated management-cutaway v005 candidate: $CurrentMapHash" }
$CurrentRestoredPressHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Resolve-ProjectLeaf $RestoredPress 'Full restored Press map')).Hash
if ($CurrentRestoredPressHash -cne $ExpectedRestoredPressSha256) { throw "Full restored Press map hash drifted: $CurrentRestoredPressHash" }
$CurrentDefaultGameHash = (Get-FileHash -Algorithm SHA256 -LiteralPath `
    (Join-Path $Root 'Config\DefaultGame.ini')).Hash
if ($CurrentDefaultGameHash -cne $ExpectedDefaultGameSha256) {
    throw "DefaultGame.ini native cook-root authority drifted: $CurrentDefaultGameHash"
}
$CurrentCreamHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $CreamMaterial).Hash
if ($CurrentCreamHash -cne $ExpectedVisualCreamHash) { throw "Body Shop cream material hash is not the independently validated visual-readability candidate: $CurrentCreamHash" }
$Before = Get-ProtectedSnapshot
New-Item -ItemType Directory -Force $Logs,$Automation | Out-Null
$env:LB_BODYSHOP_VALIDATION_STAMP = $Stamp
Push-Location $Root
try {
    if (-not $SkipEditorBuild) {
        & $Build LineBossCarFactoryEditor Win64 Development "-Project=$Project" -WaitMutex -NoHotReloadFromIDE *> (Join-Path $Logs 'editor_build.log')
        if ($LASTEXITCODE -ne 0) { throw "Editor Development build failed ($LASTEXITCODE)" }
    }
    & $Editor $Project "-ExecCmds=Automation RunTests LineBoss.BodyShop.Experimental; Quit" `
        "-ReportExportPath=$Automation" '-TestExit=Automation Test Queue Empty' -unattended -nop4 -nosplash `
        -NullRHI -stdout -FullStdOutLogOutput *> (Join-Path $Logs 'automation_full.log')
    Assert-AutomationPass (Join-Path $Automation 'index.json')

    $Script = (Join-Path $Root 'Scripts\validate_body_shop_release_candidate_pie_v002.py').Replace('\','/')
    & $Editor $Project "-ExecutePythonScript=$Script" -unattended -nop4 -nosplash -windowed -ResX=1920 -ResY=1080 `
        -stdout -FullStdOutLogOutput *> (Join-Path $Logs 'live_pie_release_validation.log')
    if (-not (Test-Path -LiteralPath $LiveReceipt)) { throw "Live PIE receipt missing: $LiveReceipt" }
    $StableLiveReceiptSha256 = Wait-StableLeaf $LiveReceipt 1024
    $Live = Get-Content -Raw -LiteralPath $LiveReceipt | ConvertFrom-Json
    $Presentation = $Live.checks.underbody_release_presentation_contract
    $Underbody = $Presentation.underbody_fixture
    $ConveyorChain = $Presentation.continuous_conveyor_chain
    $FixtureWip = $Presentation.fixture_capture_runtime_wip
    $NativeService = $Live.checks.native_support_service_dressing_v002
    if ([string]$Live.'$schema' -cne 'cairnwell/body-shop/experimental-v001/live-pie-release-validation/v3' `
            -or [string]$Live.status -cne 'PASS__BODY_SHOP_RELEASE_CANDIDATE_ACTUAL_PLAYER_PIE' `
            -or @($Live.failures).Count -ne 0 `
            -or [string]$Live.map_sha256_before -cne $ExpectedManagementV005MapSha256 `
            -or [string]$Live.map_sha256_after -cne $ExpectedManagementV005MapSha256 `
            -or -not [bool]$Live.map_hash_unchanged `
            -or @($Live.screenshots).Count -ne 6 `
            -or -not [bool]$Presentation.passed `
            -or -not [bool]$Underbody.no_underbody_main_presentation_mesh `
            -or [string]$Underbody.main_presentation_asset_path -cne '' `
            -or -not [bool]$Underbody.continuous_conveyor `
            -or [double]$Underbody.conveyor_span_cm -ne 1200.0 `
            -or [int]$Underbody.conveyor_structure_instances -ne 23 `
            -or [int]$Underbody.conveyor_roller_instances -ne 50 `
            -or [int]$Underbody.conveyor_safety_instances -ne 2 `
            -or -not [bool]$Underbody.painted_work_zone `
            -or [int]$Underbody.floor_working_zone_instances -ne 2 `
            -or [int]$Underbody.floor_safety_marking_instances -ne 6 `
            -or [double]$Underbody.neutral_conveyor_lane_width_cm -ne 260.0 `
            -or -not [bool]$Underbody.uses_open_rail_safety_presentation `
            -or [int]$Underbody.auto_assembled_fence_segments -ne 18 `
            -or -not [bool]$ConveyorChain.passed `
            -or @($ConveyorChain.cells).Count -ne 4 `
            -or @($ConveyorChain.joints).Count -ne 3 `
            -or @($ConveyorChain.joints | Where-Object { -not [bool]$_.passed -or [double]$_.gap_cm -ne 0.0 }).Count -ne 0 `
            -or -not [bool]$FixtureWip.passed `
            -or [int]$FixtureWip.logical_wip_before_captures -ne 1 `
            -or [int]$FixtureWip.visible_runtime_wip_before_captures -ne 1 `
            -or [int]$FixtureWip.logical_wip_after_both_captures -ne 1 `
            -or [int]$FixtureWip.visible_runtime_wip_after_both_captures -ne 1 `
            -or -not [bool]$FixtureWip.both_captures_completed_with_one_runtime_wip `
            -or -not [bool]$NativeService.passed `
            -or [int]$NativeService.actor_count -ne 1 `
            -or [string]$NativeService.actor_name -cne 'LB_BodyShop_ServiceDressing_v002' `
            -or [bool]$NativeService.represents_process_wip `
            -or [int]$NativeService.hism_batch_count -ne 3 `
            -or [int]$NativeService.hism_instance_count -ne 12 `
            -or (@($NativeService.hism_components | ForEach-Object { [int]$_.instance_count } | Sort-Object) -join ',') -cne '3,3,6' `
            -or [string]$NativeService.runtime_full_stillage_getter -cne 'ALBBodyShopPrototypeRuntime::GetPilotStillagePresentationMeshPath' `
            -or [string]$NativeService.runtime_full_stillage_mesh_path -cne '/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_PanelStillage_Full_v002.SM_LB_BodyShopSupport_PanelStillage_Full_v002' `
            -or -not [bool]$Live.native_support_kit_v002_unchanged) {
        throw 'Live PIE gate did not prove current Body flow plus exactly one non-WIP native-v002 service actor, 6/3/3 HISM batches and v002 runtime stillage'
    }
    $LiveServiceTags = @($NativeService.tags)
    if ($LiveServiceTags -cnotcontains 'LB.BodyShop.ServiceDressing.v002' `
            -or $LiveServiceTags -cnotcontains 'LB.Asset.CleanRoomNative.v002' `
            -or $LiveServiceTags -cnotcontains 'LB.NotProcessWIP') {
        throw 'Live PIE native-v002 service actor tags drifted'
    }
    $LiveServiceRows = @($NativeService.hism_components)
    if ($LiveServiceRows.Count -ne $ExpectedServiceHism.Count) {
        throw "Live PIE native-v002 service HISM row count drifted: $($LiveServiceRows.Count)"
    }
    foreach ($ExpectedComponent in $ExpectedServiceHism.Keys) {
        $Matches = @($LiveServiceRows | Where-Object {
            [string]$_.component -ceq $ExpectedComponent
        })
        $Expected = $ExpectedServiceHism[$ExpectedComponent]
        if ($Matches.Count -ne 1 `
                -or [string]$Matches[0].mesh -cne [string]$Expected.mesh `
                -or [int]$Matches[0].instance_count -ne [int]$Expected.instance_count) {
            throw "Live PIE native-v002 service HISM path/count drifted: $ExpectedComponent"
        }
    }
    Assert-TonalInputsStable $Live $StableLiveReceiptSha256
    $TonalAnalyzer = Join-Path $Root 'Scripts\analyze_body_shop_visual_readability_v004.py'
    Invoke-TonalAnalyzer $TonalAnalyzer $TonalReceipt
    if (-not (Test-Path -LiteralPath $TonalReceipt -PathType Leaf)) {
        throw "Visual-readability v004 tonal receipt missing: $TonalReceipt"
    }
    $Tonal = Get-Content -Raw -LiteralPath $TonalReceipt | ConvertFrom-Json
    if ([string]$Tonal.'$schema' -cne 'lineboss/audit/bodyshop/visual-readability-v004-tonal-analysis/v1' `
            -or [string]$Tonal.status -cne 'PASS__BODYSHOP_VISUAL_READABILITY_V004_TONAL_GATES' `
            -or @($Tonal.failures).Count -ne 0) {
        throw "Visual-readability v004 tonal gate failed: $($Tonal.status)"
    }
    Assert-ProtectedUnchanged $Before (Get-ProtectedSnapshot)
    [ordered]@{
        schema='cairnwell/body-shop/experimental-v001/release-validation-run/v1'
        generated_utc=(Get-Date).ToUniversalTime().ToString('o')
        status='PASS__BODY_SHOP_FULL_AUTOMATION_AND_ACTUAL_PLAYER_PIE'
        prerequisites=$Prerequisites
        automation_index=(Join-Path $Automation 'index.json')
        live_pie_receipt=$LiveReceipt
        visual_readability_v004_tonal_receipt=$TonalReceipt
        tonal_python_authority=[ordered]@{
            path=$TonalPython
            version=$TonalPythonVersion.Trim()
            sha256=$TonalPythonSha256
            runtime_library=$TonalPythonDll
            runtime_library_sha256=$TonalPythonDllSha256
        }
        native_support_kit_v002_authority=$SupportContract
        protected_hashes=$Before
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $RunRoot 'release_validation_summary_v001.json') -Encoding utf8
}
finally {
    Remove-Item Env:LB_BODYSHOP_VALIDATION_STAMP -ErrorAction SilentlyContinue
    Pop-Location
}
