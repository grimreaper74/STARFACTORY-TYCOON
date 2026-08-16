[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Python = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Script = Join-Path $Root 'Scripts\validate_body_shop_functional_hism_usage_v001.py'
$Log = Join-Path $Root 'Saved\Audits\BodyShop\Experimental_v001\Logs\validate_body_shop_functional_hism_usage_v004.log'
$UeReceipt = Join-Path $Root 'Saved\Audits\BodyShop\Experimental_v001\presentation_materials_v002_functional_hism_usage_validation_v004.json'
$Summary = Join-Path $Root 'Saved\Audits\BodyShop\Experimental_v001\presentation_materials_v002_functional_hism_usage_validation_summary_v004.json'
$SupportContractScript = Join-Path $Root 'Scripts\body_shop_support_kit_native_v002_contract.py'
$ExpectedSupportRunRoot = Join-Path $Root 'Saved\Audits\BodyShop\SupportKitNative_v002\UnrealImportLane_v003\20260814T223952Z-fa3434b0'
$ExpectedSupportValidationReceipt = Join-Path $ExpectedSupportRunRoot 'fresh_load_validation_receipt_v003.json'
$ExpectedSupportValidationReceiptSha256 = 'CDFA05DF4425695F8B6ABC8A06B17F377F6840739E207978E2595FA5A7B3DE82'
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
$ExpectedRestoredPressSha256 = 'D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5'

function Assert-NoActiveUnrealProcess {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -ne 0) {
        throw "Refusing validation while Unreal/build processes are active: $($Active.ProcessName -join ', ')"
    }
}

function Get-TreeSnapshot([string]$Directory) {
    $Rows = @()
    foreach ($File in Get-ChildItem -LiteralPath $Directory -Recurse -File | Sort-Object FullName) {
        $Rows += [ordered]@{
            path = $File.FullName.Substring($Root.Length).TrimStart('\').Replace('\','/')
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $File.FullName).Hash
        }
    }
    return $Rows
}

function Get-TextSha256([string]$Value) {
    $Sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return ([BitConverter]::ToString($Sha.ComputeHash($Bytes))).Replace('-','')
    }
    finally {
        $Sha.Dispose()
    }
}

Assert-NoActiveUnrealProcess
if (-not (Test-Path -LiteralPath $SupportContractScript -PathType Leaf)) {
    throw "Native support-kit contract validator missing: $SupportContractScript"
}
$SupportContractText = (& $Python $SupportContractScript --project-root $Root `
    --validation-receipt $ExpectedSupportValidationReceipt 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) { throw "Native support-kit v002 contract failed: $SupportContractText" }
$SupportContract = $SupportContractText | ConvertFrom-Json
if ([int]$SupportContract.asset_count -ne 12 `
        -or [int]$SupportContract.lod_count_per_asset -ne 3 `
        -or (@($SupportContract.lod_triangle_totals) -join ',') -cne '20408,7580,1780' `
        -or [string]$SupportContract.validation_receipt.sha256 -cne $ExpectedSupportValidationReceiptSha256 `
        -or @($SupportContract.packages.psobject.Properties).Count -ne 12) {
    throw 'Native support-kit v002 exact package/LOD authority drifted'
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
foreach ($Path in @($Log,$UeReceipt,$Summary)) {
    if (Test-Path -LiteralPath $Path) { throw "Refusing to overwrite validation output: $Path" }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Log) | Out-Null

$SourceBefore = @(Get-TreeSnapshot (Join-Path $Root 'Source'))
$ConfigBefore = @(Get-TreeSnapshot (Join-Path $Root 'Config'))
$ProjectArg = $Project.Replace('\','/')
$ScriptArg = $Script.Replace('\','/')
$LogArg = $Log.Replace('\','/')

& $Editor $ProjectArg "-ExecutePythonScript=$ScriptArg" -unattended -nop4 -nosplash -windowed -ResX=800 -ResY=600 -NoSound `
    -stdout -FullStdOutLogOutput "-abslog=$LogArg"
$EditorExitCode = $LASTEXITCODE

if ($EditorExitCode -ne 0) { throw "UE validation exited $EditorExitCode; log=$Log" }
if (-not (Test-Path -LiteralPath $UeReceipt -PathType Leaf)) { throw "UE validation receipt missing: $UeReceipt" }
$PythonErrors = @(Select-String -LiteralPath $Log -Pattern 'LogPython: Error|Python script executed with errors')
$PassMarkers = @(Select-String -LiteralPath $Log -SimpleMatch 'LINE_BOSS_BODYSHOP_FUNCTIONAL_HISM_USAGE_VALIDATION_V004_PASS')
if ($PythonErrors.Count -ne 0 -or $PassMarkers.Count -ne 1) {
    throw "UE validation log gate failed: python_errors=$($PythonErrors.Count) pass_markers=$($PassMarkers.Count)"
}
$UePayload = Get-Content -Raw -LiteralPath $UeReceipt | ConvertFrom-Json
if ([string]$UePayload.'$schema' -cne 'lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-v004/v1' `
        -or [string]$UePayload.status -cne 'PASS__FRESH_PROCESS_LIVE_PIE_BODYSHOP_FUNCTIONAL_HISM_NATIVE_ROBOT_SUPPORT_KIT_PROTECTION_V004') {
    throw "UE validation receipt is not the exact PASS status: $($UePayload.status)"
}
if ([int]$UePayload.live_pie.conveyor_cell_count -ne 4 `
    -or [int]$UePayload.live_pie.exercised_conveyor_hism_component_count -ne 12 `
    -or [int]$UePayload.live_pie.floor_cell_count -ne 1 `
        -or [int]$UePayload.live_pie.exercised_floor_hism_component_count -ne 2 `
        -or [int]$UePayload.live_pie.service_dressing_actor_count -ne 1 `
        -or [int]$UePayload.live_pie.service_hism_batch_count -ne 3 `
        -or [int]$UePayload.live_pie.service_hism_instance_count -ne 12 `
        -or (@($UePayload.live_pie.service_hism_components | ForEach-Object { [int]$_.instance_count } | Sort-Object) -join ',') -cne '3,3,6') {
    throw 'UE validation receipt does not prove 12 conveyor, 2 floor and native service 6/3/3 HISM batches'
}
$ServiceActor = $UePayload.live_pie.service_dressing_actor
$ServiceTags = @($ServiceActor.tags)
if ([string]$ServiceActor.name -cne 'LB_BodyShop_ServiceDressing_v002' `
        -or -not [bool]$ServiceActor.active `
        -or -not [bool]$ServiceActor.valid_contract `
        -or [bool]$ServiceActor.represents_process_wip `
        -or $ServiceTags -cnotcontains 'LB.BodyShop.ServiceDressing.v002' `
        -or $ServiceTags -cnotcontains 'LB.Asset.CleanRoomNative.v002' `
        -or $ServiceTags -cnotcontains 'LB.NotProcessWIP') {
    throw 'UE validation receipt native service actor identity/tag/non-WIP contract drifted'
}
$ServiceRows = @($UePayload.live_pie.service_hism_components)
if ($ServiceRows.Count -ne $ExpectedServiceHism.Count) {
    throw "UE validation receipt service HISM row count drifted: $($ServiceRows.Count)"
}
foreach ($ExpectedComponent in $ExpectedServiceHism.Keys) {
    $Matches = @($ServiceRows | Where-Object { [string]$_.component -ceq $ExpectedComponent })
    $Expected = $ExpectedServiceHism[$ExpectedComponent]
    if ($Matches.Count -ne 1 `
            -or [string]$Matches[0].mesh -cne [string]$Expected.mesh `
            -or [int]$Matches[0].instance_count -ne [int]$Expected.instance_count) {
        throw "UE validation receipt service HISM path/count drifted: $ExpectedComponent"
    }
}
$NativeBefore = $UePayload.protected_hashes_before.native_six_axis_robot
$NativeAfter = $UePayload.protected_hashes_after.native_six_axis_robot
if ([string]$UePayload.protected_hashes_before.press_full_factory_restored_v001_map -cne $ExpectedRestoredPressSha256 `
        -or [string]$UePayload.protected_hashes_after.press_full_factory_restored_v001_map -cne $ExpectedRestoredPressSha256) {
    throw 'UE validation receipt does not protect the exact full restored Press map'
}
foreach ($Native in @($NativeBefore,$NativeAfter)) {
    if ([IO.Path]::GetFullPath([string]$Native.receipt) -cne [IO.Path]::GetFullPath($ExpectedNativeValidationReceipt) `
            -or [string]$Native.receipt_sha256 -cne $ExpectedNativeValidationReceiptSha256 `
            -or [IO.Path]::GetFullPath([string]$Native.import_receipt) -cne [IO.Path]::GetFullPath($ExpectedNativeImportReceipt) `
            -or [string]$Native.import_receipt_sha256 -cne $ExpectedNativeImportReceiptSha256 `
            -or [IO.Path]::GetFullPath([string]$Native.lane_summary) -cne [IO.Path]::GetFullPath($ExpectedNativeLaneSummary) `
            -or [string]$Native.lane_summary_sha256 -cne $ExpectedNativeLaneSummarySha256 `
            -or [string]$Native.baseline_sha256 -cne $ExpectedNativeBaselineSha256 `
            -or [string]$Native.clean_disposition_contract_sha256 -cne $ExpectedNativeCleanDispositionContractSha256 `
            -or (@($Native.lod_triangle_totals) -join ',') -cne ($ExpectedNativeTriangleTotals -join ',') `
            -or @($Native.packages.psobject.Properties).Count -ne 8) {
        throw 'UE validation receipt does not bind the exact final native robot evidence chain'
    }
}
foreach ($Evidence in @(
        [pscustomobject]@{Path=$ExpectedNativeLaneSummary;Hash=$ExpectedNativeLaneSummarySha256},
        [pscustomobject]@{Path=$ExpectedNativeImportReceipt;Hash=$ExpectedNativeImportReceiptSha256},
        [pscustomobject]@{Path=$ExpectedNativeValidationReceipt;Hash=$ExpectedNativeValidationReceiptSha256})) {
    if (-not (Test-Path -LiteralPath $Evidence.Path -PathType Leaf) -or
            (Get-FileHash -Algorithm SHA256 -LiteralPath $Evidence.Path).Hash -cne $Evidence.Hash) {
        throw "Final native robot evidence missing or changed: $($Evidence.Path)"
    }
}
$SupportBefore = $UePayload.protected_hashes_before.native_support_kit_v002
$SupportAfter = $UePayload.protected_hashes_after.native_support_kit_v002
foreach ($Support in @($SupportBefore,$SupportAfter)) {
    if ([string]$Support.validation_receipt.sha256 -cne $ExpectedSupportValidationReceiptSha256 `
            -or (@($Support.lod_triangle_totals) -join ',') -cne '20408,7580,1780' `
            -or [int]$Support.asset_count -ne 12 `
            -or @($Support.packages.psobject.Properties).Count -ne 12) {
        throw 'UE validation receipt does not bind the exact native support-kit v002 authority'
    }
    foreach ($ExpectedPackage in @($SupportContract.packages.psobject.Properties)) {
        $Matches = @($Support.packages.psobject.Properties | Where-Object {
            $_.Name -ceq $ExpectedPackage.Name
        })
        if ($Matches.Count -ne 1 `
                -or [string]$Matches[0].Value -cne [string]$ExpectedPackage.Value) {
            throw "UE validation receipt native support package hash drifted: $($ExpectedPackage.Name)"
        }
    }
}

$MissingUsageWarnings = @(Select-String -LiteralPath $Log -Pattern `
    '(?i)(missing|not set|required|needed).*(?:bUsedWith)?InstancedStaticMeshes|(?:bUsedWith)?InstancedStaticMeshes.*(missing|not set|required|needed)')
if ($MissingUsageWarnings.Count -ne 0) {
    throw "Fresh live PIE log still contains $($MissingUsageWarnings.Count) InstancedStaticMeshes usage warnings"
}

$SourceAfter = @(Get-TreeSnapshot (Join-Path $Root 'Source'))
$ConfigAfter = @(Get-TreeSnapshot (Join-Path $Root 'Config'))
$SourceBeforeJson = $SourceBefore | ConvertTo-Json -Depth 4 -Compress
$SourceAfterJson = $SourceAfter | ConvertTo-Json -Depth 4 -Compress
$ConfigBeforeJson = $ConfigBefore | ConvertTo-Json -Depth 4 -Compress
$ConfigAfterJson = $ConfigAfter | ConvertTo-Json -Depth 4 -Compress
if ($SourceBeforeJson -cne $SourceAfterJson) { throw 'Source tree changed during validation' }
if ($ConfigBeforeJson -cne $ConfigAfterJson) { throw 'Config tree changed during validation' }

[ordered]@{
    '$schema' = 'lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-summary-v004/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'PASS__FRESH_LIVE_PIE_12_CONVEYOR_2_FLOOR_3_SERVICE_BATCH_12_SERVICE_INSTANCE_HISM_NATIVE_PROTECTED_V004'
    editor_exit_code = $EditorExitCode
    editor_executable = $Editor
    editor_shutdown_strategy = [string]$UePayload.shutdown_strategy
    process_gate = 'PASS__NO_ACTIVE_UNREAL_OR_BUILD_PROCESS_BEFORE_LAUNCH'
    validator_script = $Script
    validator_script_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Script).Hash
    ue_receipt = $UeReceipt
    ue_receipt_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $UeReceipt).Hash
    live_pie_log = $Log
    live_pie_log_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Log).Hash
    missing_instanced_static_mesh_usage_warning_count = $MissingUsageWarnings.Count
    pass_marker_count = $PassMarkers.Count
    source_tree = [ordered]@{
        file_count = $SourceBefore.Count
        snapshot_sha256_before_and_after = Get-TextSha256 $SourceBeforeJson
        changed = $false
    }
    config_tree = [ordered]@{
        file_count = $ConfigBefore.Count
        snapshot_sha256_before_and_after = Get-TextSha256 $ConfigBeforeJson
        changed = $false
    }
    maps_materials_meshes_native_robot_press_changed = $false
    maps_materials_meshes_native_robot_support_kit_press_changed = $false
    final_native_robot_authority = [ordered]@{
        lane_summary = $ExpectedNativeLaneSummary
        lane_summary_sha256 = $ExpectedNativeLaneSummarySha256
        import_receipt = $ExpectedNativeImportReceipt
        import_receipt_sha256 = $ExpectedNativeImportReceiptSha256
        validation_receipt = $ExpectedNativeValidationReceipt
        validation_receipt_sha256 = $ExpectedNativeValidationReceiptSha256
        lod_triangle_totals = $ExpectedNativeTriangleTotals
        full_restored_press_sha256 = $ExpectedRestoredPressSha256
    }
    final_native_support_kit_v002_authority = $SupportContract
    failures = @()
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Summary -Encoding utf8

Write-Output "BODYSHOP_FUNCTIONAL_HISM_USAGE_VALIDATION_SUMMARY_PASS $Summary"
