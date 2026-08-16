$ErrorActionPreference = 'Stop'

# Recoverably moves only the failed isolated Body Shop v001 import namespace.
# It must be executed after Unreal exits.  It deletes or overwrites nothing.
$Project = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Source = Join-Path $Project 'Content\LineBoss\Candidates\WeldShop\BodyShopUnderbodySlice_v001'
$AuditRoot = Join-Path $Project 'Saved\Audits\BodyShop\Experimental_v001'
$FailureReceipt = Join-Path $AuditRoot 'import_underbody_slice_art_failure_v001.json'
$RejectedRoot = Join-Path $AuditRoot 'RejectedArtifacts'
$Expected = @(
    'Fixture/SM_LB_BodyShop_UnderbodyFixture_v001.uasset',
    'Robot/SM_LB_BodyShopRobot_Base_v001.uasset',
    'Robot/SM_LB_BodyShopRobot_J1_v001.uasset',
    'Robot/SM_LB_BodyShopRobot_J2_v001.uasset',
    'Robot/SM_LB_BodyShopRobot_J3_v001.uasset',
    'Robot/SM_LB_BodyShopRobot_J4_v001.uasset',
    'Robot/SM_LB_BodyShopRobot_J5_v001.uasset',
    'Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.uasset',
    'Vision/SM_LB_BodyShop_VisionGate_v001.uasset'
)

function Get-Inventory([string]$Base) {
    @(Get-ChildItem -LiteralPath $Base -Recurse -File | Sort-Object FullName | ForEach-Object {
        [pscustomobject]@{
            relative_path = $_.FullName.Substring($Base.Length + 1).Replace('\', '/')
            bytes = [int64]$_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    })
}

try {
    $editors = @(Get-Process UnrealEditor, UnrealEditor-Cmd -ErrorAction SilentlyContinue)
    if ($editors.Count) { throw "Refusing Content mutation while Unreal is running: $($editors.Id -join ',')" }
    if (-not (Test-Path -LiteralPath $Source -PathType Container)) { throw "Missing failed target namespace: $Source" }
    if (-not (Test-Path -LiteralPath $FailureReceipt -PathType Leaf)) { throw "Missing fail-closed import receipt: $FailureReceipt" }
    $failure = Get-Content -LiteralPath $FailureReceipt -Raw | ConvertFrom-Json
    if ([string]$failure.status -notlike 'FAIL*') { throw "Failure receipt is not fail-closed: $($failure.status)" }
    $sourceResolved = (Resolve-Path -LiteralPath $Source).Path
    if (-not $sourceResolved.Equals([System.IO.Path]::GetFullPath($Source), [StringComparison]::OrdinalIgnoreCase)) { throw 'Target resolution drift' }
    $before = @(Get-Inventory $sourceResolved)
    $actual = @($before | ForEach-Object { $_.relative_path })
    if ($actual.Count -ne $Expected.Count -or @($actual | Where-Object { $_ -notin $Expected }).Count -or @($Expected | Where-Object { $_ -notin $actual }).Count) { throw 'Unexpected failed-import target inventory; preserving in place' }
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $quarantine = Join-Path $RejectedRoot ('BodyShopUnderbodySlice_v001_legacy_import_failure_' + $stamp)
    $target = Join-Path $quarantine 'BodyShopUnderbodySlice_v001'
    $rejectedFull = [System.IO.Path]::GetFullPath($RejectedRoot)
    $targetFull = [System.IO.Path]::GetFullPath($target)
    if (-not $targetFull.StartsWith($rejectedFull + [System.IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Quarantine path escapes RejectedArtifacts' }
    if ((Test-Path -LiteralPath $quarantine) -or (Test-Path -LiteralPath $target)) { throw 'Fresh quarantine target already exists' }
    New-Item -ItemType Directory -Force -Path $quarantine | Out-Null
    Move-Item -LiteralPath $sourceResolved -Destination $target -ErrorAction Stop
    if (Test-Path -LiteralPath $sourceResolved) { throw 'Source remained after recoverable move' }
    $after = @(Get-Inventory $target)
    $compactBefore = @($before | ForEach-Object { "$($_.relative_path)|$($_.bytes)|$($_.sha256)" })
    $compactAfter = @($after | ForEach-Object { "$($_.relative_path)|$($_.bytes)|$($_.sha256)" })
    if ((Compare-Object $compactBefore $compactAfter).Count) { throw 'Hash/size changed during recoverable move' }
    $receipt = [ordered]@{
        schema = 'lineboss/audit/bodyshop/experimental-v001-underbody-art-failed-import-quarantine/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__RECOVERABLY_QUARANTINED_FAILED_LEGACY_IMPORT_NAMESPACE_V001'
        action = 'Move-Item within project volume; no deletion or overwrite performed.'
        source_namespace_before = '/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001'
        source_absent_after_move = $true
        failed_import_receipt = $FailureReceipt
        failed_import_receipt_sha256 = (Get-FileHash -LiteralPath $FailureReceipt -Algorithm SHA256).Hash
        quarantine_directory = $quarantine
        quarantined_disk_path = $target
        file_count = $after.Count
        total_bytes = [int64](($after | Measure-Object -Property bytes -Sum).Sum)
        sha256_inventory_before = $before
        sha256_inventory_after = $after
        no_source_config_map_or_legacy_changes = $true
        unreal_launched_by_this_script = $false
        meshy_credits_used_by_codex = 0
    }
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $quarantine 'quarantine_receipt_v001.json') -Encoding utf8
    $receipt | ConvertTo-Json -Depth 8
}
catch {
    [ordered]@{
        schema = 'lineboss/audit/bodyshop/experimental-v001-underbody-art-failed-import-quarantine-failure/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'FAIL_CLOSED__NO_CLEANUP_PERFORMED'
        source = $Source
        error = $_.Exception.Message
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $RejectedRoot 'bodyshop_underbody_slice_failed_import_quarantine_failure_v001.json') -Encoding utf8
    throw
}
