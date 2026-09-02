# Generate the STATION DRESS for phases C and E of the look plan
# (Docs/LOOK_JUDGEMENT_AND_PLAN_v001.md; owner 2026-09-02, leaving for
# work: "can you finish all 6 phases please" and "use meshy api if you
# need anything making that you cant do yourself").
#
# Four subjects, each one the model that a code blockout cannot deliver:
#
#   Tower01_StationToolTower  - the fitting station's presence. ONE tower
#       on the far flank (never between the camera and the craft), pale
#       housing, amber cap, a blue-white light strip on the face toward
#       the work, an articulated amber arm reaching in low. Proportions
#       follow the blockout judged the same day: about 5.5 m tall on a
#       2 m by 1.7 m foot.
#   Rack01_WallStorageRack    - phase E frame fill: a tall pallet rack
#       to run along the hall walls, three shelves, crates on the
#       shelves, about 6 m long and 5 m high.
#   Light01_CeilingLightBar   - phase E: a long industrial light fitting
#       to hang in rows under the roof, about 4 m long, with a visible
#       diffuser strip.
#   Cabinet01_StationToolCabinet - the near-flank counterpart that stays
#       LOW so it hides nothing: a waist-high tool and control cabinet
#       with an angled panel, about 1.5 m long.
#
# GEOMETRY ONLY. Materials are authored in Unreal (owner, standing).
# SCALE IS THE ANCHOR: a generator ignores a count but respects a
# comparison, so each prompt says what the object is the size of.
#
# One-shot and fail-closed like every other lane here: refuses to run
# over an existing result root, refuses without an acknowledgement,
# records a receipt with the credit cost of every task.

param(
    [Parameter(Mandatory = $true)][string]$Acknowledgement,
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft\StationDress_v009',
    [int]$PollSeconds = 20,
    [int]$TimeoutMinutes = 40
)

$ErrorActionPreference = 'Stop'
if ($Acknowledgement -ne 'I ACCEPT MESHY CREDIT SPEND FOR STATION DRESS V009') {
    throw 'Acknowledgement string does not match; refusing to spend credits.'
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Result root already exists: $OutputRoot. Author v010 rather than rerunning."
}

$Style = @'
Style: pale grey and white panels, graphite framing, recessed blue-white
emissive strips, sparing safety-orange. Clean and new, not grimy or
rusted. Neutral tones, no brand colour. Matte painted metal, single
closed object. No text, letters, numbers, signage or logos. No ground
plane, no scenery, no figures, no vehicles.
'@

$Jobs = @(
    @{ Name = 'Tower01_StationToolTower'
       Subject = 'A single freestanding INDUSTRIAL TOOL TOWER for a robotic assembly bay: a tall rectangular cabinet housing on a low plinth, a flat cap on top, one articulated robot arm folded low on its front face, a vertical light strip recessed in the front face. One tower only, no gantry, no arch, no second post.'
       Anchor  = 'Scale: about three times the height of a person, standing on a foot about the size of a car bonnet. Upright, rectangular, taller than wide.' }
    @{ Name = 'Rack01_WallStorageRack'
       Subject = 'A long INDUSTRIAL PALLET RACK: two upright frames with three horizontal shelf beams, closed crates and a few cylindrical containers sitting on the shelves, flat ends so racks butt together in a row.'
       Anchor  = 'Scale: about as long as a car and a half and about three people tall. A straight repeating section, not a whole warehouse.' }
    @{ Name = 'Light01_CeilingLightBar'
       Subject = 'A long INDUSTRIAL CEILING LIGHT FITTING: a slim rectangular housing with a flat diffuser strip on its underside, two short hanging brackets on top, flat ends.'
       Anchor  = 'Scale: about as long as a car, about as thick as a forearm. A straight fitting, one piece, not a chandelier.' }
    @{ Name = 'Cabinet01_StationToolCabinet'
       Subject = 'A low INDUSTRIAL TOOL AND CONTROL CABINET: a waist-high box on a plinth with an angled control panel on top, two closed doors on the front, a short cable duct along the base.'
       Anchor  = 'Scale: waist height on a person and about as long as a person is tall. Low and wide, never taller than a person.' }
)

$ApiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($ApiKey)) { throw 'Meshy API key file is empty.' }
$Headers = @{ Authorization = "Bearer $ApiKey" }
$BalanceBefore = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$Manifest = @()
foreach ($Job in $Jobs) {
    $Prompt = "Game-ready FACTORY EQUIPMENT for a clean futuristic spacecraft factory. $($Job.Subject) $($Job.Anchor)`n$Style"
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
    '$schema'      = 'lineboss/audit/meshy-station-dress-v009/v1'
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
    '$schema'      = 'lineboss/audit/meshy-station-dress-v009/v1'
    generated_utc  = (Get-Date).ToUniversalTime().ToString('o')
    status         = if ($Succeeded -eq $Jobs.Count) { 'PASS__STATION_DRESS_PREVIEWS_GENERATED' } else { 'PARTIAL__STATION_DRESS_PREVIEWS' }
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
