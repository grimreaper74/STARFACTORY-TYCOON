param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\Meshy_S03_ComponentBatch_v624'
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$jobs = @(
    @{ Name='Asset01_StaticPressShell'; Source='C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 09_17_27 AM (2).png'; Crops=@(@(15,15,600,545),@(640,15,600,545),@(120,575,470,555),@(680,575,470,555)) },
    @{ Name='Asset02_RamSlide'; Source='C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 09_17_27 AM (3).png'; Crops=@(@(15,45,600,525),@(635,45,600,525),@(145,625,420,500),@(695,625,420,500)) },
    @{ Name='Asset03_BolsterToolingPlate'; Source='C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 09_17_28 AM (4).png'; Crops=@(@(25,35,1200,280),@(25,345,1200,280),@(45,675,1160,235),@(45,935,1160,215)) },
    @{ Name='Asset04_UpperLowerDie'; Source='C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 09_17_28 AM (5).png'; Crops=@(@(20,70,600,510),@(635,70,600,510),@(20,620,600,500),@(635,620,600,500)) },
    @{ Name='Asset05_FlywheelDriveCover'; Source='C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 09_17_29 AM (6).png'; Crops=@(@(45,45,550,500),@(650,45,550,500),@(80,615,500,490),@(675,615,500,490)) },
    @{ Name='Asset06_AccessDoors'; Source='C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 09_17_29 AM (7).png'; Crops=@(@(80,40,485,510),@(680,40,485,510),@(205,610,270,500),@(790,610,270,500)) },
    @{ Name='Asset07_SafetyGuardsGates'; Source='C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 09_17_30 AM (8).png'; Crops=@(@(25,25,580,445),@(645,25,580,445),@(190,545,330,480),@(740,545,330,480)) },
    @{ Name='Asset08_ConsoleElectricalCabinet'; Source='C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 09_17_31 AM (9).png'; Crops=@(@(65,45,520,515),@(660,45,520,515),@(130,610,490,500),@(650,610,490,500)) }
)

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$apiKey = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($apiKey)) { throw 'Meshy API key file is empty.' }
$headers = @{ Authorization = "Bearer $apiKey" }
$manifest = @()

try {
    foreach ($job in $jobs) {
        if (-not (Test-Path -LiteralPath $job.Source)) { throw "Missing source: $($job.Source)" }
        $jobDir = Join-Path $OutputRoot $job.Name
        New-Item -ItemType Directory -Path $jobDir -Force | Out-Null
        Copy-Item -LiteralPath $job.Source -Destination (Join-Path $jobDir 'source_sheet.png') -Force

        $sourceImage = [System.Drawing.Image]::FromFile($job.Source)
        $dataUris = @()
        $viewNames = @('front','rear','left','right')
        try {
            for ($i = 0; $i -lt 4; $i++) {
                $c = $job.Crops[$i]
                $rect = New-Object System.Drawing.Rectangle($c[0],$c[1],$c[2],$c[3])
                $bitmap = New-Object System.Drawing.Bitmap($rect.Width,$rect.Height)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                try {
                    $graphics.Clear([System.Drawing.Color]::White)
                    $graphics.DrawImage($sourceImage, (New-Object System.Drawing.Rectangle(0,0,$rect.Width,$rect.Height)), $rect, [System.Drawing.GraphicsUnit]::Pixel)
                    $cropPath = Join-Path $jobDir ($viewNames[$i] + '.png')
                    $bitmap.Save($cropPath, [System.Drawing.Imaging.ImageFormat]::Png)
                    $bytes = [System.IO.File]::ReadAllBytes($cropPath)
                    $dataUris += 'data:image/png;base64,' + [Convert]::ToBase64String($bytes)
                } finally {
                    $graphics.Dispose()
                    $bitmap.Dispose()
                }
            }
        } finally {
            $sourceImage.Dispose()
        }

        $payload = @{
            image_urls = $dataUris
            ai_model = 'meshy-6'
            should_texture = $true
            enable_pbr = $true
            texture_resolution = '4k'
            target_formats = @('glb')
            should_remesh = $false
            symmetry_mode = 'auto'
            image_enhancement = $false
            texture_prompt = 'Industrial automotive stamping press component. Preserve dark green painted steel, charcoal housings, safety yellow guards, machined steel working surfaces, and light grey electrical cabinets. No floor, background, labels, text, people, or surrounding machinery.'
        } | ConvertTo-Json -Depth 5

        $response = Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/multi-image-to-3d' -Headers $headers -Method Post -ContentType 'application/json' -Body $payload
        $entry = [ordered]@{ Name=$job.Name; TaskId=$response.result; Status='SUBMITTED'; Source=$job.Source }
        $manifest += [pscustomobject]$entry
        $entry | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $jobDir 'task.json') -Encoding utf8
        Write-Output ("SUBMITTED {0} {1}" -f $job.Name,$response.result)
    }
} finally {
    $apiKey = $null
    $headers = $null
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputRoot 'batch_manifest.json') -Encoding utf8
Write-Output ("MANIFEST " + (Join-Path $OutputRoot 'batch_manifest.json'))
