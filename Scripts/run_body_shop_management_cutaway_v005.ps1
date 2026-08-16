[CmdletBinding()]
param(
    [string]$VisualV004ValidationReceipt = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\BodyShop\Experimental_v001\visual_readability_v004_validation.json'
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$MapFile = Join-Path $Root 'Content\LineBoss\BodyShop\Experimental\v001\Maps\LB_BodyShop_Prototype_v001.umap'
$MapAsset = '/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001'
$ExpectedMapV004 = '6921968DE25E48497491F58E098CF870519A4E17F0C40A13EE88A9E99D155FC9'
$ExpectedV004Receipt = '956E08511F2AA840D71B94E07217DBA357EA955B701BA3A8C9F744AAAC11757E'
$AuditRoot = Join-Path $Root 'Saved\Audits\BodyShop\Experimental_v001'
$LogRoot = Join-Path $AuditRoot 'Logs'
$PatchReceipt = Join-Path $AuditRoot 'management_cutaway_v005_patch.json'
$ValidationReceipt = Join-Path $AuditRoot 'management_cutaway_v005_validation.json'
$RunnerSummary = Join-Path $AuditRoot 'management_cutaway_v005_runner_summary.json'
$RepairLog = Join-Path $LogRoot 'repair_body_shop_management_cutaway_v005.log'
$ValidatorLog = Join-Path $LogRoot 'validate_body_shop_management_cutaway_v005.log'
$BackupRoot = Join-Path $Root 'Saved\Quarantine\BodyShop\ManagementCutaway_v005_PrePatch'
$RepairScript = Join-Path $Root 'Scripts\repair_body_shop_management_cutaway_v005.py'
$ValidatorScript = Join-Path $Root 'Scripts\validate_body_shop_management_cutaway_v005.py'

function Assert-NoUnrealOrBuildProcess {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName }
    if ($Active) {
        throw "Refusing v005 cutaway work while Unreal/build processes are active: $($Active.ProcessName -join ', ')"
    }
}

function Assert-ProtectedV004Snapshot($Payload) {
    foreach ($Property in $Payload.protected_hashes.psobject.Properties) {
        $Path = [string]$Property.Name
        $Contract = $Property.Value
        $Exists = Test-Path -LiteralPath $Path -PathType Leaf
        if ($Exists -ne [bool]$Contract.exists) {
            throw "Protected v004 path existence drift: $Path"
        }
        if ($Exists -and (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash -cne [string]$Contract.sha256) {
            throw "Protected v004 path hash drift: $Path"
        }
        if (-not $Exists -and $null -ne $Contract.sha256) {
            throw "Protected v004 absent-path contract drift: $Path"
        }
    }
}

function Assert-ExactConfig {
    $Expected = [ordered]@{
        'DefaultEditor.ini'='BBE05501998265524E8ACD5319DBC42E748DDE39FB25463C8BB0D431AC746D16'
        'DefaultEditorPerProjectUserSettings.ini'='9255BE413FFFB3970BAD3C921E8E5BFE3DD41A0B01F45348354FCAAC01E9E6D4'
        'DefaultEngine.ini'='A1A3B4E5EC0327BB9AD05B094B7749CE9CE9795B1D065CFA4196C1AD3EFB82D3'
        'DefaultGame.ini'='1DE2055DB7A0F4EA1653E9656A33EE692CBEF133B8761A08A31B090B3832484C'
        'DefaultGameUserSettings.ini'='D4E55BBFC7F843097D40E3335B1FE57AE12F804D981564F904AEBCDA34F35F3E'
        'DefaultInput.ini'='8DCE19104C744A1DA03413EC234CF9D0BAD1BF40BD718C1F770D68CBD42D2F00'
    }
    $ConfigRoot = Join-Path $Root 'Config'
    $Files = @(Get-ChildItem -LiteralPath $ConfigRoot -File -Recurse)
    if ($Files.Count -ne $Expected.Count) { throw "Config inventory drift: $($Files.Count) files" }
    foreach ($Name in $Expected.Keys) {
        $Path = Join-Path $ConfigRoot $Name
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf) -or
            (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash -cne $Expected[$Name]) {
            throw "Config hash drift: $Name"
        }
    }
}

function Resolve-ExactV004Receipt([string]$Path) {
    $Resolved = [IO.Path]::GetFullPath($Path)
    $ExpectedPath = [IO.Path]::GetFullPath((Join-Path $AuditRoot 'visual_readability_v004_validation.json'))
    if ($Resolved -cne $ExpectedPath -or -not (Test-Path -LiteralPath $Resolved -PathType Leaf)) {
        throw "v005 requires the exact pinned v004 validation receipt: $ExpectedPath"
    }
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Resolved).Hash -cne $ExpectedV004Receipt) {
        throw 'Pinned v004 validation receipt hash drift'
    }
    $Payload = Get-Content -Raw -LiteralPath $Resolved | ConvertFrom-Json
    if ([string]$Payload.'$schema' -cne 'lineboss/audit/bodyshop/visual-readability-v004-validation/v1' -or
        [string]$Payload.status -cne 'PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V004' -or
        @($Payload.failures).Count -ne 0 -or
        [string]$Payload.map.sha256 -cne $ExpectedMapV004 -or
        @($Payload.protected_hashes.psobject.Properties).Count -ne 29) {
        throw 'Pinned v004 validation receipt contract drift'
    }
    Assert-ProtectedV004Snapshot $Payload
    return $Resolved
}

function Read-ExactOutput([string]$Path,[string]$ExpectedSchema,[string]$ExpectedStatus) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Expected immutable v005 output is missing: $Path"
    }
    $Payload = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ([string]$Payload.'$schema' -cne $ExpectedSchema -or
        [string]$Payload.status -cne $ExpectedStatus -or @($Payload.failures).Count -ne 0) {
        throw "v005 output did not pass its exact contract: $Path ($($Payload.status))"
    }
    return $Payload
}

function Assert-ExactCutawayLabels($Payload) {
    $Expected = @()
    foreach ($X in @(-8000,-6000,-4000,-2000,0,2000,4000,6000,8000)) {
        $Expected += ('LB_BS_ENV_Column_South_{0:+0000;-0000;+0000}' -f $X)
        $Expected += ('LB_BS_ENV_Truss_{0:+0000;-0000;+0000}' -f $X)
    }
    $Expected = @($Expected | Sort-Object)
    $Actual = @($Payload.changed_actor_labels | ForEach-Object { [string]$_ } | Sort-Object)
    if ($Actual.Count -ne 18 -or @((Compare-Object -ReferenceObject $Expected -DifferenceObject $Actual)).Count -ne 0) {
        throw 'Patch receipt changed-actor scope is not the exact nine trusses plus nine south columns'
    }
}

if (-not (Test-Path -LiteralPath $Project -PathType Leaf) -or
    -not (Test-Path -LiteralPath $Editor -PathType Leaf) -or
    -not (Test-Path -LiteralPath $MapFile -PathType Leaf) -or
    -not (Test-Path -LiteralPath $RepairScript -PathType Leaf) -or
    -not (Test-Path -LiteralPath $ValidatorScript -PathType Leaf)) {
    throw 'Pinned project, UE 5.8 commandlet, map, repair, or validator input is missing'
}

$V004 = Resolve-ExactV004Receipt $VisualV004ValidationReceipt
Assert-ExactConfig
Assert-NoUnrealOrBuildProcess
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $MapFile).Hash -cne $ExpectedMapV004) {
    throw 'Body Shop map is not the exact current v004 package'
}
foreach ($Path in @($PatchReceipt,$ValidationReceipt,$RunnerSummary,$RepairLog,$ValidatorLog,$BackupRoot)) {
    if (Test-Path -LiteralPath $Path) {
        throw "Refusing to overwrite immutable v005 output or recoverable backup: $Path"
    }
}

New-Item -ItemType Directory -Force $LogRoot | Out-Null
$env:LB_BODYSHOP_VISUAL_V004_VALIDATION_RECEIPT = $V004
try {
    $Repair = $RepairScript.Replace('\','/')
    & $Editor $Project "-ExecutePythonScript=$Repair" -unattended -nop4 -nosplash `
        -NullRHI -stdout -FullStdOutLogOutput *> $RepairLog
    if ($LASTEXITCODE -ne 0) { throw "v005 cutaway repair Editor process failed ($LASTEXITCODE)" }
    $Patch = Read-ExactOutput $PatchReceipt `
        'lineboss/audit/bodyshop/management-cutaway-v005-patch/v1' `
        'PASS__BODYSHOP_MANAGEMENT_CUTAWAY_V005_MAP_PATCHED'
    Assert-ExactCutawayLabels $Patch
    if ([string]$Patch.map.asset -cne $MapAsset -or
        [string]$Patch.map.sha256_before -cne $ExpectedMapV004 -or
        [string]$Patch.map.sha256_after -cne (Get-FileHash -Algorithm SHA256 -LiteralPath $MapFile).Hash -or
        [int]$Patch.changed_actor_count -ne 18 -or
        [int]$Patch.map.actors_added_or_removed -ne 0 -or
        @($Patch.content_packages_changed).Count -ne 1 -or
        [string]$Patch.content_packages_changed[0] -cne $MapAsset -or
        $Patch.actor_count_lights_exposure_materials_meshes_cameras_gameplay_unchanged -ne $true -or
        @($Patch.materials_or_meshes_changed).Count -ne 0 -or @($Patch.camera_changes).Count -ne 0 -or
        @($Patch.gameplay_source_config_or_save_changes).Count -ne 0) {
        throw 'v005 patch receipt exact map-only contract drift'
    }

    Assert-NoUnrealOrBuildProcess
    $env:LB_BODYSHOP_MANAGEMENT_CUTAWAY_V005_PATCH_RECEIPT = $PatchReceipt
    $Validator = $ValidatorScript.Replace('\','/')
    & $Editor $Project "-ExecutePythonScript=$Validator" -unattended -nop4 -nosplash `
        -NullRHI -stdout -FullStdOutLogOutput *> $ValidatorLog
    if ($LASTEXITCODE -ne 0) { throw "v005 cutaway fresh validator Editor process failed ($LASTEXITCODE)" }
    $Validation = Read-ExactOutput $ValidationReceipt `
        'lineboss/audit/bodyshop/management-cutaway-v005-validation/v1' `
        'PASS__FRESH_RELOAD_BODYSHOP_MANAGEMENT_CUTAWAY_V005'
    $FinalMapHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $MapFile).Hash
    if ([string]$Validation.map.asset -cne $MapAsset -or
        [string]$Validation.map.sha256 -cne [string]$Patch.map.sha256_after -or
        [string]$Validation.map.sha256 -cne $FinalMapHash -or
        [int]$Validation.map.state.actor_count -ne 336 -or
        [int]$Validation.map.state.cutaway_actor_count -ne 18 -or
        [int]$Validation.map.state.north_columns_visible_count -ne 9 -or
        $Validation.map.read_only_fresh_load_hash_unchanged -ne $true -or
        $Validation.writes_to_content_source_config_or_saves -ne $false -or
        @($Validation.materials_or_meshes_changed).Count -ne 0 -or
        @($Validation.camera_changes_in_this_validator).Count -ne 0 -or
        @($Validation.gameplay_changes_in_this_validator).Count -ne 0) {
        throw 'v005 validation receipt exact fresh-read-only contract drift'
    }

    [ordered]@{
        '$schema'='lineboss/audit/bodyshop/management-cutaway-v005-runner-summary/v1'
        generated_utc=(Get-Date).ToUniversalTime().ToString('o')
        status='PASS__GUARDED_PATCH_AND_FRESH_VALIDATION_BODYSHOP_MANAGEMENT_CUTAWAY_V005'
        prerequisite=[ordered]@{visual_readability_v004_validation=[ordered]@{path=$V004;sha256=$ExpectedV004Receipt}}
        scripts=[ordered]@{
            repair=[ordered]@{path=$RepairScript;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $RepairScript).Hash}
            validator=[ordered]@{path=$ValidatorScript;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $ValidatorScript).Hash}
        }
        map=[ordered]@{asset=$MapAsset;sha256_before=$ExpectedMapV004;sha256_after=$FinalMapHash}
        patch=[ordered]@{path=$PatchReceipt;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $PatchReceipt).Hash}
        validation=[ordered]@{path=$ValidationReceipt;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $ValidationReceipt).Hash}
        recoverable_backup=$Patch.recoverable_backup
        changed_actor_count=18
        content_packages_changed=@($MapAsset)
        failures=@()
    } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $RunnerSummary -Encoding utf8
}
finally {
    Remove-Item Env:LB_BODYSHOP_VISUAL_V004_VALIDATION_RECEIPT -ErrorAction SilentlyContinue
    Remove-Item Env:LB_BODYSHOP_MANAGEMENT_CUTAWAY_V005_PATCH_RECEIPT -ErrorAction SilentlyContinue
}
