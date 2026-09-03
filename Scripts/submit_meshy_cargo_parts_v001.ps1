# Generate CONCEPT PREVIEWS for the Cargo-01's four own component kinds
# (owner 2026-09-02, "the line grows by components per craft" ->
# Docs/CARGO_TEN_COMPONENTS_2026_09_02_v001.md; Meshy API grant
# 2026-09-02: "use meshy api if you need anything making that you cant
# do yourself"). Right now these four ride the Cargo hull as sculpted
# detail with no separate fitting moment - this submission is the first
# step toward giving each its own model, so it can attach to the real
# Cargo-01 hull (concept A, SM_LB_SC_Cargo01_Craft_v001) the way the
# Scout's six parts attach to its hull.
#
# Concept first (owner, 2026-08-30): ONE preview per subject, geometry
# only, GOES IN FRONT OF THE OWNER before anything is refined or
# imported. Four subjects, four small, well-defined fittings - not
# three variants each, because the shape here is functional and
# constrained (a door, a ring, a pod, a plate), not open like the
# freighter's whole hull was.
#
# GEOMETRY ONLY. Materials are authored in Unreal (owner, standing).
# One-shot and fail-closed like every other lane here.
param(
    [Parameter(Mandatory = $true)][string]$Acknowledgement,
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft\CargoParts_v001',
    [int]$PollSeconds = 20,
    [int]$TimeoutMinutes = 40
)
$ErrorActionPreference = 'Stop'
if ($Acknowledgement -ne 'I ACCEPT MESHY CREDIT SPEND FOR CARGO PARTS V001') {
    throw 'Acknowledgement string does not match; refusing to spend credits.'
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Result root already exists: $OutputRoot. Author v002 rather than rerunning."
}

$Style = @'
Style: clean futuristic industrial spacecraft hardware. Pale grey and white panels, graphite framing, recessed blue-white light strips, sparing safety-orange. New and clean, not battle-worn. Matte metal, one closed object, symmetrical. No text, letters, numbers, logos. No ground plane, no scenery, no figures, no whole spacecraft - this is a single detached FITTING, on its own.
'@

$Jobs = @(
    @{ Name = 'CargoBay01_BayDoor'
       Subject = 'A CARGO BAY DOOR ASSEMBLY for a spacecraft belly: a large flat hinged door with a raised frame lip around its edge, exposed hold structure visible through a narrow gap at the hinge, mounting flanges along the frame.'
       Anchor  = 'Scale: about as wide as a small truck and half as tall - a hull SECTION that bolts onto a bigger craft, not a room or a vehicle of its own.' }
    @{ Name = 'DockingCollar01_Ring'
       Subject = 'A CIRCULAR DOCKING COLLAR for the top of a spacecraft: a raised ring with docking latches spaced around its rim, a flush hatch at the centre, one short antenna stub and one beacon light on the rim.'
       Anchor  = 'Scale: about as wide as a car and low and flat - a hull-top fitting, not a tower or a whole airlock module.' }
    @{ Name = 'ThrusterPod01_Single'
       Subject = 'A single THRUSTER POD for a spacecraft flank: a short cylindrical housing with an angled exhaust nozzle at the rear, a flat mounting collar at the front, two small RCS ports along its side.'
       Anchor  = 'Scale: about as long as a person and a third as wide - a hull-mounted pod, not a main engine or a whole wing.' }
    @{ Name = 'Shielding01_PlatingStrip'
       Subject = 'A STRIP OF FLAT ARMOUR PLATING for a spacecraft hull flank: three to four overlapping rectangular plates with raised rivet lines along their edges and a slight outward bevel, following a gentle curve.'
       Anchor  = 'Scale: about as long as a car and as wide as a door - a hull cladding strip, not a wall panel or a whole fuselage side.' }
)

$ApiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($ApiKey)) { throw 'Meshy API key file is empty.' }
$Headers = @{ Authorization = "Bearer $ApiKey" }
$BalanceBefore = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$Manifest = @()
foreach ($Job in $Jobs) {
    $Prompt = "Game-ready SPACECRAFT HULL FITTING, detached, on its own. $($Job.Subject) $($Job.Anchor)`n$Style"
    $Body = @{
        mode          = 'preview'
        prompt        = $Prompt.Trim()
        art_style     = 'realistic'
        should_remesh = $true
    }
    $Created = Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v2/text-to-3d' `
        -Headers $Headers -Method Post -ContentType 'application/json' `
        -Body ($Body | ConvertTo-Json -Depth 6)
    $TaskId = $Created.result
    Write-Output "SUBMITTED $($Job.Name) -> $TaskId"
    $Manifest += [pscustomobject]@{
        name = $Job.Name; task_id = $TaskId; mode = 'preview'; prompt = $Prompt.Trim()
    }
}
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'submission_manifest.json') -Encoding UTF8

$Deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$Results = @()
foreach ($Entry in $Manifest) {
    $Task = $null
    while ((Get-Date) -lt $Deadline) {
        $Task = Invoke-RestMethod -Uri ("https://api.meshy.ai/openapi/v2/text-to-3d/" + $Entry.task_id) -Headers $Headers
        if ($Task.status -in @('SUCCEEDED', 'FAILED', 'CANCELED')) { break }
        Start-Sleep -Seconds $PollSeconds
    }
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
    '$schema'      = 'lineboss/audit/meshy-cargo-parts-v001/v1'
    generated_utc  = (Get-Date).ToUniversalTime().ToString('o')
    status         = if ($Succeeded -eq $Jobs.Count) { 'PASS__CARGO_PARTS_PREVIEWS_GENERATED' } else { 'PARTIAL__CARGO_PARTS_PREVIEWS' }
    balance_before = $BalanceBefore
    balance_after  = $BalanceAfter
    credits_spent  = $BalanceBefore - $BalanceAfter
    results        = $Results
    not_proven     = @(
        'Previews only - untextured draft geometry, not refined. Identity and quality are confirmed by RENDER, never by filename.',
        'No promotion: nothing is imported into Content until the renders confirm what each file actually is, sized to its socket and verified at import.'
    )
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'generation_receipt.json') -Encoding UTF8
Write-Output "SPENT $($BalanceBefore - $BalanceAfter) credits; $Succeeded/$($Jobs.Count) succeeded; balance now $BalanceAfter"
