param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$SourceRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\TrainA\MeshySupportingSystemsReferences_v634',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\TrainA\Meshy6SupportingSystemsProduction_v638',
    [string]$RecoveredS01TaskId = '019fe175-5280-7070-942f-18656d4f5426',
    [int]$PollSeconds = 10,
    [int]$TimeoutMinutes = 45
)

$ErrorActionPreference = 'Stop'
$assets = @(
    @{ Id='S01_DESTACK'; Folder='Asset01_S01DestackBlankFeed'; Output='01_S01DestackBlankFeed' },
    @{ Id='INTERPRESS_TRANSFER'; Folder='Asset02_InterPressTransferSystem'; Output='02_InterPressTransferSystem' },
    @{ Id='S04_SCRAP_SYSTEM'; Folder='Asset03_S04TrimScrapSystem'; Output='03_S04TrimScrapSystem' },
    @{ Id='S05_SLUG_SYSTEM'; Folder='Asset04_S05SlugCollectionSystem'; Output='04_S05SlugCollectionSystem' },
    @{ Id='S07_INSPECT_UNLOAD'; Folder='Asset05_S07InspectUnloadCell'; Output='05_S07InspectUnloadCell' }
)
$views = @('front','rear','left','right')
$key = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($key)) { throw 'Meshy API key file is empty.' }
$headers = @{ Authorization = "Bearer $key" }
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

function Get-DataUri([string]$Path) {
    $bytes = [IO.File]::ReadAllBytes($Path)
    return 'data:image/png;base64,' + [Convert]::ToBase64String($bytes)
}

$balanceBefore = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $headers).balance
if ([int]$balanceBefore -lt 150) { throw "Need 150 Meshy credits for P0; balance is $balanceBefore." }

$jobs = @()
foreach ($asset in $assets) {
    $sourceDir = Join-Path $SourceRoot $asset.Folder
    $outputDir = Join-Path $OutputRoot $asset.Output
    $originalDir = Join-Path $outputDir 'Original'
    New-Item -ItemType Directory -Path $originalDir -Force | Out-Null
    $uris = @()
    $sourceRecords = @()
    foreach ($view in $views) {
        $source = Join-Path $sourceDir ($view + '.png')
        if (-not (Test-Path -LiteralPath $source)) { throw "Missing source view: $source" }
        Copy-Item -LiteralPath $source -Destination (Join-Path $originalDir ($view + '.png')) -Force
        $uris += Get-DataUri $source
        $sourceRecords += [ordered]@{ view=$view; file=$source; sha256=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash }
    }
    $payload = [ordered]@{
        image_urls = $uris
        ai_model = 'meshy-6'
        should_texture = $true
        enable_pbr = $true
        texture_resolution = '2k'
        should_remesh = $false
        image_enhancement = $false
        remove_lighting = $true
        target_formats = @('glb','fbx')
    }
    $submissionFile = Join-Path $outputDir 'submission.json'
    if ($asset.Id -eq 'S01_DESTACK' -and -not [string]::IsNullOrWhiteSpace($RecoveredS01TaskId)) {
        $taskId = $RecoveredS01TaskId
    } elseif (Test-Path -LiteralPath $submissionFile) {
        $taskId = (Get-Content -LiteralPath $submissionFile -Raw | ConvertFrom-Json).task_id
    } else {
        $created = Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/multi-image-to-3d' -Headers $headers -Method Post -ContentType 'application/json' -Body ($payload | ConvertTo-Json -Depth 5 -Compress)
        $taskId = $created.result
    }
    $settings = [ordered]@{}
    foreach ($keyName in $payload.Keys) { if ($keyName -ne 'image_urls') { $settings[$keyName] = $payload[$keyName] } }
    $job = [ordered]@{
        id=$asset.Id; task_id=$taskId; output_dir=$outputDir; submitted_utc=(Get-Date).ToUniversalTime().ToString('o');
        status='SUBMITTED'; expected_credits=30; sources=$sourceRecords; settings=$settings
    }
    $job | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $submissionFile -Encoding UTF8
    $jobs += $job
    Write-Output "TRACKING $($asset.Id) $taskId"
}

$deadline = (Get-Date).AddMinutes($TimeoutMinutes)
while ((Get-Date) -lt $deadline) {
    $pending = 0
    foreach ($job in $jobs) {
        if ($job.status -in @('SUCCEEDED','FAILED','CANCELED')) { continue }
        $task = Invoke-RestMethod -Uri ("https://api.meshy.ai/openapi/v1/multi-image-to-3d/" + $job.task_id) -Headers $headers
        $job.status = $task.status
        $task | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $job.output_dir 'task_latest.json') -Encoding UTF8
        if ($task.status -eq 'SUCCEEDED') {
            if ($task.model_urls.glb) { Invoke-WebRequest -Uri $task.model_urls.glb -OutFile (Join-Path $job.output_dir ($job.id + '_Meshy6_Raw.glb')) }
            if ($task.model_urls.fbx) { Invoke-WebRequest -Uri $task.model_urls.fbx -OutFile (Join-Path $job.output_dir ($job.id + '_Meshy6_Raw.fbx')) }
            $task | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $job.output_dir 'task_complete.json') -Encoding UTF8
            Write-Output "SUCCEEDED $($job.id) credits=$($task.consumed_credits)"
        } elseif ($task.status -in @('FAILED','CANCELED')) {
            Write-Output "FAILED $($job.id) status=$($task.status)"
        } else { $pending++ }
    }
    if ($pending -eq 0) { break }
    Start-Sleep -Seconds $PollSeconds
}

$balanceAfter = (Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $headers).balance
$summary = [ordered]@{
    revision='v638'; generated_utc=(Get-Date).ToUniversalTime().ToString('o'); balance_before=$balanceBefore; balance_after=$balanceAfter;
    status=if(($jobs | Where-Object {$_.status -ne 'SUCCEEDED'}).Count -eq 0){'ALL_SUCCEEDED'}else{'INCOMPLETE'};
    jobs=$jobs | ForEach-Object {[ordered]@{id=$_.id;task_id=$_.task_id;status=$_.status;output_dir=$_.output_dir}}
}
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'BATCH_SUMMARY_v638.json') -Encoding UTF8
$summary | ConvertTo-Json -Depth 8
if ($summary.status -ne 'ALL_SUCCEEDED') { exit 2 }
