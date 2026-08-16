param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$InputImage = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\Meshy_S03_ComponentBatch_v624\Asset01_StaticPressShell\front.png',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\Meshy_S03_SmartTopologyTrial_v627',
    [ValidateRange(100,15000)][int]$TargetPolycount = 15000
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $InputImage)) { throw "Input image not found: $InputImage" }
$apiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($apiKey)) { throw 'Meshy API key file is empty.' }

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$bytes = [System.IO.File]::ReadAllBytes($InputImage)
$extension = [System.IO.Path]::GetExtension($InputImage).ToLowerInvariant()
$mime = if ($extension -eq '.png') { 'image/png' } else { 'image/jpeg' }
$dataUri = "data:$mime;base64," + [Convert]::ToBase64String($bytes)

$payload = @{
    image_url = $dataUri
    model_type = 'smart-topology'
    ai_model = 'meshy-t2'
    target_polycount = $TargetPolycount
    should_texture = $false
    target_formats = @('glb')
} | ConvertTo-Json -Depth 4

$headers = @{ Authorization = "Bearer $apiKey"; 'Content-Type' = 'application/json' }
try {
    $response = Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/image-to-3d' -Method Post -Headers $headers -Body $payload
    $record = [ordered]@{
        submitted_at_utc = (Get-Date).ToUniversalTime().ToString('o')
        task_id = $response.result
        input_image = $InputImage
        model_type = 'smart-topology'
        ai_model = 'meshy-t2'
        target_polycount = $TargetPolycount
        should_texture = $false
        expected_generation_credits = 5
        status = 'SUBMITTED'
    }
    $record | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputRoot 'submission.json') -Encoding utf8
    Write-Output ("SUBMITTED task=" + $response.result)
}
finally {
    $apiKey = $null
    $headers = $null
    $payload = $null
    $dataUri = $null
    $bytes = $null
}
