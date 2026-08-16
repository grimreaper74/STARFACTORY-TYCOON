[CmdletBinding()]
param([string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8')

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Importer = Join-Path $Root 'Scripts\import_spray_booth_runtime_v002.py'
$Validator = Join-Path $Root 'Scripts\validate_spray_booth_runtime_v002.py'
$RecoveryAuthority = Join-Path $Root 'SourceAssets\Candidate\PaintShop\SprayBoothRuntime_v002\Authority\unreal_lane_recovery_authority_v003.json'
$DestinationDisk = Join-Path $Root 'Content\LineBoss\Candidates\PaintShop\SprayBoothRuntime_v002'
$ImportReceipt = Join-Path $Root 'Saved\Audits\PaintShop\SprayBoothRuntime_v002\import_v002.json'
$ValidationReceipt = Join-Path $Root 'Saved\Audits\PaintShop\SprayBoothRuntime_v002\validation_v002.json'
$ExpectedImporter = 'B23FF792228CC5198178CE99C6C8BFFD322FD9720424329FDBD01485F28399EF'
$ExpectedValidator = '2AC134AF9A91730186AEFA83F66B933FBFCD337BEBAE652F52BB124403962196'
$ExpectedRecoveryAuthority = '541A4F2DBD97A19106F932B39CF495A7FB7030371F7C7EDC18CE8D6CA4C73034'

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing file: $Path" }
    (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}
function Get-Relative([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path); $prefix=$Root.TrimEnd('\')+'\'
    if(-not $full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw "Outside project: $full"}
    $full.Substring($prefix.Length).Replace('\','/')
}
function Get-ProtectedSnapshot {
    $snapshot=[ordered]@{}
    foreach($base in @((Join-Path $Root 'Content'),(Join-Path $Root 'Config'),(Join-Path $Root 'Saved\SaveGames'))){
        if(Test-Path -LiteralPath $base -PathType Container){
            foreach($item in @(Get-ChildItem -LiteralPath $base -File -Recurse | Sort-Object FullName)){
                if($item.FullName.StartsWith($DestinationDisk.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)){continue}
                $snapshot[(Get-Relative $item.FullName)]=Get-Sha256 $item.FullName
            }
        }
    }
    $snapshot
}
function Assert-Same([object]$Before,[object]$After,[string]$Stage){
    if(($Before|ConvertTo-Json -Depth 3 -Compress) -cne ($After|ConvertTo-Json -Depth 3 -Compress)){
        throw "$Stage changed protected existing Content/Config/SaveGames"
    }
}
function Assert-Marker([string]$Log,[string]$Marker){
    $count=@(Select-String -LiteralPath $Log -SimpleMatch $Marker).Count
    if($count -ne 1){throw "Expected one $Marker in $Log; found $count"}
}
function Assert-CollisionEvidence([object]$Evidence,[string]$Stage){
    if($null -eq $Evidence -or
       [string]$Evidence.acceptance_basis -cne 'BODY_SETUP_AGG_GEOM_EXACT_TYPE_COUNTS'){
        throw "$Stage did not use the exact BodySetup AggGeom acceptance basis"
    }
    $counts=$Evidence.aggregate_geometry_counts
    if($null -eq $counts -or [int]$counts.box_elems -ne 0 -or
       [int]$counts.sphere_elems -ne 0 -or [int]$counts.sphyl_elems -ne 0 -or
       [int]$counts.tapered_capsule_elems -ne 0 -or [int]$counts.convex_elems -ne 3){
        throw "$Stage exact aggregate collision inventory failed"
    }
    if([int]$Evidence.static_mesh_editor_simple_collision_count -ne 0 -or
       [int]$Evidence.static_mesh_editor_convex_collision_count -ne 3){
        throw "$Stage UE 5.8 collision API cross-check failed"
    }
    if([string]$Evidence.runtime_convex_vertex_bounds_validation -cne
       'UNAVAILABLE__UE_5_8_KCONVEXELEM_PYTHON_REFLECTION_EXPOSES_NEITHER_VERTEX_DATA_NOR_BOUNDS'){
        throw "$Stage convex detail reflection finding drifted"
    }
}

foreach($file in @($Project,$Editor,$Importer,$Validator,$RecoveryAuthority)){
    if(-not(Test-Path -LiteralPath $file -PathType Leaf)){throw "Missing prerequisite: $file"}
}
if((Get-Sha256 $Importer) -cne $ExpectedImporter){throw 'Frozen importer hash drift'}
if((Get-Sha256 $Validator) -cne $ExpectedValidator){throw 'Frozen validator hash drift'}
if((Get-Sha256 $RecoveryAuthority) -cne $ExpectedRecoveryAuthority){throw 'Frozen successor authority hash drift'}
foreach($path in @($DestinationDisk,$ImportReceipt,$ValidationReceipt)){
    if(Test-Path -LiteralPath $path){throw "Fresh-only output already exists: $path"}
}
$live=@(Get-Process -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -in @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool')})
if($live.Count){throw "Close active Unreal/build processes: $($live.ProcessName -join ', ')"}

$before=Get-ProtectedSnapshot
$stamp=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$run=Join-Path $Root "Saved\Audits\PaintShop\SprayBoothRuntime_v002\Runs\$stamp"
New-Item -ItemType Directory -Path $run | Out-Null
$importLog=Join-Path $run 'import.log'; $validationLog=Join-Path $run 'validation.log'

& $Editor $Project "-ExecutePythonScript=$($Importer.Replace('\','/'))" -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput *> $importLog
if($LASTEXITCODE -ne 0){throw "Spray booth import failed ($LASTEXITCODE): $importLog"}
Assert-Marker $importLog 'LINE_BOSS_SPRAY_BOOTH_RUNTIME_V002_IMPORT_PASS'
if(-not(Test-Path -LiteralPath $ImportReceipt -PathType Leaf)){throw 'Import receipt missing'}
$import=Get-Content -Raw $ImportReceipt|ConvertFrom-Json
if($import.status -cne 'PASS__FRESH_ORIGINAL_PROCEDURAL_SPRAY_BOOTH__TWO_SOURCE_LODS__PORTAL_SAFE_COLLISION' -or
   (@($import.triangles) -join ',') -cne '3804,420' -or @($import.packages).Count -ne 7 -or
   @($import.package_files).Count -ne 7){
    throw 'Import receipt exact contract failed'
}
Assert-CollisionEvidence $import.collision 'Import receipt'
Assert-Same $before (Get-ProtectedSnapshot) 'Import'

& $Editor $Project "-ExecutePythonScript=$($Validator.Replace('\','/'))" -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput *> $validationLog
if($LASTEXITCODE -ne 0){throw "Independent spray booth validation failed ($LASTEXITCODE): $validationLog"}
Assert-Marker $validationLog 'LINE_BOSS_SPRAY_BOOTH_RUNTIME_V002_VALIDATION_PASS'
if(-not(Test-Path -LiteralPath $ValidationReceipt -PathType Leaf)){throw 'Validation receipt missing'}
$validation=Get-Content -Raw $ValidationReceipt|ConvertFrom-Json
if($validation.status -cne 'PASS__INDEPENDENT_SPRAY_BOOTH_V002__EXACT_GEOMETRY_MATERIALS_LODS_COLLISION_UV_NANITE_SCREENS_PROVENANCE' -or
   @($validation.failures).Count -ne 0 -or (@($validation.facts.triangles) -join ',') -cne '3804,420' -or
   @($validation.facts.package_files).Count -ne 7){
    throw 'Independent receipt exact contract failed'
}
Assert-CollisionEvidence $validation.facts.collision 'Independent receipt'
Assert-Same $before (Get-ProtectedSnapshot) 'Independent validation'
$summary=[ordered]@{
    '$schema'='lineboss/audit/paint/spray-booth-runtime-run-v002/v2'; generated_utc=(Get-Date).ToUniversalTime().ToString('o')
    status='PASS__FRESH_IMPORT_AND_INDEPENDENT_VALIDATION__ORIGINAL_PROCEDURAL_SPRAY_BOOTH_V002'
    destination='/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002'
    importer_sha256=$ExpectedImporter; validator_sha256=$ExpectedValidator
    successor_authority_sha256=$ExpectedRecoveryAuthority
    collision_acceptance='BODY_SETUP_AGG_GEOM__BOX_0_SPHERE_0_SPHYL_0_TAPERED_0_CONVEX_3'
    import_receipt_sha256=Get-Sha256 $ImportReceipt; validation_receipt_sha256=Get-Sha256 $ValidationReceipt
    protected_existing_content_config_savegames_unchanged=$true
    logs=[ordered]@{import=Get-Relative $importLog;validation=Get-Relative $validationLog}
}
$summary|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $run 'run_summary_v002.json') -Encoding utf8
Write-Host 'PASS: original procedural spray booth v002 imported and independently validated.'
