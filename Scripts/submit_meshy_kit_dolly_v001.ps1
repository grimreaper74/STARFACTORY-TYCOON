# Generate the KIT DOLLY and its PART-SET CRATES (owner 2026-08-28:
# "use meshy if you need the part sets or dolly's", after settling that
# "all the parts for that station for each ship has its own dolly of
# parts").
#
# These are currently engine cubes: a deck block, four wheel blocks, a
# drawbar and eight crate blocks. The arrangement is right and proven on
# screen - eight countable crates in two bays - so this replaces the
# BLOCKS, not the design.
#
# ONE CART PER COMPONENT BAY, not one stretched cart per station. A
# station fits one or two components, so a single mesh would have to
# stretch to fit and stretched wheels read badly. A cart per kit is also
# what real plants do - dollies are coupled into a train behind a tug -
# so a two-component station simply gets two carts.
#
# GEOMETRY ONLY. Materials are authored in Unreal (owner's standing
# direction), so nothing here is refined for its maps; these take the
# project palette at import, and their base-colour maps are used only as
# panel MASKS.
#
# THE CRATE PROMPT FIGHTS THE GENERATOR'S STRONGEST HABIT. Asked for an
# industrial crate, every generator stencils part numbers, arrows and
# fragile symbols on the side. This game ships translated and bakes NO
# text into any texture, so the no-text constraint is repeated in the
# subject line as well as the style block - the one place it keeps being
# broken.
#
# SCALE BY COMPARISON, not by count - the ground-drone lesson. A
# generator ignores "about a metre" and respects "the size of a washing
# machine".
#
# One-shot and fail-closed like every other lane here: refuses to run
# over an existing result root, refuses without an acknowledgement,
# records a receipt with the credit cost of every task.

param(
    [Parameter(Mandatory = $true)][string]$Acknowledgement,
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Spacecraft\KitDolly_v001',
    [int]$PollSeconds = 20,
    [int]$TimeoutMinutes = 25
)

$ErrorActionPreference = 'Stop'
if ($Acknowledgement -ne 'I ACCEPT MESHY CREDIT SPEND FOR KIT DOLLY V001') {
    throw 'Acknowledgement string does not match; refusing to spend credits.'
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Result root already exists: $OutputRoot. Author v002 rather than rerunning."
}

# Compressed style block - the API caps a prompt at 800 characters.
$Style = @'
Style: pale grey and white panels, graphite frame, sparing safety
orange. Clean and new, not grimy. Neutral tones, no brand colour. Matte
painted metal, single object, flat bottom. No text, letters, numbers,
barcodes or logos. No ground plane, scenery, figures or forklifts.
'@

$Jobs = @(
    # THE CART. Deliberately EMPTY: the crates are placed per slot from
    # live stock, so a cart modelled with cargo on it would contradict
    # the one thing this whole system exists to show.
    @{ Name = 'Dolly01_KitCart'
       Subject = 'An EMPTY low industrial parts trolley: a flat rectangular deck with a shallow lip, four low corner posts, a tubular frame underneath, four small swivel castor wheels and a tow handle at one short end. The deck is bare.'
       Anchor  = 'Scale: the deck is about the size of a double bed and sits at knee height. Nothing is loaded on it - the deck must be empty and flat.' }
    # THE CLOSED CRATE - the default, and what most slots hold.
    @{ Name = 'Crate01_PartSet'
       Subject = 'A single closed stackable industrial shipping container: a square ribbed box with a slightly recessed lid, moulded corner feet, two recessed side handles and four latch clasps. Completely blank surfaces with absolutely no writing, labels or markings of any kind.'
       Anchor  = 'Scale: about the size of a washing machine, slightly wider than it is tall. One box only, closed, standing upright and alone.' }
    # AN OPEN TOTE, so eight slots are not eight identical boxes. The
    # contents are deliberately vague - a specific part sculpted into
    # the tote would be wrong for every set except one.
    @{ Name = 'Crate02_OpenTote'
       Subject = 'A single open-topped industrial parts tote: a square ribbed bin with no lid, a rolled rim, moulded corner feet and two recessed side handles, holding neatly stacked anonymous grey machined blanks that sit below the rim. Blank surfaces with no writing or labels.'
       Anchor  = 'Scale: about the size of a washing machine. One bin only, standing upright and alone, contents flush and tidy, nothing spilling over the rim.' }
)

# VALIDATE BEFORE ANY SIDE EFFECT. The first run of this lane created
# the result root and THEN found a prompt was 814 characters, leaving an
# empty directory that its own "already exists" guard refused to run
# over. Everything checkable offline is checked here, before the
# directory is made or a single credit is touched.
foreach ($Job in $Jobs) {
    $Check = "Game-ready factory logistics prop, clean futuristic spacecraft factory. $($Job.Subject) $($Job.Anchor)`n$Style"
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
    $Prompt = "Game-ready factory logistics prop, clean futuristic spacecraft factory. $($Job.Subject) $($Job.Anchor)`n$Style"
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
    '$schema'      = 'lineboss/audit/meshy-kit-dolly-v001/v1'
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
    '$schema'      = 'lineboss/audit/meshy-kit-dolly-v001/v1'
    generated_utc  = (Get-Date).ToUniversalTime().ToString('o')
    status         = if ($Succeeded -eq $Jobs.Count) { 'PASS__KIT_DOLLY_PREVIEWS_GENERATED' } else { 'PARTIAL__KIT_DOLLY_PREVIEWS' }
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
