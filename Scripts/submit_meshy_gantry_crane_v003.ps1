# Generate a HEAVY-DUTY PORTAL GANTRY, drone-operated (owner
# 2026-08-28: "should the crane thing be more heavy duty like container
# cranes at docks but drone fielded?").
#
# He is right, and measurement says it is not a style preference. The
# crane in the hall is 2000 x 361 x 1013 cm and only 3,621 triangles.
# The Scout it has to lift is 1400 x 746 cm. THE CRANE IS 361 WIDE AND
# ITS LOAD IS 746 - it cannot straddle the thing it carries. It is a
# narrow A-frame standing beside the lane, not a portal spanning it.
#
# A container gantry is exactly the right reference and fits decisions
# already made: it STRADDLES a lane, it TRAVELS ON RAILS on one axis
# (which is how TickHallCrane already moves it), and it lifts by a
# SPREADER that latches onto fixed lift points - the same grapple
# language the kit skid was regenerated with.
#
# DRONE-FIELDED is the important half, and it is the standing rule:
# there are no people on this floor, so no operator cab, no ladders, no
# stairs, no catwalks, no handrails. Every one of those is what a
# generator reaches for first when asked for a dock crane, so all of
# them are named in the negative. What replaces them is drone perches on
# the frame.
#
# SPAN IS THE SPEC. The station bay is 1800 cm across, so the legs must
# stand outside that, and the portal has to clear a craft carried 260 cm
# up on its cradle. Anchored by comparison rather than number, because a
# generator ignores a measurement and respects a likeness.

param(
    [Parameter(Mandatory = $true)][string]$Acknowledgement,
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft\GantryCrane_v003',
    [int]$PollSeconds = 20,
    [int]$TimeoutMinutes = 25
)

$ErrorActionPreference = 'Stop'
if ($Acknowledgement -ne 'I ACCEPT MESHY CREDIT SPEND FOR GANTRY CRANE V003') {
    throw 'Acknowledgement string does not match; refusing to spend credits.'
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Result root already exists: $OutputRoot. Author v004 rather than rerunning."
}

# Compressed style block - the API caps a prompt at 800 characters.
$Style = @'
Style: pale panels, graphite frame, sparing safety orange. Clean and
new, not grimy. Matte painted steel, single object. No text, letters,
numbers or logos. No ground plane, scenery or people.
'@

$Jobs = @(
    @{ Name = 'Crane03_PortalGantry'
       Subject = 'A heavy PORTAL GANTRY CRANE like a container yard crane: a tall rectangular portal of deep box girders on four braced legs on rails, a trolley crossing the top beam, and a rectangular lifting spreader on cables below it. NO operator cab, NO ladders, NO stairs, NO catwalks, NO handrails.'
       Anchor  = 'Scale: the portal stands over a small aircraft with room either side and lifts it clear. Massive box steelwork, not a light lattice mast. Nothing on it is built for a person to climb.' }
)

# VALIDATE BEFORE ANY SIDE EFFECT. The first run of this lane created
# the result root and THEN found a prompt was 814 characters, leaving an
# empty directory that its own "already exists" guard refused to run
# over. Everything checkable offline is checked here, before the
# directory is made or a single credit is touched.
foreach ($Job in $Jobs) {
    $Check = "Game-ready heavy industrial machine, clean futuristic spacecraft factory. $($Job.Subject) $($Job.Anchor)`n$Style"
    if ($Check.Trim().Length -gt 800) {
        throw "Prompt for $($Job.Name) is $($Check.Trim().Length) chars; the API caps at 800. Nothing was created."
    }
}

$ApiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($ApiKey)) { throw 'Meshy API key file is empty.' }
$Headers = @{ Authorization = "Bearer $ApiKey" }
$BalanceBefore = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$Manifest = @()
foreach ($Job in $Jobs) {
    $Prompt = "Game-ready heavy industrial machine, clean futuristic spacecraft factory. $($Job.Subject) $($Job.Anchor)`n$Style"
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
    '$schema'      = 'lineboss/audit/meshy-gantry-crane-v003/v1'
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
    '$schema'      = 'lineboss/audit/meshy-gantry-crane-v003/v1'
    generated_utc  = (Get-Date).ToUniversalTime().ToString('o')
    status         = if ($Succeeded -eq $Jobs.Count) { 'PASS__GANTRY_CRANE_PREVIEW_GENERATED' } else { 'PARTIAL__GANTRY_CRANE_PREVIEW' }
    balance_before = $BalanceBefore
    balance_after  = $BalanceAfter
    credits_spent  = $BalanceBefore - $BalanceAfter
    results        = $Results
    not_proven     = @(
        'Previews only - untextured draft geometry, not refined. Nobody has looked at them yet; identity and quality are confirmed by RENDER, never by filename.',
        'No promotion: nothing is imported into Content until the renders confirm what each file actually is, and the owner confirms which is which.',
        'The crate prompts fight the generator''s habit of stencilling part numbers and hazard symbols onto boxes. If ANY drop comes back with lettering it is rejected outright - the game ships translated and bakes no text into textures.'
    )
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'generation_receipt.json') -Encoding UTF8
Write-Output "SPENT $($BalanceBefore - $BalanceAfter) credits; $Succeeded/$($Jobs.Count) succeeded; balance now $BalanceAfter"
