param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$BatchRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\Meshy_S03_ComponentBatch_v624',
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'
$manifestPath = Join-Path $BatchRoot 'batch_manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$apiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($apiKey)) { throw 'Meshy API key file is empty.' }
$headers = @{ Authorization = "Bearer $apiKey" }
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)

try {
    do {
        $pending = 0
        $summary = @()
        foreach ($item in $manifest) {
            $task = Invoke-RestMethod -Uri ("https://api.meshy.ai/openapi/v1/multi-image-to-3d/" + $item.TaskId) -Headers $headers
            $summary += [pscustomobject]@{ Name=$item.Name; TaskId=$item.TaskId; Status=$task.status; Progress=$task.progress; Credits=$task.consumed_credits }
            if ($task.status -in @('PENDING','IN_PROGRESS')) { $pending++ }
            if ($task.status -eq 'SUCCEEDED') {
                $jobDir = Join-Path $BatchRoot $item.Name
                $metadataPath = Join-Path $jobDir 'task_complete.json'
                $task | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $metadataPath -Encoding utf8
                $downloads = @{
                    'model.glb' = $task.model_urls.glb
                    'model_pre_remeshed.glb' = $task.model_urls.pre_remeshed_glb
                    'preview.png' = $task.thumbnail_url
                    'preview_front.png' = $task.thumbnail_urls.front
                    'preview_right.png' = $task.thumbnail_urls.right
                    'preview_back.png' = $task.thumbnail_urls.back
                    'preview_left.png' = $task.thumbnail_urls.left
                }
                foreach ($download in $downloads.GetEnumerator()) {
                    if ($download.Value) {
                        $target = Join-Path $jobDir $download.Key
                        if (-not (Test-Path -LiteralPath $target)) {
                            Invoke-WebRequest -Uri $download.Value -OutFile $target
                        }
                    }
                }
            }
        }
        $summary | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $BatchRoot 'batch_status.json') -Encoding utf8
        Write-Output (($summary | ForEach-Object { "{0}:{1}:{2}%" -f $_.Name,$_.Status,$_.Progress }) -join ' | ')
        if ($pending -gt 0 -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 15 }
    } while ($pending -gt 0 -and (Get-Date) -lt $deadline)

    if ($pending -gt 0) { throw "Timed out with $pending unfinished Meshy tasks." }
} finally {
    $apiKey = $null
    $headers = $null
}

Write-Output ("COMPLETE " + (Join-Path $BatchRoot 'batch_status.json'))
