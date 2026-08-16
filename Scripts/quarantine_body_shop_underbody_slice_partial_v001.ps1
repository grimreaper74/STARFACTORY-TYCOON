$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

# Recoverably quarantines only the interrupted Body Shop v001 intake namespace.
# This script must run with no Unreal editor process; it never deletes files.
$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Source = Join-Path $Root 'Content\LineBoss\Candidates\WeldShop\BodyShopUnderbodySlice_v001'
$AuditRoot = Join-Path $Root 'Saved\Audits\BodyShop\Experimental_v001'
$RejectedRoot = Join-Path $AuditRoot 'RejectedArtifacts'
$PauseReceipt = Join-Path $AuditRoot 'import_underbody_slice_art_pause_v001.json'
$ExpectedRelativeFiles = @(
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

function Get-Inventory([string]$BasePath) {
    $items = @(Get-ChildItem -LiteralPath $BasePath -Recurse -File | Sort-Object FullName | ForEach-Object {
        $relative = $_.FullName.Substring($BasePath.Length + 1).Replace('\', '/')
        [pscustomobject]@{
            relative_path = $relative
            bytes = [int64]$_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            last_write_utc = $_.LastWriteTimeUtc.ToString('o')
        }
    })
    return $items
}

function Assert-ExactPartialInventory([object[]]$Inventory, [string]$Label) {
    $actual = @($Inventory | ForEach-Object { $_.relative_path })
    if ($actual.Count -ne $ExpectedRelativeFiles.Count) {
        throw "$Label file-count drift: $($actual.Count) != $($ExpectedRelativeFiles.Count)"
    }
    $unexpected = @($actual | Where-Object { $_ -notin $ExpectedRelativeFiles })
    $missing = @($ExpectedRelativeFiles | Where-Object { $_ -notin $actual })
    if ($unexpected.Count -gt 0 -or $missing.Count -gt 0) {
        throw "$Label inventory drift; unexpected=$($unexpected -join ','); missing=$($missing -join ',')"
    }
}

try {
    $editors = @(Get-Process UnrealEditor, UnrealEditor-Cmd -ErrorAction SilentlyContinue)
    if ($editors.Count -gt 0) {
        throw "Refusing Content mutation while Unreal is running: $($editors.Id -join ',')"
    }
    if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
        throw "Partial source namespace does not exist: $Source"
    }
    if (-not (Test-Path -LiteralPath $PauseReceipt -PathType Leaf)) {
        throw "Required pause receipt does not exist: $PauseReceipt"
    }

    $sourceResolved = (Resolve-Path -LiteralPath $Source).Path
    $expectedSource = [System.IO.Path]::GetFullPath($Source)
    if (-not $sourceResolved.Equals($expectedSource, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Source path resolution drift: $sourceResolved != $expectedSource"
    }
    $preInventory = @(Get-Inventory $sourceResolved)
    Assert-ExactPartialInventory $preInventory 'pre-move'
    $preBytes = [int64](($preInventory | Measure-Object -Property bytes -Sum).Sum)

    $timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $quarantineRoot = Join-Path $RejectedRoot ("BodyShopUnderbodySlice_v001_partial_" + $timestamp)
    $target = Join-Path $quarantineRoot 'BodyShopUnderbodySlice_v001'
    $rejectedRootResolved = [System.IO.Path]::GetFullPath($RejectedRoot)
    $targetFull = [System.IO.Path]::GetFullPath($target)
    if (-not $targetFull.StartsWith($rejectedRootResolved + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Resolved quarantine target escapes approved RejectedArtifacts root: $targetFull"
    }
    if ((Test-Path -LiteralPath $target) -or (Test-Path -LiteralPath $quarantineRoot)) {
        throw "Freshness violation: quarantine target already exists: $quarantineRoot"
    }
    New-Item -ItemType Directory -Force -Path $quarantineRoot | Out-Null
    Move-Item -LiteralPath $sourceResolved -Destination $target -ErrorAction Stop

    if (Test-Path -LiteralPath $sourceResolved) {
        throw "Source namespace still exists after recoverable move: $sourceResolved"
    }
    if (-not (Test-Path -LiteralPath $target -PathType Container)) {
        throw "Quarantine target missing after move: $target"
    }
    $postInventory = @(Get-Inventory $target)
    Assert-ExactPartialInventory $postInventory 'post-move'
    $postBytes = [int64](($postInventory | Measure-Object -Property bytes -Sum).Sum)
    $preCompact = @($preInventory | ForEach-Object { "$($_.relative_path)|$($_.bytes)|$($_.sha256)" })
    $postCompact = @($postInventory | ForEach-Object { "$($_.relative_path)|$($_.bytes)|$($_.sha256)" })
    if ((Compare-Object -ReferenceObject $preCompact -DifferenceObject $postCompact).Count -ne 0) {
        throw 'Hash or byte inventory changed during recoverable move'
    }

    $receipt = [ordered]@{
        schema = 'lineboss/audit/bodyshop/experimental-v001-underbody-art-partial-quarantine/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__RECOVERABLY_QUARANTINED_INTERRUPTED_PARTIAL_NAMESPACE_V001'
        action = 'Move-Item within the same project volume; no deletion or overwrite performed.'
        source_namespace_before = '/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001'
        source_disk_path_before = $sourceResolved
        source_absent_after_move = $true
        rejected_artifacts_root = $rejectedRootResolved
        quarantine_directory = $quarantineRoot
        quarantined_disk_path = $target
        file_count = $postInventory.Count
        total_bytes_before = $preBytes
        total_bytes_after = $postBytes
        sha256_inventory_before = $preInventory
        sha256_inventory_after = $postInventory
        pause_receipt = $PauseReceipt
        pause_receipt_sha256 = (Get-FileHash -LiteralPath $PauseReceipt -Algorithm SHA256).Hash
        no_source_config_map_or_legacy_changes = $true
        unreal_launched_by_this_script = $false
        meshy_credits_used_by_codex = 0
    }
    $receiptPath = Join-Path $quarantineRoot 'quarantine_receipt_v001.json'
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8
    Write-Output ($receipt | ConvertTo-Json -Depth 8)
}
catch {
    $failureRoot = Join-Path $AuditRoot 'RejectedArtifacts'
    New-Item -ItemType Directory -Force -Path $failureRoot | Out-Null
    $failurePath = Join-Path $failureRoot 'bodyshop_underbody_slice_partial_quarantine_failure_v001.json'
    [ordered]@{
        schema = 'lineboss/audit/bodyshop/experimental-v001-underbody-art-partial-quarantine-failure/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'FAIL_CLOSED__BODYSHOP_UNDERBODY_ART_PARTIAL_QUARANTINE_V001'
        source = $Source
        error = $_.Exception.Message
        automatic_cleanup = 'NOT_PERFORMED__preserved files for inspection'
        unreal_launched_by_this_script = $false
        meshy_credits_used_by_codex = 0
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $failurePath -Encoding utf8
    throw
}
