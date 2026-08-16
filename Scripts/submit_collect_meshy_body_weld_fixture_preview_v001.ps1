param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\WeldShop\BodyWeldFramingFixture_MeshyTextPreview_v001',
    [int]$PollSeconds = 10,
    [int]$TimeoutMinutes = 45
)

$ErrorActionPreference = 'Stop'
$Prompt = @'
Automotive body-framing geometry-weld fixture for a modern electric crossover SUV. Heavy rectangular floor base, four rigid corner towers, adjustable locating pins, pneumatic toggle clamps, side-frame and roof-header supports, datum blocks, linear slides, cable conduits and service platforms. Holds an EV underbody and body-side structures square during robotic spot welding. Bright medium-grey steel, charcoal frames, fixed safety-yellow handles and guards; avoid dark overall textures. Keep base, towers, clamp arms and locators visually separate with clean mechanical joints. Full isolated machine, three-quarter isometric studio view, neutral light-grey background. No car body, panels, robots, welding guns, workers, conveyor, factory, text, logos or watermark. Untextured geometry preview.
'@

if (-not (Test-Path -LiteralPath $ApiKeyPath)) { throw "Meshy API key file is missing: $ApiKeyPath" }
$Key = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($Key)) { throw 'Meshy API key file is empty.' }
$Headers = @{ Authorization = "Bearer $Key" }

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$SubmissionPath = Join-Path $OutputRoot 'submission.json'
if (Test-Path -LiteralPath $SubmissionPath) {
    throw "Refusing duplicate paid Meshy Body Weld fixture submission: $SubmissionPath"
}

$BalanceBefore = [int](Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
if ($BalanceBefore -lt 20) { throw "Need 20 Meshy credits for the text preview; balance is $BalanceBefore." }

$Payload = @{
    mode = 'preview'
    prompt = $Prompt.Trim()
    target_formats = @('glb', 'fbx')
} | ConvertTo-Json -Depth 5 -Compress

$Created = Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v2/text-to-3d' `
    -Headers $Headers -Method Post -ContentType 'application/json' -Body $Payload
$TaskId = [string]$Created.result
if ([string]::IsNullOrWhiteSpace($TaskId)) { throw 'Meshy returned no text-to-3D task id.' }

@{
    asset = 'Cairnwell_2040_BodyWeld_FramingFixture'
    role = 'Body-weld framing fixture'
    revision = 'v001'
    mode = 'preview'
    task_id = $TaskId
    submitted_utc = (Get-Date).ToUniversalTime().ToString('o')
    expected_credits = 20
    balance_before = $BalanceBefore
    prompt = $Prompt.Trim()
    settings = @{
        endpoint = '/openapi/v2/text-to-3d'
        target_formats = @('glb', 'fbx')
        textured = $false
    }
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $SubmissionPath -Encoding UTF8

$Deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$Task = $null
do {
    $Task = Invoke-RestMethod -Uri ("https://api.meshy.ai/openapi/v2/text-to-3d/" + $TaskId) -Headers $Headers
    @{
        id = $Task.id
        status = $Task.status
        progress = $Task.progress
        consumed_credits = $Task.consumed_credits
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputRoot 'task_latest.json') -Encoding UTF8
    Write-Output "STATUS $($Task.status) progress=$($Task.progress)"
    if ($Task.status -in @('SUCCEEDED', 'FAILED', 'CANCELED')) { break }
    Start-Sleep -Seconds $PollSeconds
} while ((Get-Date) -lt $Deadline)

if (-not $Task -or $Task.status -ne 'SUCCEEDED') {
    throw "Meshy Body Weld fixture preview did not succeed; final status=$($Task.status)"
}

if ($Task.model_urls.glb) {
    Invoke-WebRequest -Uri $Task.model_urls.glb -OutFile (Join-Path $OutputRoot 'LB_C2040_BodyWeldFramingFixture_MeshyPreview_v001.glb')
}
if ($Task.model_urls.fbx) {
    Invoke-WebRequest -Uri $Task.model_urls.fbx -OutFile (Join-Path $OutputRoot 'LB_C2040_BodyWeldFramingFixture_MeshyPreview_v001.fbx')
}
if ($Task.thumbnail_url) {
    Invoke-WebRequest -Uri $Task.thumbnail_url -OutFile (Join-Path $OutputRoot 'LB_C2040_BodyWeldFramingFixture_MeshyPreview_v001.png')
}
$Task | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $OutputRoot 'task_complete.json') -Encoding UTF8

$BalanceAfter = [int](Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
$Summary = @{
    revision = 'v001'
    role = 'Body-weld framing fixture'
    status = 'SUCCEEDED_UNTEXTURED_PREVIEW_PENDING_GEOMETRY_REVIEW'
    task_id = $TaskId
    consumed_credits_reported = $Task.consumed_credits
    balance_before = $BalanceBefore
    balance_after = $BalanceAfter
    observed_balance_delta = $BalanceBefore - $BalanceAfter
    refine_submitted = $false
    texture_submitted = $false
    unreal_imported = $false
}
$Summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputRoot 'summary_v001.json') -Encoding UTF8
$Summary | ConvertTo-Json -Depth 6
