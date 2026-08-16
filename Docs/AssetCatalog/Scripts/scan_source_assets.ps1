[CmdletBinding()]
param(
    [ValidateSet('Scan', 'Validate')]
    [string]$Mode = 'Scan',
    [switch]$FullHashValidation,
    [string]$ProjectRoot,
    [string]$LedgerPath,
    [int]$CheckpointEvery = 100
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
}
$sourceRoot = Join-Path $ProjectRoot 'SourceAssets'
$catalogRoot = Join-Path $ProjectRoot 'Docs\AssetCatalog'
if ([string]::IsNullOrWhiteSpace($LedgerPath)) {
    $LedgerPath = Join-Path $catalogRoot 'sourceassets_file_ledger.jsonl'
}
$csvPath = Join-Path $catalogRoot 'sourceassets_file_ledger.csv'
$summaryPath = Join-Path $catalogRoot 'sourceassets_file_ledger_summary.json'
$checkpointPath = Join-Path $catalogRoot 'sourceassets_file_ledger.checkpoint.jsonl'
$checkpointStatePath = Join-Path $catalogRoot 'sourceassets_file_ledger.checkpoint.state.json'
$manifestIndexJson = Join-Path $catalogRoot 'sourceassets_manifest_index.json'
$manifestIndexCsv = Join-Path $catalogRoot 'sourceassets_manifest_index.csv'
$duplicateIndexJson = Join-Path $catalogRoot 'sourceassets_duplicate_hash_groups.json'
$duplicateIndexCsv = Join-Path $catalogRoot 'sourceassets_duplicate_hash_groups.csv'
$validationResultPath = Join-Path $catalogRoot $(if ($FullHashValidation) { 'sourceassets_validation_result_full.json' } else { 'sourceassets_validation_result.json' })
$curatedCatalogPath = Join-Path $catalogRoot 'master_asset_catalog.json'

if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    throw "SourceAssets root not found: $sourceRoot"
}
New-Item -ItemType Directory -Path $catalogRoot -Force | Out-Null

function Get-RelativePathNormalized {
    param([string]$Base, [string]$Path)
    $normalizedBase = [System.IO.Path]::GetFullPath($Base).TrimEnd('\') + '\'
    $normalizedPath = [System.IO.Path]::GetFullPath($Path)
    $baseUri = [System.Uri]::new($normalizedBase)
    $pathUri = [System.Uri]::new($normalizedPath)
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace('\', '/')
}

function Read-JsonlIndex {
    param([string]$Path)
    $index = @{}
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $index }
    foreach ($line in [System.IO.File]::ReadLines($Path)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $record = $line | ConvertFrom-Json
            if ($record.relative_path) { $index[[string]$record.relative_path] = $record }
        }
        catch {
            Write-Warning "Ignored malformed JSONL record in ${Path}: $($_.Exception.Message)"
        }
    }
    return $index
}

function Write-JsonlAtomic {
    param([object[]]$Records, [string]$Path)
    $tempPath = "$Path.tmp"
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    $writer = [System.IO.StreamWriter]::new($tempPath, $false, $utf8NoBom)
    try {
        foreach ($record in $Records) {
            $writer.WriteLine(($record | ConvertTo-Json -Compress -Depth 8))
        }
    }
    finally { $writer.Dispose() }
    Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

function Find-NearestManifestFolder {
    param([string]$FileDirectory, [hashtable]$ManifestDirectories)
    $cursor = [System.IO.DirectoryInfo]::new($FileDirectory)
    while ($null -ne $cursor -and $cursor.FullName.StartsWith($sourceRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        if ($ManifestDirectories.ContainsKey($cursor.FullName)) {
            return Get-RelativePathNormalized -Base $sourceRoot -Path $cursor.FullName
        }
        $cursor = $cursor.Parent
    }
    return $null
}

$manifestFiles = Get-ChildItem -LiteralPath $sourceRoot -File -Recurse | Where-Object {
    $_.Extension -ieq '.json' -and $_.Name -match '(?i)manifest'
} | Sort-Object FullName
$manifestDirectories = @{}
foreach ($manifest in $manifestFiles) { $manifestDirectories[$manifest.Directory.FullName] = $true }

$manifestRecords = foreach ($manifest in $manifestFiles) {
    [pscustomobject][ordered]@{
        relative_path = Get-RelativePathNormalized -Base $sourceRoot -Path $manifest.FullName
        folder = Get-RelativePathNormalized -Base $sourceRoot -Path $manifest.Directory.FullName
        bytes = [int64]$manifest.Length
        last_write_utc = $manifest.LastWriteTimeUtc.ToString('o')
        sha256 = (Get-FileHash -LiteralPath $manifest.FullName -Algorithm SHA256).Hash
    }
}
$manifestIndex = [ordered]@{
    schema = 'lineboss.sourceassets.manifest-index.v1'
    generated_utc = [DateTime]::UtcNow.ToString('o')
    source_root = $sourceRoot
    manifest_count = @($manifestRecords).Count
    manifests = @($manifestRecords)
}
[System.IO.File]::WriteAllText($manifestIndexJson, (($manifestIndex | ConvertTo-Json -Depth 6) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
$manifestRecords | Export-Csv -LiteralPath $manifestIndexCsv -NoTypeInformation -Encoding utf8

if ($Mode -eq 'Scan') {
    $existing = Read-JsonlIndex -Path $LedgerPath
    $resumeCount = 0
    if ($existing.Count -eq 0 -and (Test-Path -LiteralPath $checkpointPath -PathType Leaf)) {
        $existing = Read-JsonlIndex -Path $checkpointPath
        if (Test-Path -LiteralPath $checkpointStatePath -PathType Leaf) {
            try { $resumeCount = [int](Get-Content -Raw -LiteralPath $checkpointStatePath | ConvertFrom-Json).record_count }
            catch { $resumeCount = 0 }
        }
        if ($resumeCount -le 0) { $resumeCount = $existing.Count }
    }
    $files = Get-ChildItem -LiteralPath $sourceRoot -File -Recurse | Sort-Object @{ Expression = { Get-RelativePathNormalized -Base $sourceRoot -Path $_.FullName } }
    $records = [System.Collections.Generic.List[object]]::new()
    $reused = 0
    $hashed = 0
    if ($resumeCount -gt 0) {
        foreach ($file in $files | Select-Object -First $resumeCount) {
            $relative = Get-RelativePathNormalized -Base $sourceRoot -Path $file.FullName
            if ($existing.ContainsKey($relative)) { $records.Add($existing[$relative]); $reused++ }
        }
        if ($records.Count -ne $resumeCount) {
            throw "Checkpoint cannot be resumed safely: expected $resumeCount ordered records but recovered $($records.Count)."
        }
    }
    foreach ($file in $files | Select-Object -Skip $resumeCount) {
        $relative = Get-RelativePathNormalized -Base $sourceRoot -Path $file.FullName
        $timestamp = $file.LastWriteTimeUtc.ToString('o')
        $prior = $existing[$relative]
        $hash = $null
        if ($null -ne $prior -and [int64]$prior.bytes -eq [int64]$file.Length -and [string]$prior.last_write_utc -eq $timestamp -and [string]$prior.sha256 -match '^[A-Fa-f0-9]{64}$') {
            $hash = ([string]$prior.sha256).ToUpperInvariant()
            $reused++
        }
        else {
            $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
            $hashed++
        }
        $records.Add([pscustomobject][ordered]@{
            relative_path = $relative
            bytes = [int64]$file.Length
            last_write_utc = $timestamp
            sha256 = $hash
            extension = $file.Extension.ToLowerInvariant()
            nearest_manifest_folder = Find-NearestManifestFolder -FileDirectory $file.Directory.FullName -ManifestDirectories $manifestDirectories
        })
        if ($CheckpointEvery -gt 0 -and ($records.Count % $CheckpointEvery) -eq 0) {
            Write-JsonlAtomic -Records $records.ToArray() -Path $checkpointPath
            [System.IO.File]::WriteAllText($checkpointStatePath, (([ordered]@{
                schema = 'lineboss.sourceassets.file-ledger-checkpoint.v1'
                source_root = $sourceRoot
                record_count = $records.Count
                total_file_count = $files.Count
                updated_utc = [DateTime]::UtcNow.ToString('o')
            } | ConvertTo-Json -Depth 4) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
            Write-Progress -Activity 'Hashing SourceAssets' -Status "$($records.Count) / $($files.Count)" -PercentComplete (($records.Count / [Math]::Max(1, $files.Count)) * 100)
        }
    }
    Write-JsonlAtomic -Records $records.ToArray() -Path $LedgerPath
    $records | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding utf8
    if (Test-Path -LiteralPath $checkpointPath) { Remove-Item -LiteralPath $checkpointPath -Force }
    if (Test-Path -LiteralPath $checkpointStatePath) { Remove-Item -LiteralPath $checkpointStatePath -Force }
    $duplicateGroups = @($records | Group-Object sha256 | Where-Object Count -gt 1 | Sort-Object Name)
    $duplicateRecords = @(
        foreach ($group in $duplicateGroups) {
            $orderedGroup = @($group.Group | Sort-Object relative_path)
            $bytesPerCopy = [int64]$orderedGroup[0].bytes
            [pscustomobject][ordered]@{
                sha256 = [string]$group.Name
                file_count = [int]$group.Count
                bytes_per_copy = $bytesPerCopy
                total_bytes_all_copies = [int64]($bytesPerCopy * [int64]$group.Count)
                potential_duplicate_bytes_beyond_one_copy = [int64]($bytesPerCopy * [int64]($group.Count - 1))
                relative_paths = @($orderedGroup | ForEach-Object { [string]$_.relative_path })
            }
        }
    )
    $duplicateIndex = [ordered]@{
        schema = 'lineboss.sourceassets.duplicate-hash-index.v1'
        generated_utc = [DateTime]::UtcNow.ToString('o')
        source_root = $sourceRoot
        duplicate_hash_group_count = $duplicateRecords.Count
        duplicate_file_count = [int](($duplicateRecords | ForEach-Object { $_.file_count } | Measure-Object -Sum).Sum)
        duplicate_extra_copy_count = [int](($duplicateRecords | ForEach-Object { $_.file_count - 1 } | Measure-Object -Sum).Sum)
        potential_duplicate_bytes_beyond_one_copy = [int64](($duplicateRecords | ForEach-Object { [decimal]$_.potential_duplicate_bytes_beyond_one_copy } | Measure-Object -Sum).Sum)
        groups = $duplicateRecords
    }
    [System.IO.File]::WriteAllText($duplicateIndexJson, (($duplicateIndex | ConvertTo-Json -Depth 8) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
    $duplicateCsvRows = @(
        foreach ($group in $duplicateRecords) {
            foreach ($relativePath in $group.relative_paths) {
                [pscustomobject][ordered]@{
                    sha256 = $group.sha256
                    group_file_count = $group.file_count
                    bytes_per_copy = $group.bytes_per_copy
                    potential_duplicate_bytes_beyond_one_copy = $group.potential_duplicate_bytes_beyond_one_copy
                    relative_path = $relativePath
                }
            }
        }
    )
    $duplicateCsvRows | Export-Csv -LiteralPath $duplicateIndexCsv -NoTypeInformation -Encoding utf8
    $summary = [ordered]@{
        schema = 'lineboss.sourceassets.file-ledger-summary.v1'
        generated_utc = [DateTime]::UtcNow.ToString('o')
        source_root = $sourceRoot
        file_count = $records.Count
        total_bytes = [int64](($records | ForEach-Object { [decimal]$_.bytes } | Measure-Object -Sum).Sum)
        hashes_reused = $reused
        hashes_computed = $hashed
        duplicate_hash_group_count = $duplicateRecords.Count
        duplicate_file_count = $duplicateIndex.duplicate_file_count
        duplicate_extra_copy_count = $duplicateIndex.duplicate_extra_copy_count
        potential_duplicate_bytes_beyond_one_copy = $duplicateIndex.potential_duplicate_bytes_beyond_one_copy
        ledger_sha256 = (Get-FileHash -LiteralPath $LedgerPath -Algorithm SHA256).Hash
        csv_sha256 = (Get-FileHash -LiteralPath $csvPath -Algorithm SHA256).Hash
    }
    [System.IO.File]::WriteAllText($summaryPath, (($summary | ConvertTo-Json -Depth 5) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
    $summary | ConvertTo-Json -Depth 5
    exit 0
}

$ledger = Read-JsonlIndex -Path $LedgerPath
if ($ledger.Count -eq 0) { throw "Ledger is empty or missing: $LedgerPath" }
$currentFiles = Get-ChildItem -LiteralPath $sourceRoot -File -Recurse | Sort-Object @{ Expression = { Get-RelativePathNormalized -Base $sourceRoot -Path $_.FullName } }
$currentIndex = @{}
$errors = [System.Collections.Generic.List[string]]::new()
foreach ($file in $currentFiles) {
    $relative = Get-RelativePathNormalized -Base $sourceRoot -Path $file.FullName
    $currentIndex[$relative] = $true
    $record = $ledger[$relative]
    if ($null -eq $record) { $errors.Add("UNTRACKED: $relative"); continue }
    if ([int64]$record.bytes -ne [int64]$file.Length) { $errors.Add("SIZE_MISMATCH: $relative") }
    if ([string]$record.last_write_utc -ne $file.LastWriteTimeUtc.ToString('o')) { $errors.Add("TIMESTAMP_MISMATCH: $relative") }
    if ($FullHashValidation) {
        $actual = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        if ($actual -ne [string]$record.sha256) { $errors.Add("HASH_MISMATCH: $relative") }
    }
}
foreach ($relative in $ledger.Keys) {
    if (-not $currentIndex.ContainsKey($relative)) { $errors.Add("MISSING: $relative") }
}

if (Test-Path -LiteralPath $curatedCatalogPath) {
    $catalog = Get-Content -Raw -LiteralPath $curatedCatalogPath | ConvertFrom-Json
    foreach ($family in $catalog.families) {
        foreach ($source in @($family.source_files)) {
            $candidatePath = $null
            if ($source.intake_relative_path) { $candidatePath = Join-Path $ProjectRoot ([string]$source.intake_relative_path) }
            elseif ($source.path -and [System.IO.Path]::IsPathRooted([string]$source.path)) { $candidatePath = [string]$source.path }
            if ($candidatePath -and -not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
                $errors.Add("CURATED_SOURCE_MISSING: $($family.asset_id) :: $candidatePath")
            }
            elseif ($candidatePath -and $source.sha256) {
                $actual = (Get-FileHash -LiteralPath $candidatePath -Algorithm SHA256).Hash
                if ($actual -ne [string]$source.sha256) { $errors.Add("CURATED_HASH_MISMATCH: $($family.asset_id) :: $candidatePath") }
            }
        }
        foreach ($pathField in @('manifest_relative_path', 'audit_relative_path', 'best_authority_relative_path')) {
            $value = $family.$pathField
            if ($value -and -not (Test-Path -LiteralPath (Join-Path $ProjectRoot ([string]$value)))) {
                $errors.Add("CURATED_PATH_MISSING: $($family.asset_id) :: $pathField :: $value")
            }
        }
    }
}

$result = [ordered]@{
    schema = 'lineboss.sourceassets.validation-result.v1'
    checked_utc = [DateTime]::UtcNow.ToString('o')
    full_hash_validation = [bool]$FullHashValidation
    ledger_file_count = $ledger.Count
    current_file_count = $currentFiles.Count
    error_count = $errors.Count
    status = if ($errors.Count -eq 0) { 'PASS' } else { 'FAIL' }
    errors = $errors
}
$resultJson = ($result | ConvertTo-Json -Depth 6) + [Environment]::NewLine
[System.IO.File]::WriteAllText($validationResultPath, $resultJson, [System.Text.UTF8Encoding]::new($false))
$resultJson
if ($errors.Count -gt 0) { exit 1 }
