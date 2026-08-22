[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),

    [string]$ReportPath
)

$ErrorActionPreference = 'Stop'

$resolvedProject = (Resolve-Path -LiteralPath $ProjectRoot).Path
$configPath = Join-Path $resolvedProject 'Config\DefaultGame.ini'
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "Missing packaging configuration: $configPath"
}

$configContents = Get-Content -LiteralPath $configPath -Raw
$rootMatches = [regex]::Matches(
    $configContents,
    '\+DirectoriesToAlwaysCook=\(Path="(?<path>[^"]+)"\)')
$roots = @($rootMatches | ForEach-Object { $_.Groups['path'].Value } |
    Select-Object -Unique)

$sourceRoot = Join-Path $resolvedProject 'Source'
$sourceFiles = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File |
    Where-Object { $_.Extension -in '.h', '.cpp', '.cs' })
$sourceText = @{}
foreach ($file in $sourceFiles) {
    $sourceText[$file.FullName] = Get-Content -LiteralPath $file.FullName -Raw
}

$rows = foreach ($root in $roots) {
    $references = [System.Collections.Generic.List[string]]::new()
    foreach ($file in $sourceFiles) {
        if ($sourceText[$file.FullName].IndexOf($root,
                [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            $references.Add($file.FullName.Substring($resolvedProject.Length + 1))
        }
    }

    $classification = if ($root.StartsWith('/Game/LineBoss/Candidates/',
            [System.StringComparison]::OrdinalIgnoreCase)) {
        'candidate-root'
    } elseif ($root.StartsWith('/Game/LineBoss/Vendor/',
            [System.StringComparison]::OrdinalIgnoreCase)) {
        'vendor-root'
    } elseif ($root.StartsWith('/Engine/',
            [System.StringComparison]::OrdinalIgnoreCase)) {
        'engine-root'
    } else {
        'owned-or-native-root'
    }

    [pscustomobject]@{
        cook_root = $root
        classification = $classification
        direct_source_reference_count = $references.Count
        direct_source_references = @($references | Sort-Object)
        disposition = if ($references.Count -gt 0) {
            'MAP_BEFORE_NARROWING'
        } else {
            'NO_DIRECT_SOURCE_REFERENCE__VERIFY_ASSET_DEPENDENCIES_BEFORE_REMOVAL'
        }
    }
}

$report = [ordered]@{
    status = 'PASS__LINE_BOSS_DEVELOPMENT_COOK_ROOT_AUDIT'
    project_root = $resolvedProject
    config = 'Config/DefaultGame.ini'
    always_cook_root_count = $roots.Count
    roots = @($rows)
}

if (-not [string]::IsNullOrWhiteSpace($ReportPath)) {
    $parent = Split-Path -Parent $ReportPath
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        [System.IO.Directory]::CreateDirectory($parent) | Out-Null
    }
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReportPath -Encoding utf8
}

[pscustomobject]$report
