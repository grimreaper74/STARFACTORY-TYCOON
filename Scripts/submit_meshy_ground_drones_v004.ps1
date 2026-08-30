# Generate the THREE GROUND DRONES (owner 2026-08-28: "we also need 3
# ground drones, 6 or 8 wheels for working underneath the ship, a
# lifter, assembly and sprayer").
#
# The aerial drones cannot work under a craft standing on its gear -
# these are the crew that can. Multi-wheeled, low-bodied, and low
# enough to drive beneath a Scout: the height is the whole point of
# the design, so it is the anchor every prompt leads with.
#
# GEOMETRY ONLY. Materials are authored in Unreal now (owner, same
# day), so nothing here will be refined for its maps - these meshes
# take the project palette at import.
#
# Why generate rather than buy: the project already owns a 759-piece
# industrial kit, but it is GREY PRESENT-DAY industrial while the
# factory buildings are WHITE FUTURISTIC. Dressing the site with the kit
# works at map distance and reads as a deliberate contrast - but scenery
# in our own language removes the contrast question entirely, costs
# credits we already hold, and needs no licence decision.
#
# Prompt discipline follows Docs/MESHY_BUILDING_PROMPT_v002.md, with a
# third scale class added: SITE FURNITURE stands outdoors, is read from
# map distance AND from the ground, and its anchors are vehicle-scale -
# a truck passing through a gate, a person beside a fence panel.
#
# The three standing constraints are repeated in every prompt: no text,
# no conveyors, no strong brand colour.
#
# One-shot and fail-closed like every other lane here: refuses to run
# over an existing result root, refuses without an acknowledgement,
# records a receipt with the credit cost of every task.

param(
    [Parameter(Mandatory = $true)][string]$Acknowledgement,
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft\GroundDrones_v004',
    [int]$PollSeconds = 20,
    [int]$TimeoutMinutes = 25
)

$ErrorActionPreference = 'Stop'
if ($Acknowledgement -ne 'I ACCEPT MESHY CREDIT SPEND FOR GROUND DRONES V004') {
    throw 'Acknowledgement string does not match; refusing to spend credits.'
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Result root already exists: $OutputRoot. Author v002 rather than rerunning."
}

# The API caps a prompt at 800 characters, so the style block is the
# v002 language COMPRESSED, not shortened in substance: white/pale-grey
# panels over graphite framing, blue-white emissive, sparing orange,
# clean not grimy - and all three standing constraints (no text, no
# conveyors, no brand colour) survive the squeeze, because they are the
# ones that keep being violated.
$Style = @'
Style: smooth white and pale-grey panels, chamfered edges, graphite-dark
framing, recessed blue-white emissive strips, sparing safety-orange on
hazard corners. Clean and new, not grimy or rusted. Neutral cold tones,
no brand colour. Flat base, hard-surface modelling, PBR painted metal,
single closed object. No text, letters, numbers, signage or logos. No
ground plane, no scenery, no figures, no conveyors.
'@

# Each subject carries its OWN scale anchor, in the chosen language -
# the lesson from v002: without an anchor a generator returns a prop.
$Jobs = @(
    @{ Name = 'Ground01_LifterDrone'
       Subject = 'A low eight-wheeled ground drone with a flat scissor-lift deck on its back, built to drive under a spacecraft and raise a load.'
       Anchor  = 'Scale: low enough for a person to step over, four small wheels a side reaching mid-shin, the lift deck at knee height when stowed.' }
    @{ Name = 'Ground02_AssemblyDrone'
       Subject = 'A low six-wheeled ground drone carrying a folded articulated work arm and a tool head on top.'
       Anchor  = 'Scale: knee height with the arm folded, three small wheels a side, a tool head about the size of a persons forearm.' }
    @{ Name = 'Ground03_SprayerDrone'
       Subject = 'A low eight-wheeled ground drone with a pair of spray booms on a small mast and two fluid tanks along its flanks.'
       Anchor  = 'Scale: knee height at the deck, the mast rising to waist height, tanks the size of beer kegs.' }
)

$ApiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($ApiKey)) { throw 'Meshy API key file is empty.' }
$Headers = @{ Authorization = "Bearer $ApiKey" }
$BalanceBefore = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$Manifest = @()
foreach ($Job in $Jobs) {
    $Prompt = "Game-ready FUTURISTIC INDUSTRIAL SITE FURNITURE for a spacecraft factory site. $($Job.Subject) $($Job.Anchor)`n$Style"
    if ($Prompt.Trim().Length -gt 800) {
        throw "Prompt for $($Job.Name) is $($Prompt.Trim().Length) chars; the API caps at 800."
    }
    $Payload = @{
        mode         = 'preview'
        prompt       = $Prompt.Trim()
        art_style    = 'realistic'
        should_remesh = $true
    } | ConvertTo-Json -Depth 6
    $Created = Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v2/text-to-3d' `
        -Headers $Headers -Method Post -ContentType 'application/json' -Body $Payload
    $TaskId = [string]$Created.result
    if ([string]::IsNullOrWhiteSpace($TaskId)) { throw "No task id for $($Job.Name)." }
    Write-Output "SUBMITTED $($Job.Name) -> $TaskId"
    $Manifest += [pscustomobject]@{
        name = $Job.Name; task_id = $TaskId; mode = 'preview'; prompt = $Prompt.Trim()
    }
}

$ManifestPath = Join-Path $OutputRoot 'submission_manifest.json'
@{
    '$schema'      = 'lineboss/audit/meshy-ground-drones-v004/v1'
    submitted_utc  = (Get-Date).ToUniversalTime().ToString('o')
    balance_before = $BalanceBefore
    endpoint       = '/openapi/v2/text-to-3d'
    tasks          = $Manifest
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8

# ---- poll every task to completion and pull the GLB ----
$Deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$Results = @()
foreach ($Entry in $Manifest) {
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
        Invoke-WebRequest -Uri $Task.model_urls.glb -OutFile $GlbPath -TimeoutSec 300
    }
    $Results += [pscustomobject]@{
        name = $Entry.name; task_id = $Entry.task_id; status = $Task.status
        consumed_credits = $Task.consumed_credits
        glb = $GlbPath
        sha256 = if ($GlbPath -and (Test-Path $GlbPath)) { (Get-FileHash -Algorithm SHA256 -LiteralPath $GlbPath).Hash } else { $null }
    }
}

$BalanceAfter = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
$Succeeded = @($Results | Where-Object { $_.status -eq 'SUCCEEDED' }).Count
@{
    '$schema'      = 'lineboss/audit/meshy-ground-drones-v004/v1'
    generated_utc  = (Get-Date).ToUniversalTime().ToString('o')
    status         = if ($Succeeded -eq $Jobs.Count) { 'PASS__SITE_SCENERY_PREVIEWS_GENERATED' } else { 'PARTIAL__SITE_SCENERY_PREVIEWS' }
    balance_before = $BalanceBefore
    balance_after  = $BalanceAfter
    credits_spent  = $BalanceBefore - $BalanceAfter
    results        = $Results
    not_proven     = @(
        'Previews only - untextured draft geometry, not refined. Nobody has looked at them yet; identity and quality are confirmed by RENDER, never by filename.',
        'No promotion: nothing is imported into Content until the owner has seen the renders.'
    )
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'generation_receipt.json') -Encoding UTF8
Write-Output "SPENT $($BalanceBefore - $BalanceAfter) credits; $Succeeded/$($Jobs.Count) succeeded; balance now $BalanceAfter"
