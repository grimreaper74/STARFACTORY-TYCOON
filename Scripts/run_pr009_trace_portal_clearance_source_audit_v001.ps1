$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$package = Join-Path $root 'SourceAssets\PR009\AutomatedBlankStacker\TracePortalClearance_v001'
$audit = Join-Path $root 'Saved\Audits\PR009_TracePortalClearance_v001'
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$inventory = Join-Path $root 'Scripts\audit_pr009_trace_portal_clearance_blender_v001.py'
$consolidate = Join-Path $root 'Scripts\consolidate_pr009_trace_portal_clearance_source_audit_v001.py'
New-Item -ItemType Directory -Force -Path $audit | Out-Null

$blend = Join-Path $package 'PR009_Source\CA_MW_PR009_TracePortalClearance_ProductionSource_v001.blend'
$fbx = Join-Path $package 'PR009_Exports\SM_CA_MW_PR009_TracePortal_Clearance_01_v001.fbx'

# --disable-autoexec is mandatory: this is a read-only audit and embedded scripts must not run.
& $blender --background --disable-autoexec $blend --python $inventory -- `
    --mode source --output (Join-Path $audit 'blender_source_inventory.json') `
    *> (Join-Path $audit 'blender_source_inventory.log')
if ($LASTEXITCODE -ne 0) { throw "Blender source inventory failed: $LASTEXITCODE" }

& $blender --background --factory-startup --disable-autoexec --python $inventory -- `
    --mode fbx --input $fbx --output (Join-Path $audit 'fbx_roundtrip_inventory.json') `
    *> (Join-Path $audit 'fbx_roundtrip_inventory.log')
if ($LASTEXITCODE -ne 0) { throw "FBX round-trip inventory failed: $LASTEXITCODE" }

Push-Location $root
try { python $consolidate }
finally { Pop-Location }
