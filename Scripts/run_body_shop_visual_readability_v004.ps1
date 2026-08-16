[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$VisualV003Receipt,
    [Parameter(Mandatory=$true)][string]$HISMValidationSummary
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$AuditRoot = Join-Path $Root 'Saved\Audits\BodyShop\Experimental_v001'
$LogRoot = Join-Path $AuditRoot 'Logs'
$PatchReceipt = Join-Path $AuditRoot 'visual_readability_v004_patch.json'
$ValidationReceipt = Join-Path $AuditRoot 'visual_readability_v004_validation.json'
$RunnerSummary = Join-Path $AuditRoot 'visual_readability_v004_runner_summary.json'
$RepairScript = Join-Path $Root 'Scripts\repair_body_shop_visual_readability_v004.py'
$ValidatorScript = Join-Path $Root 'Scripts\validate_body_shop_visual_readability_v004.py'

function Resolve-Receipt([string]$Path,[string]$ExpectedSchema,[string]$ExpectedStatus) {
    $Resolved = if ([IO.Path]::IsPathRooted($Path)) {
        [IO.Path]::GetFullPath($Path)
    } else {
        [IO.Path]::GetFullPath((Join-Path $Root $Path))
    }
    if (-not (Test-Path -LiteralPath $Resolved -PathType Leaf)) {
        throw "Required receipt is missing: $Resolved"
    }
    $Payload = Get-Content -Raw -LiteralPath $Resolved | ConvertFrom-Json
    if ([string]$Payload.'$schema' -cne $ExpectedSchema -or
        [string]$Payload.status -cne $ExpectedStatus -or @($Payload.failures).Count -ne 0) {
        throw "Required receipt did not pass its exact contract: $Resolved"
    }
    return $Resolved
}

function Assert-NoUnrealOrBuildProcess {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName }
    if ($Active) {
        throw "Refusing v004 work while Unreal/build processes are active: $($Active.ProcessName -join ', ')"
    }
}

function Assert-ExactOutput([string]$Path,[string]$ExpectedSchema,[string]$ExpectedStatus) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Expected v004 output is missing: $Path"
    }
    $Payload = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ([string]$Payload.'$schema' -cne $ExpectedSchema -or
        [string]$Payload.status -cne $ExpectedStatus -or @($Payload.failures).Count -ne 0) {
        throw "v004 output did not pass its exact contract: $Path ($($Payload.status))"
    }
}

$VisualV003 = Resolve-Receipt $VisualV003Receipt `
    'lineboss/audit/bodyshop/visual-readability-v003-validation/v1' `
    'PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V003'
$HISM = Resolve-Receipt $HISMValidationSummary `
    'lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-summary-v001/v1' `
    'PASS__FRESH_LIVE_PIE_LOG_HAS_NO_INSTANCED_STATIC_MESH_USAGE_WARNINGS'

Assert-NoUnrealOrBuildProcess
if (Test-Path -LiteralPath $PatchReceipt -PathType Leaf) {
    throw "Refusing to overwrite immutable v004 patch receipt: $PatchReceipt"
}
if (Test-Path -LiteralPath $ValidationReceipt -PathType Leaf) {
    throw "Refusing to overwrite immutable v004 validation receipt: $ValidationReceipt"
}
New-Item -ItemType Directory -Force $LogRoot | Out-Null
$env:LB_BODYSHOP_VISUAL_V003_RECEIPT = $VisualV003
$env:LB_BODYSHOP_HISM_VALIDATION_SUMMARY = $HISM
try {
    $Repair = $RepairScript.Replace('\','/')
    & $Editor $Project "-ExecutePythonScript=$Repair" -unattended -nop4 -nosplash `
        -NullRHI -stdout -FullStdOutLogOutput *> (Join-Path $LogRoot 'repair_body_shop_visual_readability_v004.log')
    if ($LASTEXITCODE -ne 0) { throw "v004 map repair Editor process failed ($LASTEXITCODE)" }
    Assert-ExactOutput $PatchReceipt `
        'lineboss/audit/bodyshop/visual-readability-v004-patch/v1' `
        'PASS__BODYSHOP_VISUAL_READABILITY_V004_MAP_PATCHED'

    Assert-NoUnrealOrBuildProcess
    $env:LB_BODYSHOP_VISUAL_V004_PATCH_RECEIPT = $PatchReceipt
    $Validator = $ValidatorScript.Replace('\','/')
    & $Editor $Project "-ExecutePythonScript=$Validator" -unattended -nop4 -nosplash `
        -NullRHI -stdout -FullStdOutLogOutput *> (Join-Path $LogRoot 'validate_body_shop_visual_readability_v004.log')
    if ($LASTEXITCODE -ne 0) { throw "v004 fresh validator Editor process failed ($LASTEXITCODE)" }
    Assert-ExactOutput $ValidationReceipt `
        'lineboss/audit/bodyshop/visual-readability-v004-validation/v1' `
        'PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V004'

    [ordered]@{
        '$schema'='lineboss/audit/bodyshop/visual-readability-v004-runner-summary/v1'
        generated_utc=(Get-Date).ToUniversalTime().ToString('o')
        status='PASS__GUARDED_PATCH_AND_FRESH_VALIDATION_BODYSHOP_VISUAL_READABILITY_V004'
        prerequisites=[ordered]@{
            visual_v003=[ordered]@{path=$VisualV003;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $VisualV003).Hash}
            functional_hism_validation=[ordered]@{path=$HISM;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $HISM).Hash}
        }
        patch=[ordered]@{path=$PatchReceipt;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $PatchReceipt).Hash}
        validation=[ordered]@{path=$ValidationReceipt;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $ValidationReceipt).Hash}
        failures=@()
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $RunnerSummary -Encoding utf8
}
finally {
    Remove-Item Env:LB_BODYSHOP_VISUAL_V003_RECEIPT -ErrorAction SilentlyContinue
    Remove-Item Env:LB_BODYSHOP_HISM_VALIDATION_SUMMARY -ErrorAction SilentlyContinue
    Remove-Item Env:LB_BODYSHOP_VISUAL_V004_PATCH_RECEIPT -ErrorAction SilentlyContinue
}
