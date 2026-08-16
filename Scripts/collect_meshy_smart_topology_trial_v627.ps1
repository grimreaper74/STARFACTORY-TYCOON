param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\Meshy_S03_SmartTopologyTrial_v627',
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'
$submissionPath = Join-Path $OutputRoot 'submission.json'
$submission = Get-Content -LiteralPath $submissionPath -Raw | ConvertFrom-Json
$apiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($apiKey)) { throw 'Meshy API key file is empty.' }
$headers = @{ Authorization = "Bearer $apiKey" }
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)

try {
    do {
        $task = Invoke-RestMethod -Uri ("https://api.meshy.ai/openapi/v1/image-to-3d/" + $submission.task_id) -Headers $headers
        Write-Output ("STATUS " + $task.status + " " + $task.progress + "%")
        if ($task.status -in @('PENDING','IN_PROGRESS')) { Start-Sleep -Seconds 10 }
    } while ($task.status -in @('PENDING','IN_PROGRESS') -and (Get-Date) -lt $deadline)

    if ($task.status -in @('PENDING','IN_PROGRESS')) { throw 'Timed out waiting for Meshy trial.' }
    $task | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $OutputRoot 'task_complete.json') -Encoding utf8
    if ($task.status -ne 'SUCCEEDED') { throw "Meshy task ended with status: $($task.status)" }

    $target = Join-Path $OutputRoot 'model.glb'
    Invoke-WebRequest -Uri $task.model_urls.glb -OutFile $target
    Copy-Item -LiteralPath $task.thumbnail_url -Destination (Join-Path $OutputRoot 'preview.png') -ErrorAction SilentlyContinue
    Write-Output ("COMPLETE credits=" + $task.consumed_credits + " model=" + $target)
}
finally {
    $apiKey = $null
    $headers = $null
}
