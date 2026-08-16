[CmdletBinding()]
param(
    [string]$CatalogPath = (Join-Path (Split-Path $PSScriptRoot -Parent) 'master_asset_catalog.json'),
    [string]$OutputPath = (Join-Path (Split-Path $PSScriptRoot -Parent) 'master_asset_catalog.csv'),
    [string]$TodayFilesOutputPath = (Join-Path (Split-Path $PSScriptRoot -Parent) 'meshy_files_received_2026-08-12.csv')
)

$ErrorActionPreference = 'Stop'
$catalog = Get-Content -Raw -LiteralPath $CatalogPath | ConvertFrom-Json
$rows = foreach ($family in $catalog.families) {
    [pscustomobject][ordered]@{
        asset_id = $family.asset_id
        display_name = $family.display_name
        domain = $family.domain
        source_family = $family.source_family
        supplied_today = [bool]$family.supplied_today
        role = $family.role
        role_verdict = $family.role_verdict
        lifecycle_status = $family.lifecycle_status
        runtime_status = $family.runtime_status
        source_file_count = @($family.source_files).Count
        best_authority_relative_path = $family.best_authority_relative_path
        manifest_relative_path = $family.manifest_relative_path
        audit_relative_path = $family.audit_relative_path
        unreal_paths = (@($family.unreal_paths) -join '; ')
        outstanding_action = $family.outstanding_action
    }
}
$rows | Sort-Object asset_id | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8

$todayRows = foreach ($family in $catalog.families | Where-Object supplied_today) {
    foreach ($source in $family.source_files) {
        [pscustomobject][ordered]@{
            asset_id = $family.asset_id
            family = $family.display_name
            role = $family.role
            role_verdict = $family.role_verdict
            lifecycle_status = $family.lifecycle_status
            stage = $source.stage
            original_path = $source.path
            intake_relative_path = $source.intake_relative_path
            bytes = [int64]$source.bytes
            sha256 = $source.sha256
            best_authority = ($family.best_authority_relative_path -eq $source.intake_relative_path)
            outstanding_action = $family.outstanding_action
        }
    }
}
$todayRows | Sort-Object asset_id, stage, original_path | Export-Csv -LiteralPath $TodayFilesOutputPath -NoTypeInformation -Encoding utf8

[pscustomobject]@{
    family_rows = @($rows).Count
    today_file_rows = @($todayRows).Count
    family_csv = $OutputPath
    today_files_csv = $TodayFilesOutputPath
} | ConvertTo-Json
