# Generate the TRICYCLE LANDING GEAR (owner 2026-08-28: "we also need
# tricycle landing gear ... also needs to be on ship but disappears when
# it takes off at the end, also your call if it has wheels or feet").
#
# WHEELS, decided: the site has a permanent runway, the craft taxis a
# chicane onto it before the sprint, and wheels are what "tricycle gear"
# means in the aircraft sense the owner used. Wheels also give the new
# ground crew something to work around under the belly.
#
# TWO subjects, not three: a NOSE leg and a MAIN leg. The main is placed
# twice, mirrored, which is how real gear is built and what keeps the
# bill of materials honest - one nose leg and two mains.
#
# GEOMETRY ONLY. Materials are authored in Unreal (owner, same day), so
# nothing here will be refined for its maps; these take the project
# palette at import.
#
# SCALE IS THE ANCHOR, and the lesson from the ground drones is that a
# generator ignores a COUNT but respects a COMPARISON. So neither prompt
# asks for "a small wheel" - each says what the wheel is the size of.
# The leg is about a metre: waist height on a person, wheel about the
# size of a motorcycle wheel on the nose and a car wheel on the mains.
#
# One-shot and fail-closed like every other lane here: refuses to run
# over an existing result root, refuses without an acknowledgement,
# records a receipt with the credit cost of every task.

param(
    [Parameter(Mandatory = $true)][string]$Acknowledgement,
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft\LineHardware_v008',
    [int]$PollSeconds = 20,
    [int]$TimeoutMinutes = 25
)

$ErrorActionPreference = 'Stop'
if ($Acknowledgement -ne 'I ACCEPT MESHY CREDIT SPEND FOR LINE HARDWARE V008') {
    throw 'Acknowledgement string does not match; refusing to spend credits.'
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Result root already exists: $OutputRoot. Author v009 rather than rerunning."
}

# Compressed style block - the API caps a prompt at 800 characters. The
# three standing constraints (no text, no conveyors, no brand colour)
# survive the squeeze because they are the ones that keep being broken.
# "Retracted position not shown" matters: a generator asked for landing
# gear will happily fold it away, and a folded leg is useless here.
$Style = @'
Style: pale grey and white panels, graphite framing, recessed blue-white
emissive strips, sparing safety-orange. Clean and new, not grimy or
rusted. Neutral cold tones, no brand colour. Matte painted metal, single
closed object. No text, letters, numbers, signage or logos. No ground
plane, no scenery, no figures, no vehicles.
'@

$Jobs = @(
    # THE TRACK is now the most prominent thing on the factory floor and
    # renders as a painted stripe. In both reference games the conveyor
    # is the spine of the picture, so this is the highest-value model in
    # the project right now.
    #
    # It is a SECTION, laid repeatedly, so it must tile: the prompt says
    # flat-ended and straight so the ends butt against each other.
    @{ Name = 'Track01_ConveyorSection'
       Subject = 'A straight section of heavy industrial floor conveyor: a flat slatted belt deck between two low side rails, carried on short square legs, with roller ends. Flat cut ends so sections butt together in a line.'
       Anchor  = 'Scale: about four metres long and three wide, the deck at about knee height. It is a straight repeating section, not a whole machine and not a curve.' }
    # The lift is engine cylinders standing in for a hydraulic ram.
    @{ Name = 'Lift01_HydraulicRam'
       Subject = 'A single vertical TELESCOPIC HYDRAULIC RAM standing on a round floor base: three nested polished cylinder stages, widest at the bottom, with a flat square load saddle on top and hydraulic hoses down one side.'
       Anchor  = 'Scale: the base is about a metre and a half across and the ram stands about waist height retracted. One central column only - no scissor linkage and no corner posts.' }
)

$ApiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($ApiKey)) { throw 'Meshy API key file is empty.' }
$Headers = @{ Authorization = "Bearer $ApiKey" }
$BalanceBefore = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$Manifest = @()
foreach ($Job in $Jobs) {
    $Prompt = "Game-ready FUTURISTIC AIRCRAFT UNDERCARRIAGE part for a spacecraft. $($Job.Subject) $($Job.Anchor)`n$Style"
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
    '$schema'      = 'lineboss/audit/meshy-line-hardware-v008/v1'
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
    '$schema'      = 'lineboss/audit/meshy-line-hardware-v008/v1'
    generated_utc  = (Get-Date).ToUniversalTime().ToString('o')
    status         = if ($Succeeded -eq $Jobs.Count) { 'PASS__LINE_HARDWARE_PREVIEWS_GENERATED' } else { 'PARTIAL__LINE_HARDWARE_PREVIEWS' }
    balance_before = $BalanceBefore
    balance_after  = $BalanceAfter
    credits_spent  = $BalanceBefore - $BalanceAfter
    results        = $Results
    not_proven     = @(
        'Previews only - untextured draft geometry, not refined. Nobody has looked at them yet; identity and quality are confirmed by RENDER, never by filename.',
        'No promotion: nothing is imported into Content until the renders confirm what each file actually is.'
    )
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'generation_receipt.json') -Encoding UTF8
Write-Output "SPENT $($BalanceBefore - $BalanceAfter) credits; $Succeeded/$($Jobs.Count) succeeded; balance now $BalanceAfter"
