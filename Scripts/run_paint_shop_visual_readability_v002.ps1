[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Map = Join-Path $Root 'Content\LineBoss\PaintShop\Experimental\v001\Maps\LB_PaintShop_Prototype_v001.umap'
$RepairScript = Join-Path $Root 'Scripts\repair_paint_shop_visual_readability_v002.py'
$ValidatorScript = Join-Path $Root 'Scripts\validate_paint_shop_visual_readability_v002.py'
$AuditRoot = Join-Path $Root 'Saved\Audits\PaintShop\Experimental_v001\VisualReadability_v002'
$PatchReceipt = Join-Path $AuditRoot 'paint_shop_visual_readability_v002_patch.json'
$ValidationReceipt = Join-Path $AuditRoot 'paint_shop_visual_readability_v002_validation.json'
$RunnerSummary = Join-Path $AuditRoot 'paint_shop_visual_readability_v002_runner_summary.json'
$LogRoot = Join-Path $AuditRoot 'Logs'
$BackupRoot = Join-Path $Root 'Saved\Quarantine\PaintShop\VisualReadability_v002_PrePatch'

$Frozen = [ordered]@{
    map = [ordered]@{path=$Map; sha256='2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069'}
    creation = [ordered]@{path=(Join-Path $Root 'Saved\Audits\PaintShop\Experimental_v001\paint_shop_prototype_map_create_v001.json'); sha256='4E65E671CB25D8615F3A775B1697E7D72C523D58FFA7481356A5BF8D5941AC09'}
    validation = [ordered]@{path=(Join-Path $Root 'Saved\Audits\PaintShop\Experimental_v001\paint_shop_prototype_map_validation_v001.json'); sha256='B452A68FF04B89BF6D6FD43486230692C05B1338368794570174150DFC90F136'}
    release = [ordered]@{path=(Join-Path $Root 'Saved\Audits\PaintShop\Experimental_v001\ReleaseValidation\20260814T174958518Z\release_validation_summary_v001.json'); sha256='660546CB5ABECB16A59C716F4D69DDAAE0DA143F70AA2685C43B9A4DB71AE1CB'}
    live_pie = [ordered]@{path=(Join-Path $Root 'Saved\Audits\PaintShop\Experimental_v001\ReleaseValidation\20260814T174958518Z\live_pie_edcoat_validation_v001.json'); sha256='8E01A7635D968C95A89B8F8371129869D5BC8BF8DE20F05C86396437E571E4D4'}
    automation_index = [ordered]@{path=(Join-Path $Root 'Saved\Automation\PaintShop\Experimental_v001\ReleaseValidation_20260814T174958518Z\index.json'); sha256='D9AB9A52221848CB9E7A75745F231A738A1EA2FA2F885EF9B717ED6B9A2B33BE'}
    calibration = [ordered]@{path=(Join-Path $Root 'Saved\Audits\PaintShop\Experimental_v001\LightingCalibration_v001\20260814T175521Z\lighting_calibration_v001.json'); sha256='1F287DD1D0758F37DD94F83737922B4282836E2BAB6506C27EED190E4117D766'}
    calibration_B_capture = [ordered]@{path=(Join-Path $Root 'Saved\Audits\PaintShop\Experimental_v001\LightingCalibration_v001\20260814T175521Z\02_B_stylized.png'); sha256='463F90CA7BA45EF45F4A0F594FBE429088813752CF3545976FBB7FB230041E58'}
    factory_visual_standard = [ordered]@{path=(Join-Path $Root 'Docs\LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md'); sha256='0E61306C437BCB587C82D6BF5609CAFDA1211E004CCFC86C6C4608CBA42A2971'}
    repair_script = [ordered]@{path=$RepairScript; sha256='2EA599FD11F804738943E39FABE6EFEBDD22830D773441E972B7AC7BEC7B7D10'}
    validator_script = [ordered]@{path=$ValidatorScript; sha256='F9FCB6060D4D60DB985F0EAB3CB782E4AD75AB55845FCE25AE5CB450E1B1296B'}
}

function Assert-ExactHash([string]$Path, [string]$Expected) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required frozen file is missing: $Path"
    }
    $Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
    if ($Actual -cne $Expected) {
        throw "Frozen file hash drift: $Path expected=$Expected actual=$Actual"
    }
}

function Assert-NoUnrealOrBuildProcess {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -ne 0) {
        throw "Refusing Paint v002 patch while Unreal/build processes are active: $($Active.ProcessName -join ', ')"
    }
}

function Read-ExactReceipt([string]$Path, [string]$Schema, [string]$Status) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Expected immutable receipt is missing: $Path"
    }
    $Payload = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ([string]$Payload.'$schema' -cne $Schema -or [string]$Payload.status -cne $Status -or
        @($Payload.failures).Count -ne 0) {
        throw "Receipt failed its exact schema/status contract: $Path"
    }
    return $Payload
}

if ((Resolve-Path -LiteralPath $Root).Path -cne $Root) { throw 'Project root identity drift' }
if (-not (Test-Path -LiteralPath $Project -PathType Leaf)) { throw "Project file missing: $Project" }
if (-not (Test-Path -LiteralPath $Editor -PathType Leaf)) { throw "UnrealEditor-Cmd missing: $Editor" }

Assert-NoUnrealOrBuildProcess
foreach ($row in $Frozen.GetEnumerator()) { Assert-ExactHash $row.Value.path $row.Value.sha256 }

$Create = Read-ExactReceipt $Frozen.creation.path `
    'lineboss/audit/paint-shop/prototype-map-create-v001/v1' `
    'PASS__ISOLATED_PAINT_SHOP_ONE_BOOTSTRAP_ZERO_MAP_OWNED_PRODUCTION'
$BaseValidation = Read-ExactReceipt $Frozen.validation.path `
    'lineboss/audit/paint-shop/prototype-map-validation-v001/v1' `
    'PASS__FRESH_RELOAD_PAINT_SHOP_PROTOTYPE_MAP_V001'
$Release = Read-ExactReceipt $Frozen.release.path `
    'lineboss/audit/paint-shop/release-validation-run-v001/v1' `
    'PASS__PAINT_SHOP_AUTOMATION_AND_ACTUAL_PLAYER_ED_COAT_PIE_V001'
$Calibration = Read-ExactReceipt $Frozen.calibration.path `
    'lineboss/audit/paint-shop/lighting-calibration-v001/v1' `
    'PASS__TRANSIENT_PAINT_SHOP_LIGHTING_CALIBRATION_V001'

if ([string]$Create.map_sha256 -cne $Frozen.map.sha256 -or
    [string]$BaseValidation.map_sha256 -cne $Frozen.map.sha256 -or
    [string]$Release.expected_map_sha256 -cne $Frozen.map.sha256 -or
    [string]$Calibration.map_sha256_before -cne $Frozen.map.sha256 -or
    [string]$Calibration.map_sha256_after -cne $Frozen.map.sha256 -or
    $Calibration.map_hash_unchanged -ne $true) {
    throw 'Frozen Paint map authority chain does not share the exact pre-patch hash'
}
$Selected = @($Calibration.options | Where-Object { $_.name -ceq 'B_stylized' })
if ($Selected.Count -ne 1 -or [double]$Selected[0].rect_lumens -ne 1200.0 -or
    [double]$Selected[0].sun -ne 0.30 -or [double]$Selected[0].sky -ne 0.20 -or
    [double]$Selected[0].exposure_bias -ne -0.50 -or
    [string]$Selected[0].sha256 -cne $Frozen.calibration_B_capture.sha256) {
    throw 'Selected calibration B contract drift'
}

foreach ($Output in @($PatchReceipt,$ValidationReceipt,$RunnerSummary,$LogRoot,$BackupRoot)) {
    if (Test-Path -LiteralPath $Output) { throw "Refusing to overwrite v002 output: $Output" }
}
New-Item -ItemType Directory -Path $LogRoot | Out-Null

$RepairPath = $RepairScript.Replace('\','/')
& $Editor $Project "-ExecutePythonScript=$RepairPath" -unattended -nop4 -nosplash -NullRHI `
    -stdout -FullStdOutLogOutput *> (Join-Path $LogRoot 'repair_paint_shop_visual_readability_v002.log')
if ($LASTEXITCODE -ne 0) { throw "Paint v002 repair Editor process failed ($LASTEXITCODE); backup may be recoverable" }
$Patch = Read-ExactReceipt $PatchReceipt `
    'lineboss/audit/paint-shop/visual-readability-v002-patch/v1' `
    'PASS__PAINT_SHOP_VISUAL_READABILITY_V002_MAP_PATCHED'
if ([string]$Patch.source_script_sha256 -cne $Frozen.repair_script.sha256 -or
    [string]$Patch.map.sha256_before -cne $Frozen.map.sha256 -or
    @($Patch.content_packages_changed).Count -ne 1 -or
    [string]$Patch.content_packages_changed[0] -cne '/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001') {
    throw 'Paint v002 patch receipt scope/hash binding drift'
}

Assert-NoUnrealOrBuildProcess
$ValidatorPath = $ValidatorScript.Replace('\','/')
& $Editor $Project "-ExecutePythonScript=$ValidatorPath" -unattended -nop4 -nosplash -NullRHI `
    -stdout -FullStdOutLogOutput *> (Join-Path $LogRoot 'validate_paint_shop_visual_readability_v002.log')
if ($LASTEXITCODE -ne 0) { throw "Paint v002 independent validator Editor process failed ($LASTEXITCODE)" }
$Validation = Read-ExactReceipt $ValidationReceipt `
    'lineboss/audit/paint-shop/visual-readability-v002-validation/v1' `
    'PASS__FRESH_RELOAD_PAINT_SHOP_VISUAL_READABILITY_V002'
if ([string]$Validation.validator_script_sha256 -cne $Frozen.validator_script.sha256 -or
    [string]$Validation.repair_script_sha256 -cne $Frozen.repair_script.sha256 -or
    [string]$Validation.map.sha256 -cne [string]$Patch.map.sha256_after) {
    throw 'Paint v002 independent validation receipt binding drift'
}

if (Test-Path -LiteralPath $RunnerSummary) { throw "Refusing late runner-summary overwrite: $RunnerSummary" }
[ordered]@{
    '$schema' = 'lineboss/audit/paint-shop/visual-readability-v002-runner-summary/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'PASS__GUARDED_PATCH_AND_FRESH_VALIDATION_PAINT_SHOP_VISUAL_READABILITY_V002'
    selected_calibration = [ordered]@{name='B_stylized';rect_lumens=1200.0;temperature_kelvin=5000.0;sun=0.30;sky=0.20;fixed_exposure_bias=-0.50}
    frozen_authorities = $Frozen
    patch = [ordered]@{path=$PatchReceipt;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $PatchReceipt).Hash}
    validation = [ordered]@{path=$ValidationReceipt;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $ValidationReceipt).Hash}
    only_content_package_changed = '/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001'
    other_shop_maps_changed = @()
    promotion_authorized = $false
    failures = @()
} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $RunnerSummary -Encoding utf8

Write-Host "PASS: guarded Paint Shop visual-readability v002 patch and independent fresh validation"
Write-Host "Patch: $PatchReceipt"
Write-Host "Validation: $ValidationReceipt"
Write-Host "Summary: $RunnerSummary"
