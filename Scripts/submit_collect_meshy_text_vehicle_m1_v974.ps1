param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Vehicles\M1_Moorcross\MeshyTextPreview_v974',
    [int]$PollSeconds = 10,
    [int]$TimeoutMinutes = 45
)

$ErrorActionPreference = 'Stop'
$Prompt = @'
Original 2042 near-future production EV, isolated whole car. Practical five-door C-segment hatchback: 4.38m long, 1.82m wide, 1.45m high, 2.72m wheelbase, compact overhangs and road tyres. Mass-producible smooth stamped-steel aero body, closed nose, thin full-width front/rear LED blades, windscreen sensor strip, flush handles, camera-mirror pods, panoramic roof, aero wheels, graphite lower trim, four normal doors and rear hatch. Wheels straight, circular and grounded on one plane; all closures shut. No driver, scenery, plinth, text, logo, loose parts, gullwings, exposed wheels, levitation or race-car shape. Clean watertight exterior for later body, closures, glass, lights and wheel separation. Untextured preview.
'@

if (-not (Test-Path -LiteralPath $ApiKeyPath)) { throw "Meshy API key file is missing: $ApiKeyPath" }
$Key = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($Key)) { throw 'Meshy API key file is empty.' }
$Headers = @{ Authorization = "Bearer $Key" }

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$SubmissionPath = Join-Path $OutputRoot 'submission.json'
if (Test-Path -LiteralPath $SubmissionPath) { throw 'Refusing duplicate paid Meshy M1 v974 submission.' }

$BalanceBefore = [int](Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
if ($BalanceBefore -lt 20) { throw "Need 20 Meshy credits for text preview; balance is $BalanceBefore." }

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
    asset = 'Cairnwell_M1_Moorcross_2042'
    mode = 'preview'
    task_id = $TaskId
    submitted_utc = (Get-Date).ToUniversalTime().ToString('o')
    expected_credits = 20
    balance_before = $BalanceBefore
    prompt = $Prompt.Trim()
    settings = @{ endpoint = '/openapi/v2/text-to-3d'; target_formats = @('glb','fbx'); textured = $false }
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $SubmissionPath -Encoding UTF8

$Deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$Task = $null
do {
    $Task = Invoke-RestMethod -Uri ("https://api.meshy.ai/openapi/v2/text-to-3d/" + $TaskId) -Headers $Headers
    @{ id=$Task.id; status=$Task.status; progress=$Task.progress; consumed_credits=$Task.consumed_credits } `
        | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputRoot 'task_latest.json') -Encoding UTF8
    Write-Output "STATUS $($Task.status) progress=$($Task.progress)"
    if ($Task.status -in @('SUCCEEDED','FAILED','CANCELED')) { break }
    Start-Sleep -Seconds $PollSeconds
} while ((Get-Date) -lt $Deadline)

if (-not $Task -or $Task.status -ne 'SUCCEEDED') {
    throw "Meshy M1 text preview did not succeed; final status=$($Task.status)"
}

if ($Task.model_urls.glb) {
    Invoke-WebRequest -Uri $Task.model_urls.glb -OutFile (Join-Path $OutputRoot 'Cairnwell_M1_Moorcross_2042_MeshyTextPreview_v974.glb')
}
if ($Task.model_urls.fbx) {
    Invoke-WebRequest -Uri $Task.model_urls.fbx -OutFile (Join-Path $OutputRoot 'Cairnwell_M1_Moorcross_2042_MeshyTextPreview_v974.fbx')
}
if ($Task.thumbnail_url) {
    Invoke-WebRequest -Uri $Task.thumbnail_url -OutFile (Join-Path $OutputRoot 'MeshyTextPreview_v974.png')
}
$Task | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $OutputRoot 'task_complete.json') -Encoding UTF8

$BalanceAfter = [int](Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
$Summary = @{
    revision = 'v974'
    status = 'SUCCEEDED_UNTEXTURED_PREVIEW_PENDING_BLENDER_REVIEW'
    task_id = $TaskId
    consumed_credits_reported = $Task.consumed_credits
    balance_before = $BalanceBefore
    balance_after = $BalanceAfter
    observed_balance_delta = $BalanceBefore - $BalanceAfter
    refine_submitted = $false
}
$Summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputRoot 'summary_v974.json') -Encoding UTF8
$Summary | ConvertTo-Json -Depth 6
