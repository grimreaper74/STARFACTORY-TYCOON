[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$PackageRoot,

    # An optional JSON report is useful in CI and leaves the package itself untouched.
    [string]$ReportPath,

    # A release candidate must not inherit development-only candidate roots.
    [switch]$ReleaseCandidate
)

$ErrorActionPreference = 'Stop'

$resolvedRoot = (Resolve-Path -LiteralPath $PackageRoot).Path
$manifest = Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File -Filter 'Manifest_UFSFiles_Win64.txt' | Select-Object -First 1
if ($null -eq $manifest) {
    throw "No Windows UFS manifest exists under '$resolvedRoot'."
}

$forbiddenTokens = @(
    'PhysicalSigns_v397',
    'PhysicalSigns_v411',
    'Meshy',
    'UserMeshy',
    'ExternalGenerated',
    'LB_WeldRobot_SharedBase_LOD0_v001',
    'Cairnwell2040Runtime_v001'
)

$mode = if ($ReleaseCandidate) { 'release-candidate' } else { 'development' }
if ($ReleaseCandidate) {
    $forbiddenTokens += @('VehicleWIPNativeKit_v001', '/Candidates/', '/Candidate_')
}

$requiredTokens = @(
    'ScanKit_v001',
    'VehicleWIPNativeKit_v001',
    'Cairnwell2040PanelModules_v001'
)
if ($ReleaseCandidate) { $requiredTokens = @('ScanKit_v001') }

# These materials and textures are still the declared dependency closure of
# the native development WIP kit.  Its retired runtime meshes are forbidden.
$permittedDevelopmentRuntimeClosure = @(
    'Cairnwell2040Runtime_v001/Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_BaseColor_v001.uasset',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_BaseColor_v001.ubulk',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_MRBodyMask_v001.uasset',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_MRBodyMask_v001.ubulk',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_Normal_v001.uasset',
    'Cairnwell2040Runtime_v001/Textures/T_LB_C2040_Emerald_Normal_v001.ubulk'
)

$lines = Get-Content -LiteralPath $manifest.FullName
$violations = [System.Collections.Generic.List[object]]::new()
foreach ($token in $forbiddenTokens) {
    foreach ($line in $lines) {
        if ($token -eq 'Cairnwell2040Runtime_v001' -and -not $ReleaseCandidate -and
            $null -ne ($permittedDevelopmentRuntimeClosure | Where-Object {
                $line.IndexOf($_, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
            } | Select-Object -First 1)) {
            continue
        }
        if ($line.IndexOf($token, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            $violations.Add([pscustomobject]@{
                Token = $token
                ManifestEntry = $line
            })
        }
    }
}

$missingRequired = [System.Collections.Generic.List[string]]::new()
foreach ($requiredToken in $requiredTokens) {
    $found = $false
    foreach ($line in $lines) {
        if ($line.IndexOf($requiredToken, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            $found = $true
            break
        }
    }
    if (-not $found) { $missingRequired.Add($requiredToken) }
}
$containers = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File |
    Where-Object { $_.Extension -in '.pak', '.ucas', '.utoc' })

$report = [ordered]@{
    Status = if ($violations.Count -eq 0 -and $missingRequired.Count -eq 0 -and $containers.Count -gt 0) {
        'PASS__LINE_BOSS_DEVELOPMENT_PACKAGE_CLEANROOM_MANIFEST'
    } else {
        'FAIL__LINE_BOSS_DEVELOPMENT_PACKAGE_CLEANROOM_MANIFEST'
    }
    PackageRoot = $resolvedRoot
    Mode = $mode
    Manifest = $manifest.FullName
    ManifestEntries = $lines.Count
    ForbiddenTokens = $forbiddenTokens
    RequiredTokens = $requiredTokens
    Violations = @($violations)
    MissingRequired = $missingRequired
    ContainerCount = $containers.Count
}

if (-not [string]::IsNullOrWhiteSpace($ReportPath)) {
    $parent = Split-Path -Parent $ReportPath
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        [System.IO.Directory]::CreateDirectory($parent) | Out-Null
    }
    $report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ReportPath -Encoding utf8
}

if ($violations.Count -gt 0 -or $missingRequired.Count -gt 0 -or $containers.Count -eq 0) {
    $violations | ForEach-Object { Write-Error "Forbidden cooked payload [$($_.Token)]: $($_.ManifestEntry)" }
    $missingRequired | ForEach-Object { Write-Error "Required cooked payload is missing: $_" }
    if ($containers.Count -eq 0) { Write-Error 'No staged .pak, .ucas or .utoc container exists.' }
    throw "Clean-room package verification failed with $($violations.Count) forbidden entries and $($missingRequired.Count) missing required payloads."
}

[pscustomobject]$report
