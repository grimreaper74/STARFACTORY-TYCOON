[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateNotNullOrEmpty()][string]$DevelopmentPackageSummary,
    [string]$ProjectRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8',
    [ValidateRange(120,600)][int]$PerViewTimeoutSeconds = 240
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = [IO.Path]::GetFullPath($ProjectRoot)
$MapPackage = '/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001'
$PackageSchema = 'cairnwell/body-shop/experimental-v001/development-package-run/v2'
$PackageStatus = 'PASS__BODY_SHOP_DEVELOPMENT_PACKAGE_TWO_PROCESS_V002'
$ManifestSchema = 'cairnwell/body-shop/experimental-v001/package-manifest-validation/v2'
$ManifestStatus = 'PASS__BODY_SHOP_DEVELOPMENT_PACKAGE_MANIFEST_EXACT_CONTAINER_V002'
$RuntimeStatus = 'PASS__BODY_SHOP_PACKAGED_PERFORMANCE_LOD_VIEW_V002'
$GateStatus = 'PASS__BODY_SHOP_PACKAGED_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V002'
$RunStatus = 'PASS__BODY_SHOP_PACKAGED_PERFORMANCE_LOD_VALIDATION_RUN_V002'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$Token = [Guid]::NewGuid().ToString('N')
$RunRoot = Join-Path $Root "Saved\Audits\BodyShop\Experimental_v001\PackagedPerformanceLODValidation\$Stamp-$($Token.Substring(0,8))"
$Logs = Join-Path $RunRoot 'Logs'
$GateReceipt = Join-Path $RunRoot 'packaged_performance_lod_gate_v002.json'
$Summary = Join-Path $RunRoot 'packaged_performance_lod_validation_summary_v002.json'
$AnalysisStdout = Join-Path $Logs 'analyzer.stdout.log'
$AnalysisStderr = Join-Path $Logs 'analyzer.stderr.log'
$Analyzer = Join-Path $Root 'Scripts\analyze_body_shop_packaged_performance_lod_v002.py'
$SupportContractScript = Join-Path $Root 'Scripts\body_shop_support_kit_native_v002_contract.py'
$LegacyAnalyzer = Join-Path $Root 'Scripts\analyze_body_shop_performance_lod_v001.py'
$GameModeCpp = Join-Path $Root 'Source\LineBossCarFactory\LBBodyShopPrototypeGameMode.cpp'
$GameModeHeader = Join-Path $Root 'Source\LineBossCarFactory\LBBodyShopPrototypeGameMode.h'
$BridgeTests = Join-Path $Root 'Source\LineBossCarFactory\LBBodyShopPackagedPerformanceBridgeTests.cpp'
$BodyShopSourceRoot = Join-Path $Root 'Source\LineBossCarFactory'
$CurrentBodyShopSourceFiles = @()
$BodyMap = Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001\Maps\LB_BodyShop_Prototype_v001.umap'
$PressMap = Join-Path $Root 'Content\LineBoss\Maps\LB_PressShop_RebuildFromLorry_v20260810_v913.umap'
$RestoredPressMap = Join-Path $Root 'Content\LineBoss\Maps\LB_PressShop_FullFactoryRestored_v001.umap'
$ExpectedRestoredPressSha256 = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'
$ExpectedDefaultGameSha256 = '4458BB41EE3A56B67B8ECDD6954A46B23FD038A9CB8294E9A79C48580A86852B'
$PackageArtifactFiles = @()
$NativeSupportAssetFiles = @()

function Assert-NoActiveUnrealOrGameProcess {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $Names -contains $_.ProcessName -or $_.ProcessName -like 'LineBossCarFactory*'
    }
    if ($Active) {
        throw "Refusing packaged performance capture while Unreal/build/game processes are active: $($Active.ProcessName -join ', ')"
    }
}

function Resolve-ProjectPath([string]$Path,[string]$Label) {
    $Candidate = if ([IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $Root $Path }
    $Resolved = [IO.Path]::GetFullPath($Candidate)
    $RootFull = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar)
    $RootPrefix = $RootFull + [IO.Path]::DirectorySeparatorChar
    if (-not $Resolved.Equals($RootFull,[StringComparison]::OrdinalIgnoreCase) -and
        -not $Resolved.StartsWith($RootPrefix,[StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the project root: $Resolved"
    }
    return $Resolved
}

function Resolve-ProjectLeaf([string]$Path,[string]$Label) {
    $Resolved = Resolve-ProjectPath $Path $Label
    if (-not (Test-Path -LiteralPath $Resolved -PathType Leaf)) { throw "$Label missing: $Resolved" }
    return $Resolved
}

function Resolve-DeclaredAbsoluteRoot([string]$Path,[string]$Label) {
    if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathRooted($Path)) {
        throw "$Label must be an exact absolute path from the PASS package summary"
    }
    $Resolved = [IO.Path]::GetFullPath($Path).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar)
    $Declared = $Path.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar)
    if (-not $Resolved.Equals($Declared,[StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label is not a canonical absolute path: $Path"
    }
    if (-not (Test-Path -LiteralPath $Resolved -PathType Container)) {
        throw "$Label missing: $Resolved"
    }
    return $Resolved
}

function Resolve-ExactChildLeaf([string]$RootPath,[string]$RelativePath,[string]$Label) {
    $RootFull = [IO.Path]::GetFullPath($RootPath).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar)
    $Resolved = [IO.Path]::GetFullPath((Join-Path $RootFull $RelativePath))
    $RootPrefix = $RootFull + [IO.Path]::DirectorySeparatorChar
    if (-not $Resolved.StartsWith($RootPrefix,[StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes its declared package root: $Resolved"
    }
    if (-not (Test-Path -LiteralPath $Resolved -PathType Leaf)) {
        throw "$Label missing: $Resolved"
    }
    return $Resolved
}

function Assert-ExactHashRecord($Record,[string]$ExpectedPath,[string]$Label) {
    if ($null -eq $Record) { throw "$Label has no exact manifest hash record" }
    $RecordedPath = if ([string]::IsNullOrWhiteSpace([string]$Record.path)) { '' } else {
        [IO.Path]::GetFullPath([string]$Record.path)
    }
    if (-not $RecordedPath.Equals($ExpectedPath,[StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label manifest path drifted: $RecordedPath"
    }
    $Item = Get-Item -LiteralPath $ExpectedPath
    $ExpectedHash = [string]$Record.sha256
    if ($Item.Length -ne [int64]$Record.bytes -or
        $ExpectedHash -notmatch '^[0-9A-Fa-f]{64}$' -or
        (Get-FileHash -Algorithm SHA256 -LiteralPath $ExpectedPath).Hash -cne
            $ExpectedHash.ToUpperInvariant()) {
        throw "$Label length/hash drifted: $ExpectedPath"
    }
}

function Get-HashRecord([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [ordered]@{ path=$Path; exists=$false; bytes=$null; sha256=$null }
    }
    $Item = Get-Item -LiteralPath $Path
    return [ordered]@{
        path=$Item.FullName
        exists=$true
        bytes=$Item.Length
        sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $Item.FullName).Hash
    }
}

function Get-ProtectedSnapshot {
    $Files = @($PackageSummaryPath,$PackagedExecutable,$Analyzer,$LegacyAnalyzer,$PSCommandPath,
        $SupportContractScript,$GameModeCpp,$GameModeHeader,$BridgeTests,$BodyMap,$PressMap,
        $RestoredPressMap,$NativeRobotValidationPath,$NativeSupportValidationPath,
        (Join-Path $Root 'Config\DefaultGame.ini')) +
        $CurrentBodyShopSourceFiles + $NativeRobotAssetFiles + $NativeSupportAssetFiles +
        $PackageArtifactFiles
    $Files = @($Files | Sort-Object -Unique)
    return @($Files | ForEach-Object { Get-HashRecord $_ })
}

function Test-SnapshotEqual($Before,$After) {
    return (($Before | ConvertTo-Json -Depth 5 -Compress) -ceq
        ($After | ConvertTo-Json -Depth 5 -Compress))
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

function Quote-ProcessArgument([string]$Value) {
    if ($Value.Contains('"')) { throw "Process argument contains a forbidden quote: $Value" }
    return '"' + $Value + '"'
}

function Invoke-PackagedPerformanceView([ValidateSet('management','focus')][string]$View) {
    Assert-NoActiveUnrealOrGameProcess
    $ViewRoot = Join-Path $RunRoot $View
    $UserDir = Join-Path $ViewRoot 'UserDir'
    $Stdout = Join-Path $Logs "$View.stdout.log"
    $Stderr = Join-Path $Logs "$View.stderr.log"
    $EngineLog = Join-Path $Logs "$View.engine.log"
    New-Item -ItemType Directory -Path $UserDir -Force | Out-Null
    foreach ($Path in @($Stdout,$Stderr,$EngineLog)) {
        if (Test-Path -LiteralPath $Path) { throw "Fresh $View log path already exists: $Path" }
    }

    $ViewArgument = if ($View -eq 'management') { 'Management' } else { 'Focus' }
    $Arguments = @(
        $MapPackage,
        "-LineBossBodyShopPerformanceValidation=$ViewArgument",
        "-LineBossBodyShopValidationToken=$Token",
        "-UserDir=`"$UserDir`"",
        "-AbsLog=`"$EngineLog`"",
        '-windowed',
        '-ResX=1920',
        '-ResY=1080',
        '-ForceRes',
        '-csvGpuStats',
        '-csvCompression=0',
        '-NoHardwareBenchmark',
        '-nosound',
        '-unattended',
        '-nosplash',
        '-stdout',
        '-FullStdOutLogOutput'
    )
    if ($Arguments -contains '-nullrhi') { throw 'NullRHI is forbidden in packaged performance capture' }
    $StartedUtc = (Get-Date).ToUniversalTime()
    $Process = Start-Process -FilePath $PackagedExecutable -ArgumentList $Arguments `
        -WorkingDirectory $PackagedWorkingDirectory -PassThru -WindowStyle Normal `
        -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr
    # Windows PowerShell 5.1 can leave ExitCode null after redirected
    # Start-Process unless the native process handle is materialized first.
    $null = $Process.Handle
    $TimedOut = -not $Process.WaitForExit($PerViewTimeoutSeconds * 1000)
    if ($TimedOut) {
        $Process.Kill()
        $Process.WaitForExit()
    } else {
        $Process.WaitForExit()
    }
    $FinishedUtc = (Get-Date).ToUniversalTime()
    if ($TimedOut) { throw "Packaged $View performance process exceeded $PerViewTimeoutSeconds seconds" }
    $ExitCode = $Process.ExitCode
    if ($null -eq $ExitCode) { throw "Packaged $View performance process did not expose an exit code" }
    if ($ExitCode -ne 0) { throw "Packaged $View performance process failed with exit $ExitCode" }
    if (-not (Test-Path -LiteralPath $EngineLog -PathType Leaf)) {
        throw "Packaged $View engine log is missing: $EngineLog"
    }
    $AllText = Get-ExactLogText @($EngineLog,$Stdout,$Stderr)
    if ($AllText -match 'Fatal error|Unhandled Exception|Assertion failed|Ensure condition failed') {
        throw "Packaged $View logs contain a fatal/assert/ensure"
    }

    $ReceiptLeaf = "${View}_runtime_capture_v002.json"
    $Receipts = @(Get-ChildItem -LiteralPath $UserDir -Recurse -File -Filter $ReceiptLeaf -ErrorAction SilentlyContinue)
    if ($Receipts.Count -ne 1) {
        throw "Packaged $View must emit exactly one runtime receipt; found $($Receipts.Count)"
    }
    $Receipt = $Receipts[0].FullName
    $Runtime = Get-Content -Raw -LiteralPath $Receipt | ConvertFrom-Json
    if ([string]$Runtime.status -cne $RuntimeStatus -or [string]$Runtime.view -cne $View -or
        [string]$Runtime.token -cne $Token -or [string]$Runtime.map -cne $MapPackage) {
        throw "Packaged $View runtime receipt identity drifted"
    }
    if ([string]$Runtime.capture_contract.renderer_lod_selection_source -cne
            'FPrimitiveSceneProxy::GetLOD(FSceneView)' -or
        [string]$Runtime.renderer_lod_snapshot.thread -cne 'game_thread' -or
        [string]$Runtime.renderer_lod_snapshot.phase -cne 'after_120_warmup_frames_before_csv' -or
        [bool]$Runtime.capture_contract.primitive_debug_dump_used -ne $false -or
        [int]$Runtime.renderer_lod_snapshot.component_count -ne 25 -or
        [int]$Runtime.renderer_lod_snapshot.unique_mesh_count -ne 10 -or
        [int]$Runtime.renderer_lod_snapshot.global_forced_lod -ne -1 -or
        @($Runtime.target_components).Count -ne 25 -or
        $null -ne $Runtime.PSObject.Properties['primitive_csv_candidates']) {
        throw "Packaged $View renderer LOD snapshot contract drifted"
    }
    return [ordered]@{
        view=$View
        started_utc=$StartedUtc.ToString('o')
        finished_utc=$FinishedUtc.ToString('o')
        exit_code=$ExitCode
        command=$PackagedExecutable
        command_args=$Arguments
        user_dir=$UserDir
        runtime_receipt=$Receipt
        runtime_receipt_record=Get-HashRecord $Receipt
        stdout=Get-HashRecord $Stdout
        stderr=Get-HashRecord $Stderr
        engine_log=Get-HashRecord $EngineLog
    }
}

foreach ($Required in @($Analyzer,$LegacyAnalyzer,$SupportContractScript,$GameModeCpp,$GameModeHeader,$BridgeTests,$BodyMap,$PressMap,$RestoredPressMap)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) { throw "Required file missing: $Required" }
}
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $RestoredPressMap).Hash -cne $ExpectedRestoredPressSha256) {
    throw "Full restored Press map hash drifted: $RestoredPressMap"
}
if ((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Root 'Config\DefaultGame.ini')).Hash -cne $ExpectedDefaultGameSha256) {
    throw 'DefaultGame.ini native cook-root authority drifted'
}
$CurrentBodyShopSourceFiles = @(Get-ChildItem -LiteralPath $BodyShopSourceRoot -File |
    Where-Object { $_.Name -like 'LBBodyShop*.h' -or $_.Name -like 'LBBodyShop*.cpp' } |
    Sort-Object FullName | ForEach-Object { $_.FullName })
if ($CurrentBodyShopSourceFiles.Count -eq 0) { throw 'Current Body Shop source set is empty' }
$PackageSummaryPath = Resolve-ProjectLeaf $DevelopmentPackageSummary 'Development package summary'
$PackageSummaryHashAtLoad = (Get-FileHash -Algorithm SHA256 `
    -LiteralPath $PackageSummaryPath).Hash
$Package = Get-Content -Raw -LiteralPath $PackageSummaryPath | ConvertFrom-Json
if ([string]$Package.schema -cne $PackageSchema -or [string]$Package.status -cne $PackageStatus -or
    [string]$Package.configuration -cne 'Development' -or [bool]$Package.shipping_requested -ne $false -or
    [string]$Package.explicit_map -cne $MapPackage -or [bool]$Package.protected_unchanged -ne $true) {
    throw "Development package is not the exact current PASS contract: schema=$($Package.schema) status=$($Package.status)"
}
foreach ($EvidenceContract in @(
    [pscustomobject]@{ Path=[string]$Package.build_receipt; Hash=[string]$Package.build_receipt_sha256; Label='BuildCookRun receipt' },
    [pscustomobject]@{ Path=[string]$Package.manifest_receipt; Hash=[string]$Package.manifest_receipt_sha256; Label='package manifest receipt' },
    [pscustomobject]@{ Path=[string]$Package.container_listing_receipt; Hash=[string]$Package.container_listing_receipt_sha256; Label='container listing receipt' },
    [pscustomobject]@{ Path=[string]$Package.native_robot_fresh_load_validation_receipt; Hash=[string]$Package.native_robot_fresh_load_validation_receipt_sha256; Label='native six-axis robot fresh-load receipt' },
    [pscustomobject]@{ Path=[string]$Package.native_support_kit_v002_fresh_load_validation_receipt; Hash=[string]$Package.native_support_kit_v002_fresh_load_validation_receipt_sha256; Label='native support-kit v002 fresh-load receipt' }
)) {
    $EvidencePath = Resolve-ProjectLeaf $EvidenceContract.Path $EvidenceContract.Label
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $EvidencePath).Hash -cne $EvidenceContract.Hash) {
        throw "$($EvidenceContract.Label) hash drifted: $EvidencePath"
    }
}
$NativeRobotValidationPath = Resolve-ProjectLeaf `
    ([string]$Package.native_robot_fresh_load_validation_receipt) `
    'native six-axis robot fresh-load receipt'
$ExpectedNativeRunRoot = Join-Path $Root 'Saved\Audits\BodyShop\RobotNative_v001\UnrealImportLane\20260814T204134Z-19e41ca7'
$ExpectedNativeLaneSummary = Join-Path $ExpectedNativeRunRoot 'lane_summary_v001.json'
$ExpectedNativeImportReceipt = Join-Path $ExpectedNativeRunRoot 'import_receipt_v001.json'
$ExpectedNativeValidationReceipt = Join-Path $ExpectedNativeRunRoot 'fresh_load_validation_receipt_v001.json'
$ExpectedNativeLaneSummarySha256 = 'B1AFEDB019C28B04082497F46B954C29262D0A30B19854D00CF1168537AA2F73'
$ExpectedNativeImportReceiptSha256 = 'B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF'
$ExpectedNativeValidationReceiptSha256 = '9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA'
if ($NativeRobotValidationPath -cne [IO.Path]::GetFullPath($ExpectedNativeValidationReceipt) -or
        [string]$Package.native_robot_fresh_load_validation_receipt_sha256 -cne $ExpectedNativeValidationReceiptSha256 -or
        (Get-FileHash -Algorithm SHA256 -LiteralPath $NativeRobotValidationPath).Hash -cne $ExpectedNativeValidationReceiptSha256 -or
        (Get-FileHash -Algorithm SHA256 -LiteralPath (Resolve-ProjectLeaf $ExpectedNativeLaneSummary 'Native robot lane summary')).Hash -cne $ExpectedNativeLaneSummarySha256 -or
        (Get-FileHash -Algorithm SHA256 -LiteralPath (Resolve-ProjectLeaf $ExpectedNativeImportReceipt 'Native robot import receipt')).Hash -cne $ExpectedNativeImportReceiptSha256) {
    throw 'Development package does not bind the exact final 204134 native robot evidence chain'
}
$NativeSupportValidationPath = Resolve-ProjectLeaf `
    ([string]$Package.native_support_kit_v002_fresh_load_validation_receipt) `
    'native support-kit v002 fresh-load receipt'
$Python = (Get-Command python -ErrorAction Stop).Source
$SupportContractText = (& $Python $SupportContractScript --project-root $Root `
    --validation-receipt $NativeSupportValidationPath 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) { throw "Native support-kit v002 contract failed: $SupportContractText" }
$SupportContract = $SupportContractText | ConvertFrom-Json
if ([int]$SupportContract.asset_count -ne 12 `
        -or [int]$SupportContract.lod_count_per_asset -ne 3 `
        -or (@($SupportContract.lod_triangle_totals) -join ',') -cne '20408,7580,1780' `
        -or @($SupportContract.packages.psobject.Properties).Count -ne 12) {
    throw 'Development package native support-kit v002 authority drifted'
}
$NativeRobotAssetFiles = @(Get-ChildItem -LiteralPath `
    (Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopRobotNative_v001') `
    -Recurse -File -Filter '*.uasset' -ErrorAction Stop | Sort-Object FullName |
    ForEach-Object { $_.FullName })
if ($NativeRobotAssetFiles.Count -ne 8) {
    throw "Native robot namespace must contain exactly 8 uassets, found $($NativeRobotAssetFiles.Count)"
}
$NativeSupportAssetFiles = @(Get-ChildItem -LiteralPath `
    (Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopSupportKitNative_v002') `
    -Recurse -File -Filter '*.uasset' -ErrorAction Stop | Sort-Object FullName |
    ForEach-Object { $_.FullName })
if ($NativeSupportAssetFiles.Count -ne 12) {
    throw "Native support-kit namespace must contain exactly 12 uassets, found $($NativeSupportAssetFiles.Count)"
}
if ([string]$Package.protected_before.body_shop_game_mode_cpp -cne
        (Get-FileHash -Algorithm SHA256 -LiteralPath $GameModeCpp).Hash -or
    [string]$Package.protected_before.body_shop_game_mode_h -cne
        (Get-FileHash -Algorithm SHA256 -LiteralPath $GameModeHeader).Hash -or
    [string]$Package.protected_after.body_shop_game_mode_cpp -cne
        (Get-FileHash -Algorithm SHA256 -LiteralPath $GameModeCpp).Hash -or
    [string]$Package.protected_after.body_shop_game_mode_h -cne
        (Get-FileHash -Algorithm SHA256 -LiteralPath $GameModeHeader).Hash) {
    throw 'Development package summary does not bind the current packaged-performance native bridge source'
}
if ([string]$Package.protected_before.press_full_factory_restored_v001 -cne $ExpectedRestoredPressSha256 -or
        [string]$Package.protected_after.press_full_factory_restored_v001 -cne $ExpectedRestoredPressSha256) {
    throw 'Development package summary does not protect the exact full restored Press map'
}
$BeforeSourceContracts = @($Package.protected_before.all_body_shop_source)
$AfterSourceContracts = @($Package.protected_after.all_body_shop_source)
if ($BeforeSourceContracts.Count -ne $CurrentBodyShopSourceFiles.Count -or
    $AfterSourceContracts.Count -ne $CurrentBodyShopSourceFiles.Count) {
    throw "Development package Body Shop source cardinality drifted: before=$($BeforeSourceContracts.Count) after=$($AfterSourceContracts.Count) current=$($CurrentBodyShopSourceFiles.Count)"
}
for ($Index = 0; $Index -lt $CurrentBodyShopSourceFiles.Count; ++$Index) {
    $ExpectedPath = [IO.Path]::GetFullPath($CurrentBodyShopSourceFiles[$Index])
    $BeforePath = Resolve-ProjectLeaf ([string]$BeforeSourceContracts[$Index].path) 'Packaged pre-build Body Shop source'
    $AfterPath = Resolve-ProjectLeaf ([string]$AfterSourceContracts[$Index].path) 'Packaged post-build Body Shop source'
    $CurrentHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ExpectedPath).Hash
    if (-not $BeforePath.Equals($ExpectedPath,[StringComparison]::OrdinalIgnoreCase) -or
        -not $AfterPath.Equals($ExpectedPath,[StringComparison]::OrdinalIgnoreCase) -or
        [string]$BeforeSourceContracts[$Index].sha256 -cne $CurrentHash -or
        [string]$AfterSourceContracts[$Index].sha256 -cne $CurrentHash) {
        throw "Development package does not bind the exact current Body Shop source set: $ExpectedPath"
    }
}
$BeforeNativeContracts = @($Package.protected_before.native_robot_assets)
$AfterNativeContracts = @($Package.protected_after.native_robot_assets)
if ($BeforeNativeContracts.Count -ne $NativeRobotAssetFiles.Count -or
        $AfterNativeContracts.Count -ne $NativeRobotAssetFiles.Count) {
    throw 'Development package native robot asset cardinality drifted'
}
for ($Index = 0; $Index -lt $NativeRobotAssetFiles.Count; ++$Index) {
    $ExpectedPath = [IO.Path]::GetFullPath($NativeRobotAssetFiles[$Index])
    $BeforePath = Resolve-ProjectLeaf ([string]$BeforeNativeContracts[$Index].path) `
        'Packaged pre-build native robot asset'
    $AfterPath = Resolve-ProjectLeaf ([string]$AfterNativeContracts[$Index].path) `
        'Packaged post-build native robot asset'
    $CurrentHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ExpectedPath).Hash
    if (-not $BeforePath.Equals($ExpectedPath,[StringComparison]::OrdinalIgnoreCase) -or
            -not $AfterPath.Equals($ExpectedPath,[StringComparison]::OrdinalIgnoreCase) -or
            [string]$BeforeNativeContracts[$Index].sha256 -cne $CurrentHash -or
            [string]$AfterNativeContracts[$Index].sha256 -cne $CurrentHash) {
        throw "Development package does not bind the exact native robot asset set: $ExpectedPath"
    }
}
$BeforeSupportContracts = @($Package.protected_before.native_support_kit_v002_assets)
$AfterSupportContracts = @($Package.protected_after.native_support_kit_v002_assets)
if ($BeforeSupportContracts.Count -ne 12 -or $AfterSupportContracts.Count -ne 12) {
    throw 'Development package native support-kit asset cardinality drifted'
}
for ($Index = 0; $Index -lt $NativeSupportAssetFiles.Count; ++$Index) {
    $ExpectedPath = [IO.Path]::GetFullPath($NativeSupportAssetFiles[$Index])
    $BeforePath = Resolve-ProjectLeaf ([string]$BeforeSupportContracts[$Index].path) `
        'Packaged pre-build native support-kit asset'
    $AfterPath = Resolve-ProjectLeaf ([string]$AfterSupportContracts[$Index].path) `
        'Packaged post-build native support-kit asset'
    $CurrentHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ExpectedPath).Hash
    if (-not $BeforePath.Equals($ExpectedPath,[StringComparison]::OrdinalIgnoreCase) -or
            -not $AfterPath.Equals($ExpectedPath,[StringComparison]::OrdinalIgnoreCase) -or
            [string]$BeforeSupportContracts[$Index].sha256 -cne $CurrentHash -or
            [string]$AfterSupportContracts[$Index].sha256 -cne $CurrentHash) {
        throw "Development package does not bind the exact native support-kit asset set: $ExpectedPath"
    }
}
$ManifestReceiptPath = Resolve-ProjectLeaf ([string]$Package.manifest_receipt) `
    'package manifest receipt'
$Manifest = Get-Content -Raw -LiteralPath $ManifestReceiptPath | ConvertFrom-Json
if ([string]$Manifest.'$schema' -cne $ManifestSchema -or
    [string]$Manifest.status -cne $ManifestStatus -or
    @($Manifest.failures).Count -ne 0 -or
    [string]$Manifest.native_six_axis_robot.validation_receipt.sha256 -cne $ExpectedNativeValidationReceiptSha256 -or
    [string]$Manifest.native_six_axis_robot.import_receipt.sha256 -cne $ExpectedNativeImportReceiptSha256 -or
    [string]$Manifest.native_six_axis_robot.lane_summary.sha256 -cne $ExpectedNativeLaneSummarySha256 -or
    (@($Manifest.native_six_axis_robot.lod_triangle_totals) -join ',') -cne '2628,1964,1356' -or
    [string]$Manifest.native_support_kit_v002.validation_receipt.sha256 -cne `
        [string]$SupportContract.validation_receipt.sha256 -or
    (@($Manifest.native_support_kit_v002.lod_triangle_totals) -join ',') -cne '20408,7580,1780' -or
    [int]$Manifest.native_support_kit_v002.asset_count -ne 12 -or
    @($Manifest.native_support_kit_v002.packages.psobject.Properties).Count -ne 12 -or
    -not ([IO.Path]::GetFullPath([string]$Manifest.project_root)).Equals(
        [IO.Path]::GetFullPath($Root),[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Hash-bound package manifest is not the exact PASS project contract'
}

# Stage/archive are deliberately allowed outside the project root, but only when
# both exact absolute roots are bound by the already hash-verified PASS summary
# and its exact manifest receipt.
$Archive = Resolve-DeclaredAbsoluteRoot ([string]$Package.archive) 'Development archive'
$Stage = Resolve-DeclaredAbsoluteRoot ([string]$Package.stage) 'Development stage'
$ManifestArchive = Resolve-DeclaredAbsoluteRoot ([string]$Manifest.archive_root) `
    'Manifest Development archive'
$ManifestStage = Resolve-DeclaredAbsoluteRoot ([string]$Manifest.stage_root) `
    'Manifest Development stage'
if (-not $Archive.Equals($ManifestArchive,[StringComparison]::OrdinalIgnoreCase) -or
    -not $Stage.Equals($ManifestStage,[StringComparison]::OrdinalIgnoreCase)) {
    throw 'PASS package summary and manifest do not bind the same stage/archive roots'
}

$PackagedWorkingDirectory = Join-Path $Archive 'Windows'
$PackagedExecutable = Resolve-ExactChildLeaf $Archive `
    'Windows\LineBossCarFactory\Binaries\Win64\LineBossCarFactory.exe' `
    'Exact archived Development executable'
$StageExecutable = Resolve-ExactChildLeaf $Stage `
    'Windows\LineBossCarFactory\Binaries\Win64\LineBossCarFactory.exe' `
    'Exact staged Development executable'
$ArchiveExecutableMatches = @($Manifest.archive_executables | Where-Object {
    ([IO.Path]::GetFullPath([string]$_.path)).Equals(
        $PackagedExecutable,[StringComparison]::OrdinalIgnoreCase)
})
$StageExecutableMatches = @($Manifest.stage_executables | Where-Object {
    ([IO.Path]::GetFullPath([string]$_.path)).Equals(
        $StageExecutable,[StringComparison]::OrdinalIgnoreCase)
})
if ($ArchiveExecutableMatches.Count -ne 1 -or $StageExecutableMatches.Count -ne 1) {
    throw 'PASS package manifest does not contain one exact inner Development executable per root'
}
Assert-ExactHashRecord $ArchiveExecutableMatches[0] $PackagedExecutable `
    'Archived Development executable'
Assert-ExactHashRecord $StageExecutableMatches[0] $StageExecutable `
    'Staged Development executable'
if ([string]$ArchiveExecutableMatches[0].sha256 -cne
        [string]$StageExecutableMatches[0].sha256) {
    throw 'Stage/archive Development executable hashes differ'
}

$ContainerRelativeRoot = 'Windows\LineBossCarFactory\Content\Paks'
$ArchiveUtoc = Resolve-ExactChildLeaf $Archive `
    "$ContainerRelativeRoot\LineBossCarFactory-Windows.utoc" 'Archived IoStore UTOC'
$ArchiveUcas = Resolve-ExactChildLeaf $Archive `
    "$ContainerRelativeRoot\LineBossCarFactory-Windows.ucas" 'Archived IoStore UCAS'
$StageUtoc = Resolve-ExactChildLeaf $Stage `
    "$ContainerRelativeRoot\LineBossCarFactory-Windows.utoc" 'Staged IoStore UTOC'
$StageUcas = Resolve-ExactChildLeaf $Stage `
    "$ContainerRelativeRoot\LineBossCarFactory-Windows.ucas" 'Staged IoStore UCAS'
$ArchiveContainerMatches = @($Manifest.archive_containers | Where-Object {
    ([IO.Path]::GetFullPath([string]$_.utoc)).Equals(
        $ArchiveUtoc,[StringComparison]::OrdinalIgnoreCase) -and
    ([IO.Path]::GetFullPath([string]$_.ucas)).Equals(
        $ArchiveUcas,[StringComparison]::OrdinalIgnoreCase)
})
$StageContainerMatches = @($Manifest.stage_containers | Where-Object {
    ([IO.Path]::GetFullPath([string]$_.utoc)).Equals(
        $StageUtoc,[StringComparison]::OrdinalIgnoreCase) -and
    ([IO.Path]::GetFullPath([string]$_.ucas)).Equals(
        $StageUcas,[StringComparison]::OrdinalIgnoreCase)
})
if ($ArchiveContainerMatches.Count -ne 1 -or $StageContainerMatches.Count -ne 1) {
    throw 'PASS package manifest does not contain one exact project IoStore pair per root'
}
$ArchiveContainer = $ArchiveContainerMatches[0]
$StageContainer = $StageContainerMatches[0]
Assert-ExactHashRecord ([pscustomobject]@{ path=$ArchiveContainer.utoc; bytes=$ArchiveContainer.utoc_bytes; sha256=$ArchiveContainer.utoc_sha256 }) `
    $ArchiveUtoc 'Archived IoStore UTOC'
Assert-ExactHashRecord ([pscustomobject]@{ path=$ArchiveContainer.ucas; bytes=$ArchiveContainer.ucas_bytes; sha256=$ArchiveContainer.ucas_sha256 }) `
    $ArchiveUcas 'Archived IoStore UCAS'
Assert-ExactHashRecord ([pscustomobject]@{ path=$StageContainer.utoc; bytes=$StageContainer.utoc_bytes; sha256=$StageContainer.utoc_sha256 }) `
    $StageUtoc 'Staged IoStore UTOC'
Assert-ExactHashRecord ([pscustomobject]@{ path=$StageContainer.ucas; bytes=$StageContainer.ucas_bytes; sha256=$StageContainer.ucas_sha256 }) `
    $StageUcas 'Staged IoStore UCAS'
if ([string]$ArchiveContainer.utoc_sha256 -cne [string]$StageContainer.utoc_sha256 -or
    [string]$ArchiveContainer.ucas_sha256 -cne [string]$StageContainer.ucas_sha256) {
    throw 'Stage/archive IoStore container hashes differ'
}
$PackageArtifactFiles = @(
    $PackageSummaryPath,$ManifestReceiptPath,$PackagedExecutable,$ArchiveUtoc,$ArchiveUcas
)
$Python = (Get-Command python -ErrorAction Stop).Source
Assert-NoActiveUnrealOrGameProcess
if (Test-Path -LiteralPath $RunRoot) { throw "Fresh packaged performance run path already exists: $RunRoot" }
New-Item -ItemType Directory -Path $Logs -Force | Out-Null
$Before = Get-ProtectedSnapshot
$Failure = $null
$Management = $null
$Focus = $null
$AnalysisExit = $null
$Gate = $null
$ProtectedUnchanged = $false

try {
    $Management = Invoke-PackagedPerformanceView 'management'
    $Focus = Invoke-PackagedPerformanceView 'focus'
    Assert-NoActiveUnrealOrGameProcess
    $AnalyzerArguments = @(
        (Quote-ProcessArgument $Analyzer),
        '--package-summary', (Quote-ProcessArgument $PackageSummaryPath),
        '--executable', (Quote-ProcessArgument $PackagedExecutable),
        '--management-receipt', (Quote-ProcessArgument ([string]$Management.runtime_receipt)),
        '--focus-receipt', (Quote-ProcessArgument ([string]$Focus.runtime_receipt)),
        '--management-log', (Quote-ProcessArgument ([string]$Management.engine_log.path)),
        '--focus-log', (Quote-ProcessArgument ([string]$Focus.engine_log.path)),
        '--run-root', (Quote-ProcessArgument $RunRoot),
        '--output', (Quote-ProcessArgument $GateReceipt)
    )
    $AnalyzerProcess = Start-Process -FilePath $Python -ArgumentList $AnalyzerArguments `
        -WorkingDirectory $Root -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $AnalysisStdout -RedirectStandardError $AnalysisStderr
    $null = $AnalyzerProcess.Handle
    $AnalyzerProcess.WaitForExit()
    $AnalyzerProcess.WaitForExit()
    $AnalysisExit = $AnalyzerProcess.ExitCode
    if ($null -eq $AnalysisExit) {
        throw 'Packaged performance analyzer process did not expose an exit code'
    }
    if (-not (Test-Path -LiteralPath $GateReceipt -PathType Leaf)) {
        throw "Packaged performance analyzer did not emit its gate receipt: $GateReceipt"
    }
    $Gate = Get-Content -Raw -LiteralPath $GateReceipt | ConvertFrom-Json
    if ($AnalysisExit -ne 0 -or [string]$Gate.status -cne $GateStatus) {
        throw "Packaged performance numeric/LOD gate failed (exit=$AnalysisExit status=$($Gate.status))"
    }
}
catch {
    $Failure = $_.Exception.Message
}

$After = Get-ProtectedSnapshot
$ProtectedUnchanged = Test-SnapshotEqual $Before $After
if (-not $ProtectedUnchanged -and -not $Failure) {
    $Failure = 'Package, executable, performance scripts/source, or protected maps changed during capture'
}
$Status = if (-not $Failure -and $ProtectedUnchanged -and $Gate -and
    [string]$Gate.status -ceq $GateStatus) { $RunStatus } else {
    'FAIL__BODY_SHOP_PACKAGED_PERFORMANCE_LOD_VALIDATION_RUN_V002'
}

[ordered]@{
    schema='cairnwell/body-shop/experimental-v001/packaged-performance-lod-validation-run/v2'
    generated_utc=(Get-Date).ToUniversalTime().ToString('o')
    status=$Status
    stamp=$Stamp
    token=$Token
    failure=$Failure
    package_summary=Get-HashRecord $PackageSummaryPath
    package_summary_sha256_at_load=$PackageSummaryHashAtLoad
    packaged_executable=Get-HashRecord $PackagedExecutable
    package_roots=[ordered]@{ archive=$Archive; stage=$Stage }
    manifest_bound_package_artifacts=[ordered]@{
        archive_executable_sha256=[string]$ArchiveExecutableMatches[0].sha256
        stage_executable_sha256=[string]$StageExecutableMatches[0].sha256
        archive_utoc_sha256=[string]$ArchiveContainer.utoc_sha256
        archive_ucas_sha256=[string]$ArchiveContainer.ucas_sha256
        stage_utoc_sha256=[string]$StageContainer.utoc_sha256
        stage_ucas_sha256=[string]$StageContainer.ucas_sha256
    }
    package_manifest_sha256=[string]$Package.manifest_receipt_sha256
    container_listing_receipt_sha256=[string]$Package.container_listing_receipt_sha256
    final_native_robot_authority=[ordered]@{
        lane_summary=Get-HashRecord $ExpectedNativeLaneSummary
        import_receipt=Get-HashRecord $ExpectedNativeImportReceipt
        validation_receipt=Get-HashRecord $ExpectedNativeValidationReceipt
        lod_triangle_totals=@(2628,1964,1356)
        runtime_target_components=25
        runtime_unique_meshes=10
    }
    final_native_support_kit_v002_authority=$SupportContract
    command_contract=[ordered]@{
        configuration='Development'
        shipping_requested=$false
        exact_map=$MapPackage
        views=@('management','focus')
        per_view_csv_frames=300
        resolution=@(1920,1080)
        force_res=$true
        real_rhi=$true
        null_rhi=$false
        csv_gpu_stats=$true
        renderer_lod_snapshot='game_thread_FPrimitiveSceneProxy_GetLOD'
        core_renderer_manifest_components=25
        core_renderer_manifest_unique_meshes=10
        native_service_props_in_scene_totals=$true
        primitive_debug_dump=$false
        build_ubt_or_package_launched=$false
    }
    management=$Management
    focus=$Focus
    analyzer_exit_code=$AnalysisExit
    analyzer_stdout=Get-HashRecord $AnalysisStdout
    analyzer_stderr=Get-HashRecord $AnalysisStderr
    gate_receipt=Get-HashRecord $GateReceipt
    scripts_and_native_bridge=@(
        (Get-HashRecord $PSCommandPath),
        (Get-HashRecord $Analyzer),
        (Get-HashRecord $LegacyAnalyzer),
        (Get-HashRecord $GameModeCpp),
        (Get-HashRecord $GameModeHeader),
        (Get-HashRecord $BridgeTests)
    )
    protected_snapshot_unchanged=$ProtectedUnchanged
    protected_before=$Before
    protected_after=$After
} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Summary -Encoding utf8

if ($Failure) { throw $Failure }
Write-Output $Summary
