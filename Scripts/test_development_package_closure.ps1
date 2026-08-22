param(
    [Parameter(Mandatory = $true)]
    [string]$PackageRoot,

    # Development builds intentionally carry the current revisionable Cairnwell
    # authority. A release candidate must prove it has been replaced.
    [switch]$ReleaseCandidate
)

# This is a cooked-package closure guard, not a provenance certificate.  It
# blocks known legacy/external package names and proves required live bindings
# are present; source-asset provenance remains a separate release gate.

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $PackageRoot).Path
$manifest = Join-Path $root 'Manifest_UFSFiles_Win64.txt'
if (-not (Test-Path -LiteralPath $manifest)) {
    throw "Missing UFS manifest: $manifest"
}

$entries = Get-Content -LiteralPath $manifest
$forbidden = @(
    'PhysicalSigns_v397',
    'PhysicalSigns_v411',
    'Meshy',
    'UserMeshy',
    'ExternalGenerated',
    'LB_WeldRobot_SharedBase_LOD0_v001',
    # The imported full-car authority is not the active development WIP
    # presentation. It stays in source evidence until replaced by a
    # clean-room production vehicle authority.
    'Cairnwell2040Runtime_v001'
    # The imported full-car authority is intentionally excluded above. The
    # separately promoted panel set is the active press/body WIP authority;
    # it is required below and must not be confused with that retired car.
)
$mode = if ($ReleaseCandidate) { 'release-candidate' } else { 'development' }
if ($ReleaseCandidate) {
    $forbidden += @(
        'VehicleWIPNativeKit_v001',
        # Candidate roots are development/source lanes, not a release
        # provenance authority. A release candidate must replace them with
        # explicitly approved production roots before it can pass.
        '/Candidates/',
        '/Candidate_'
    )
}
$required = @(
    'ScanKit_v001',
    'VehicleWIPNativeKit_v001',
    'Cairnwell2040PanelModules_v001'
)
$permittedDevelopmentRuntimeClosure = @(
    # These are the only retained dependencies from the revisionable runtime
    # source: the active WIP panel material and its three packed textures.
    # Retired full-car meshes must remain absent.
    'Cairnwell2040Runtime_v001/Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_BaseColor_v001.uasset',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_BaseColor_v001.ubulk',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_MRBodyMask_v001.uasset',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_MRBodyMask_v001.ubulk',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_Normal_v001.uasset',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_Normal_v001.ubulk'
)
if ($ReleaseCandidate) {
    # A release authority will have its own required root. This guard only
    # establishes that the development-only roots are absent.
    $required = @('ScanKit_v001')
}

$forbiddenHits = @{}
foreach ($token in $forbidden) {
    $hits = @($entries | Where-Object { $_ -match [regex]::Escape($token) })
    if ($token -eq 'Cairnwell2040Runtime_v001' -and -not $ReleaseCandidate) {
        $hits = @($hits | Where-Object {
            $entry = $_
            -not (@($permittedDevelopmentRuntimeClosure | Where-Object { $entry -match [regex]::Escape($_) }).Count -gt 0)
        })
    }
    if ($hits.Count -gt 0) { $forbiddenHits[$token] = $hits }
}
$missingRequired = @()
foreach ($token in $required) {
    if (@($entries | Where-Object { $_ -match [regex]::Escape($token) }).Count -eq 0) {
        $missingRequired += $token
    }
}
$containers = @(Get-ChildItem -LiteralPath $root -Recurse -File |
    Where-Object { $_.Extension -in '.pak', '.ucas', '.utoc' })

$result = [ordered]@{
    package_root = $root
    mode = $mode
    manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifest).Hash
    manifest_entries = $entries.Count
    container_count = $containers.Count
    forbidden_hits = $forbiddenHits
    missing_required = $missingRequired
    status = if ($forbiddenHits.Count -eq 0 -and $missingRequired.Count -eq 0 -and $containers.Count -gt 0) { 'PASS' } else { 'FAIL' }
}
$result | ConvertTo-Json -Depth 6
if ($result.status -ne 'PASS') { exit 1 }
