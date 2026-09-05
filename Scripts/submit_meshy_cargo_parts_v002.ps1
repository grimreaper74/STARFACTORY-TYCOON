# Re-generate the ONE preview that missed from CargoParts_v001: the
# thruster pod came back as a boxy valve-fitting hub with two round
# ports and no visible exhaust cone - not a thruster (owner review,
# 2026-09-03, judged on the render, not the filename). Same lane, same
# style block, one subject only, prompt rewritten to force the one
# shape a thruster cannot be mistaken without: a flared exhaust bell.
param(
    [Parameter(Mandatory = $true)][string]$Acknowledgement,
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft\CargoParts_v002',
    [int]$PollSeconds = 20,
    [int]$TimeoutMinutes = 40
)
$ErrorActionPreference = 'Stop'
if ($Acknowledgement -ne 'I ACCEPT MESHY CREDIT SPEND FOR CARGO PARTS V002') {
    throw 'Acknowledgement string does not match; refusing to spend credits.'
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Result root already exists: $OutputRoot. Author v003 rather than rerunning."
}

$Style = @'
Style: clean futuristic industrial spacecraft hardware. Pale grey and white panels, graphite framing, recessed blue-white light strips, sparing safety-orange. New and clean, not battle-worn. Matte metal, one closed object, symmetrical. No text, letters, numbers, logos. No ground plane, no scenery, no figures, no whole spacecraft - this is a single detached FITTING, on its own.
'@

$Jobs = @(
    @{ Name = 'ThrusterPod02_Single'
       Subject = 'A single small ROCKET THRUSTER for a spacecraft flank: a plain cylindrical body with a CONE-SHAPED EXHAUST NOZZLE flared outward at the REAR like a rocket engine bell, and a flat round mounting collar at the FRONT. No boxes, no valves, no side ports.'
       Anchor  = 'Scale: about as long as a person - a slim engine bell, not a machine housing.' }
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
    '$schema'      = 'lineboss/audit/meshy-cargo-parts-v002/v1'
    generated_utc  = (Get-Date).ToUniversalTime().ToString('o')
    status         = if ($Succeeded -eq $Jobs.Count) { 'PASS__CARGO_PARTS_PREVIEWS_GENERATED' } else { 'PARTIAL__CARGO_PARTS_PREVIEWS' }
    balance_before = $BalanceBefore
    balance_after  = $BalanceAfter
    credits_spent  = $BalanceBefore - $BalanceAfter
    results        = $Results
    not_proven     = @(
        'Preview only - untextured draft geometry, not refined. Identity confirmed by RENDER, never by filename.',
        'No promotion: nothing is imported into Content until the render confirms what it is, sized to its socket and verified at import.'
    )
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'generation_receipt.json') -Encoding UTF8
Write-Output "SPENT $($BalanceBefore - $BalanceAfter) credits; $Succeeded/$($Jobs.Count) succeeded; balance now $BalanceAfter"
