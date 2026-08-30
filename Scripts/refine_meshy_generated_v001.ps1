# REFINE the preview meshes we generated into textured assets.
#
# Everything generated on 2026-08-28 is Meshy PREVIEW output: draft
# geometry with no maps at all. It reads well as white forms at map
# distance, which is why it shipped that way first - but up close there
# is no panel detail, no wear, nothing. Refining is the second half of
# the same task and costs credits, so it is its own lane with its own
# acknowledgement rather than a step buried in the generation script.
#
# Refinement takes the PREVIEW TASK ID, not the mesh: the receipts from
# the generation lanes are the input, which is why those receipts record
# every task id.
#
# One-shot and fail-closed like the rest: refuses to run over its own
# result root, refuses without the acknowledgement, records what each
# task cost and what the balance was before and after.

param(
    [Parameter(Mandatory = $true)][string]$Acknowledgement,
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft\Refined_v001',
    [int]$PollSeconds = 20,
    [int]$TimeoutMinutes = 40
)

$ErrorActionPreference = 'Stop'
if ($Acknowledgement -ne 'I ACCEPT MESHY CREDIT SPEND FOR REFINEMENT V001') {
    throw 'Acknowledgement string does not match; refusing to spend credits.'
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Result root already exists: $OutputRoot. Author v002."
}

# The ELEVEN keepers, by the preview task that made each one. The two
# that were generated and NOT kept (the pipe rack, the craft cradle)
# are deliberately absent: refining a mesh the game does not use is
# just spending.
$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft'
$Sources = @(
    @{ Receipt = "$Root\SiteScenery_v001\generation_receipt.json"
       Keep = @('Scenery01_PerimeterFencePanel', 'Scenery02_SiteEntranceGate',
                'Scenery04_CargoContainer', 'Scenery05_BulkStorageTank',
                'Scenery06_ElectricalSubstation', 'Scenery08_DeliveryHauler') },
    @{ Receipt = "$Root\SiteScenery_v002\generation_receipt.json"
       Keep = @('Scenery03_YardLightMast') },
    @{ Receipt = "$Root\ShipFactoryInterior_v003\generation_receipt.json"
       Keep = @('Interior01_PartsStockpileRack', 'Interior02_HallSupportColumn',
                'Interior03_OverheadGantryCrane', 'Interior05_DispatchDoorway') }
)

$ApiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($ApiKey)) { throw 'Meshy API key file is empty.' }
$Headers = @{ Authorization = "Bearer $ApiKey" }
$BalanceBefore = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$Jobs = @()
foreach ($Source in $Sources) {
    if (-not (Test-Path -LiteralPath $Source.Receipt)) {
        throw "Missing generation receipt: $($Source.Receipt)"
    }
    $Receipt = Get-Content -LiteralPath $Source.Receipt -Raw | ConvertFrom-Json
    foreach ($Result in $Receipt.results) {
        if ($Source.Keep -notcontains $Result.name) { continue }
        if ($Result.status -ne 'SUCCEEDED') {
            throw "$($Result.name) did not succeed in preview; nothing to refine."
        }
        $Jobs += [pscustomobject]@{ name = $Result.name; preview = $Result.task_id }
    }
}
if ($Jobs.Count -ne 11) {
    throw "Expected 11 keepers to refine, found $($Jobs.Count)."
}

$Submitted = @()
foreach ($Job in $Jobs) {
    $Payload = @{
        mode = 'refine'
        preview_task_id = $Job.preview
        enable_pbr = $true
    } | ConvertTo-Json -Depth 5
    $Created = Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v2/text-to-3d' `
        -Headers $Headers -Method Post -ContentType 'application/json' -Body $Payload
    $TaskId = [string]$Created.result
    if ([string]::IsNullOrWhiteSpace($TaskId)) { throw "No refine task for $($Job.name)." }
    Write-Output "REFINING $($Job.name) -> $TaskId"
    $Submitted += [pscustomobject]@{ name = $Job.name; preview = $Job.preview; task_id = $TaskId }
}

$Deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$Results = @()
foreach ($Entry in $Submitted) {
    $Task = $null
    do {
        $Task = Invoke-RestMethod -Uri ("https://api.meshy.ai/openapi/v2/text-to-3d/" + $Entry.task_id) -Headers $Headers
        if ($Task.status -in @('SUCCEEDED', 'FAILED', 'CANCELED')) { break }
        Start-Sleep -Seconds $PollSeconds
    } while ((Get-Date) -lt $Deadline)
    Write-Output "$($Entry.name): $($Task.status) credits=$($Task.consumed_credits)"
    $GlbPath = $null
    if ($Task.status -eq 'SUCCEEDED' -and $Task.model_urls.glb) {
        $GlbPath = Join-Path $OutputRoot ("$($Entry.name).glb")
        Invoke-WebRequest -Uri $Task.model_urls.glb -OutFile $GlbPath -TimeoutSec 600
    }
    $Results += [pscustomobject]@{
        name = $Entry.name; preview_task_id = $Entry.preview
        refine_task_id = $Entry.task_id; status = $Task.status
        consumed_credits = $Task.consumed_credits; glb = $GlbPath
        sha256 = if ($GlbPath -and (Test-Path $GlbPath)) { (Get-FileHash -Algorithm SHA256 -LiteralPath $GlbPath).Hash } else { $null }
    }
}

$BalanceAfter = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
$Succeeded = @($Results | Where-Object { $_.status -eq 'SUCCEEDED' }).Count
@{
    '$schema'      = 'lineboss/audit/meshy-refine-v001/v1'
    generated_utc  = (Get-Date).ToUniversalTime().ToString('o')
    status         = if ($Succeeded -eq $Jobs.Count) { 'PASS__REFINED_WITH_PBR' } else { 'PARTIAL__REFINE' }
    balance_before = $BalanceBefore
    balance_after  = $BalanceAfter
    credits_spent  = $BalanceBefore - $BalanceAfter
    results        = $Results
    not_proven     = @(
        'Refined geometry and maps exist; nothing is imported until the renders are looked at.',
        'The refined mesh REPLACES the preview only if it is still the same object - a refine can drift, and identity is confirmed by looking.'
    )
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'refine_receipt.json') -Encoding UTF8
Write-Output "SPENT $($BalanceBefore - $BalanceAfter) credits; $Succeeded/$($Jobs.Count) refined; balance now $BalanceAfter"
