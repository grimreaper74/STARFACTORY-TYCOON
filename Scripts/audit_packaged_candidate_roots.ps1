[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$PackageRoot,

    [string]$ReportPath,

    # -1 is inventory-only.  A non-negative value makes the audit a ratchet:
    # new unclassified roots fail, while each migration can lower the baseline.
    [int]$MaxUnclassifiedRoots = -1
)

$ErrorActionPreference = 'Stop'

$root = (Resolve-Path -LiteralPath $PackageRoot).Path
$utoc = Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.utoc' |
    Where-Object { $_.Name -match '^LineBossCarFactory-.*\.utoc$' } |
    Select-Object -First 1
if ($null -eq $utoc) { throw "No IoStore .utoc was found under '$root'." }

$unrealPak = Join-Path $env:ProgramFiles 'Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealPak.exe'
if (-not (Test-Path -LiteralPath $unrealPak)) {
    throw "UnrealPak was not found at '$unrealPak'."
}

$configPath = Join-Path (Split-Path -Parent (Split-Path -Parent $root)) 'Config\DefaultGame.ini'
if (-not (Test-Path -LiteralPath $configPath)) {
    # Packaged output may be outside the project, so accept a sibling project
    # config only when the package cannot tell us its source project.
    $configPath = Join-Path (Get-Location) 'Config\DefaultGame.ini'
}
$alwaysCook = @()
if (Test-Path -LiteralPath $configPath) {
    $alwaysCook = @(Get-Content -LiteralPath $configPath |
        ForEach-Object {
            if ($_ -match '^\+DirectoriesToAlwaysCook=\(Path="(?<path>/Game/LineBoss/Candidates/[^"]+)"\)') {
                $Matches['path'].TrimEnd('/')
            }
        })
}

# Hard references in native code are intentional runtime dependencies until
# their assets are migrated.  Treat them differently from a package-only
# dependency: that distinction makes this audit safe to use as a migration
# queue rather than encouraging blind NeverCook edits.
$sourceReferences = @()
$sourceRoot = Join-Path (Get-Location) 'Source'
if (Test-Path -LiteralPath $sourceRoot) {
    $sourceReferences = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File |
        Where-Object { $_.Extension -in '.cpp', '.h' } |
        ForEach-Object {
            $content = Get-Content -LiteralPath $_.FullName -Raw
            [regex]::Matches($content, '/Game/LineBoss/Candidates/[^"''\s]+') |
                ForEach-Object { $_.Value.TrimEnd('.', ')', '"', '''') }
        } | Sort-Object -Unique)
}

$listing = & $unrealPak $utoc.FullName -List 2>&1
if ($LASTEXITCODE -ne 0) { throw "UnrealPak could not list '$($utoc.FullName)'." }

$entries = [System.Collections.Generic.List[string]]::new()
foreach ($line in $listing) {
    if ($line -match '(?:\.\./)+LineBossCarFactory/Content/(?<path>LineBoss/Candidates/[^"\s]+)') {
        $entries.Add($Matches['path'])
    }
}

$groups = $entries | Group-Object {
    $parts = $_ -split '/'
    if ($parts.Count -ge 4) { ($parts[0..3] -join '/') } else { $_ }
} | Sort-Object Count -Descending | ForEach-Object {
    $relativeRoot = $_.Name
    $gameRoot = '/Game/' + $relativeRoot
    $declared = @($alwaysCook | Where-Object {
        $gameRoot.StartsWith($_, [System.StringComparison]::OrdinalIgnoreCase)
    })
    $nativeReferences = @($sourceReferences | Where-Object {
        $_.StartsWith($gameRoot, [System.StringComparison]::OrdinalIgnoreCase)
    })
    [pscustomobject]@{
        CandidateRoot = $gameRoot
        CookedEntries = $_.Count
        Classification = if ($declared.Count -gt 0) {
            'declared-always-cook'
        } elseif ($nativeReferences.Count -gt 0) {
            'hard-referenced-native-code'
        } else {
            'transitive-or-unclassified'
        }
        MatchingAlwaysCookRoots = $declared
        NativeReferenceCount = $nativeReferences.Count
        NativeReferenceSamples = @($nativeReferences | Select-Object -First 3)
    }
}

$report = [ordered]@{
    Status = 'INVENTORY__REVIEW_REQUIRED'
    PackageRoot = $root
    Utoc = $utoc.FullName
    CandidateEntryCount = $entries.Count
    CandidateRootCount = @($groups).Count
    DeclaredAlwaysCookRoots = $alwaysCook
    NativeCandidateReferenceCount = $sourceReferences.Count
    Roots = @($groups)
}

$unclassifiedRoots = @($groups | Where-Object {
    $_.Classification -eq 'transitive-or-unclassified'
})
$report.UnclassifiedRootCount = $unclassifiedRoots.Count
$report.MaxUnclassifiedRoots = $MaxUnclassifiedRoots
if ($MaxUnclassifiedRoots -ge 0) {
    $report.Status = if ($unclassifiedRoots.Count -le $MaxUnclassifiedRoots) {
        'PASS__CANDIDATE_ROOT_RATCHET'
    } else {
        'FAIL__CANDIDATE_ROOT_RATCHET'
    }
}

if (-not [string]::IsNullOrWhiteSpace($ReportPath)) {
    $parent = Split-Path -Parent $ReportPath
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        [System.IO.Directory]::CreateDirectory($parent) | Out-Null
    }
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReportPath -Encoding utf8
}

if ($MaxUnclassifiedRoots -ge 0 -and
    $unclassifiedRoots.Count -gt $MaxUnclassifiedRoots) {
    throw "Candidate-root ratchet failed: $($unclassifiedRoots.Count) unclassified roots exceed maximum $MaxUnclassifiedRoots."
}

[pscustomobject]$report
