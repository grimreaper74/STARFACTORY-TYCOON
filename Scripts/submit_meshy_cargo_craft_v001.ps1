# Generate CONCEPT PREVIEWS for the Cargo-01 craft (owner 2026-09-03,
# "ok do it" to the plan whose first item was getting the Cargo model
# and its four new kinds on screen; the Meshy API grant of 2026-09-02:
# "use meshy api if you need anything making that you cant do yourself").
#
# Concept first (owner, 2026-08-30): three shapes go in front of the
# owner as PREVIEWS; he picks one; only the pick is refined, reduced in
# Blender if heavy, imported with its size imposed and verified, and
# promoted. Nothing here is imported into Content.
#
# The craft the previews must carry, because these are the ten kinds
# the line now fits (Docs/CARGO_TEN_COMPONENTS_2026_09_02_v001.md):
# a hull with a belly CARGO BAY door, a DOCKING COLLAR on top amidships,
# twin THRUSTER PODS aft on the flanks, flat SHIELDING plates low along
# both sides, a short nose with a canopy, three engine nozzles at the
# tail, landing skids. About 1.5x the Scout (21 m long, 11 m wide).
#
# GEOMETRY ONLY. Materials are authored in Unreal (owner, standing).
# One-shot and fail-closed like every other lane here.
param(
    [Parameter(Mandatory = $true)][string]$Acknowledgement,
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft\CargoCraft_v001',
    [int]$PollSeconds = 20,
    [int]$TimeoutMinutes = 40
)

$ErrorActionPreference = 'Stop'
if ($Acknowledgement -ne 'I ACCEPT MESHY CREDIT SPEND FOR CARGO CRAFT V001') {
    throw 'Acknowledgement string does not match; refusing to spend credits.'
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Result root already exists: $OutputRoot. Author v002 rather than rerunning."
}

$Style = @'
Style: clean futuristic industrial spacecraft. Pale grey and white hull panels, graphite framing, recessed blue-white light strips, sparing safety-orange. New and clean, not battle-worn. Matte metal, one closed object, symmetrical. No text, letters, numbers, logos. No ground plane, no scenery, no figures.
'@

$Jobs = @(
    @{ Name = 'CargoA_BluntFreighter'
       Subject = 'A compact CARGO SPACECRAFT, blunt box freighter: a boxy central hold with a large belly cargo bay door, a round docking collar on top amidships, twin small thruster pods aft on each flank, flat armour plates low along both sides, a short nose with a canopy, three engine nozzles at the tail, landing skids.'
       Anchor  = 'Scale: about as long as a bus and a half, wider than it is tall. One craft only.' }
    @{ Name = 'CargoB_LiftingBody'
       Subject = 'A compact CARGO SPACECRAFT, lifting-body freighter: a flattened wedge hull, a belly cargo bay door under the middle, a round docking collar on the upper deck, twin thruster pods aft on the flanks, flat armour plates low along both sides, a canopy at the short nose, three engine nozzles at the tail, landing skids.'
       Anchor  = 'Scale: about as long as a bus and a half, wider than it is tall. One craft only.' }
    @{ Name = 'CargoC_TwinBoom'
       Subject = 'A compact CARGO SPACECRAFT, twin-boom hauler: a cargo pod with a belly bay door slung between two side booms, a round docking collar on top of the pod, a thruster pod at the end of each boom, flat armour plates low on the booms, a canopy at the short nose, three engine nozzles at the tail, landing skids.'
       Anchor  = 'Scale: about as long as a bus and a half, wider than it is tall. One craft only.' }
)

$ApiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($ApiKey)) { throw 'Meshy API key file is empty.' }
$Headers = @{ Authorization = "Bearer $ApiKey" }
$BalanceBefore = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$Manifest = @()
foreach ($Job in $Jobs) {
    $Prompt = "Game-ready SMALL SPACECRAFT built in a futuristic factory. $($Job.Subject) $($Job.Anchor)`n$Style"
    if ($Prompt.Trim().Length -gt 800) {
        throw "Prompt for $($Job.Name) is $($Prompt.Trim().Length) chars; the API caps at 800."
    }
    $Payload = @{
        mode          = 'preview'
        prompt        = $Prompt.Trim()
        art_style     = 'realistic'
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
    '$schema'      = 'lineboss/audit/meshy-cargo-craft-v001/v1'
    submitted_utc  = (Get-Date).ToUniversalTime().ToString('o')
    balance_before = $BalanceBefore
    endpoint       = '/openapi/v2/text-to-3d'
    tasks          = $Manifest
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8

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
    '$schema'      = 'lineboss/audit/meshy-cargo-craft-v001/v1'
    generated_utc  = (Get-Date).ToUniversalTime().ToString('o')
    status         = if ($Succeeded -eq $Jobs.Count) { 'PASS__CARGO_CRAFT_PREVIEWS_GENERATED' } else { 'PARTIAL__CARGO_CRAFT_PREVIEWS' }
    balance_before = $BalanceBefore
    balance_after  = $BalanceAfter
    credits_spent  = $BalanceBefore - $BalanceAfter
    results        = $Results
    not_proven     = @(
        'Previews only - untextured draft geometry, not refined. Identity and quality are confirmed by RENDER, never by filename.',
        'No promotion: nothing is imported into Content until the renders confirm what each file actually is and the size is imposed at export and verified at import.'
    )
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'generation_receipt.json') -Encoding UTF8
Write-Output "SPENT $($BalanceBefore - $BalanceAfter) credits; $Succeeded/$($Jobs.Count) succeeded; balance now $BalanceAfter"
