$ErrorActionPreference = 'Stop'

# Completes the audit record for the recoverable move that occurred before the
# original quarantine script's reporting bug.  It does not mutate Content.
$Project = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$AuditRoot = Join-Path $Project 'Saved\Audits\BodyShop\Experimental_v001'
$FailureReceipt = Join-Path $AuditRoot 'import_underbody_slice_art_failure_v001.json'
$Quarantine = Join-Path $AuditRoot 'RejectedArtifacts\BodyShopUnderbodySlice_v001_legacy_import_failure_20260813T171502Z'
$MovedRoot = Join-Path $Quarantine 'BodyShopUnderbodySlice_v001'
$ExpectedContentRoot = Join-Path $Project 'Content\LineBoss\Candidates\WeldShop\BodyShopUnderbodySlice_v001'

if (Get-Process UnrealEditor, UnrealEditor-Cmd -ErrorAction SilentlyContinue) { throw 'Refusing audit mutation while Unreal is running' }
if (Test-Path -LiteralPath $ExpectedContentRoot) { throw 'Target Content namespace unexpectedly exists; no receipt written' }
if (-not (Test-Path -LiteralPath $FailureReceipt -PathType Leaf)) { throw 'Missing fail-closed import receipt' }
if (-not (Test-Path -LiteralPath $MovedRoot -PathType Container)) { throw 'Missing quarantined artifact root' }
$failure = Get-Content -LiteralPath $FailureReceipt -Raw | ConvertFrom-Json
if ([string]$failure.status -notlike 'FAIL*') { throw 'Prior import receipt is not fail-closed' }
$expected = $failure.namespace_files_preserved_for_inspection
$actual = @(Get-ChildItem -LiteralPath $MovedRoot -Recurse -File | Sort-Object FullName | ForEach-Object {
    $rel = 'LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/' + $_.FullName.Substring($MovedRoot.Length + 1).Replace('\', '/')
    [pscustomobject]@{ path = $rel; bytes = [int64]$_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
})
if ($actual.Count -ne @($expected.PSObject.Properties).Count) { throw "File-count mismatch: $($actual.Count)" }
foreach ($row in $actual) {
    $expectedRow = $expected.PSObject.Properties[$row.path].Value
    if ($null -eq $expectedRow -or [int64]$expectedRow.bytes -ne $row.bytes -or [string]$expectedRow.sha256 -ne $row.sha256) { throw "Hash/size mismatch: $($row.path)" }
}
$receiptPath = Join-Path $Quarantine 'quarantine_receipt_v001.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Receipt already exists; refusing overwrite' }
$receipt = [ordered]@{
    schema = 'lineboss/audit/bodyshop/experimental-v001-underbody-art-failed-import-quarantine/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'PASS__RECOVERABLY_QUARANTINED_FAILED_LEGACY_IMPORT_NAMESPACE_V001'
    recovery_note = 'The guarded Move-Item completed before a reporting-only Measure-Object bug; this receipt was completed after exact hash/byte reconciliation against the fail-closed import receipt.'
    action = 'Prior action: Move-Item within project volume; no deletion or overwrite performed.'
    source_namespace_before = '/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001'
    source_absent_after_move = $true
    failed_import_receipt = $FailureReceipt
    failed_import_receipt_sha256 = (Get-FileHash -LiteralPath $FailureReceipt -Algorithm SHA256).Hash
    quarantine_directory = $Quarantine
    quarantined_disk_path = $MovedRoot
    file_count = $actual.Count
    total_bytes = [int64](($actual | Measure-Object -Property bytes -Sum).Sum)
    sha256_inventory = $actual
    no_source_config_map_or_legacy_changes = $true
    unreal_launched_by_this_script = $false
    meshy_credits_used_by_codex = 0
}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8
$receipt | ConvertTo-Json -Depth 8
