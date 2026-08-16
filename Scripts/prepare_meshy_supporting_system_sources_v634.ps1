param(
    [string]$OutputRoot = "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\TrainA\MeshySupportingSystemsReferences_v634"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$sources = @{
    S01       = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_15 AM (1).png"
    Transfer  = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_15 AM (2).png"
    Scrap     = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_16 AM (3).png"
    Slug      = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_16 AM (4).png"
    Inspect   = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_16 AM (5).png"
    DieCart   = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_16 AM (6).png"
    HPU       = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_17 AM (7).png"
    Platform  = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_17 AM (8).png"
    Stillages = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_17 AM (9).png"
    Conveyor  = "C:\Users\greg_\Downloads\ChatGPT Image Aug 8, 2026, 11_13_17 AM (10).png"
}

foreach ($path in $sources.Values) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing source: $path" }
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$originalRoot = Join-Path $OutputRoot "OriginalSheets"
New-Item -ItemType Directory -Force -Path $originalRoot | Out-Null

foreach ($entry in $sources.GetEnumerator()) {
    Copy-Item -LiteralPath $entry.Value -Destination (Join-Path $originalRoot ($entry.Key + ".png")) -Force
}

function New-CropSpec([string]$View, [int]$X, [int]$Y, [int]$W, [int]$H) {
    return [ordered]@{ view=$View; x=$X; y=$Y; width=$W; height=$H }
}

$quadrants = @(
    (New-CropSpec "front" 10 10 607 607),
    (New-CropSpec "rear" 637 10 607 607),
    (New-CropSpec "left" 10 637 607 607),
    (New-CropSpec "right" 637 637 607 607)
)

$assets = @(
    [ordered]@{ name="Asset01_S01DestackBlankFeed"; source=$sources.S01; crops=$quadrants; notes="Complete destack/feed cell; retain vacuum and separator tooling as visible subassemblies." },
    [ordered]@{ name="Asset02_InterPressTransferSystem"; source=$sources.Transfer; crops=$quadrants; notes="Complete transfer gantry reference; moving crossbar and gripper must be separated after generation." },
    [ordered]@{ name="Asset03_S04TrimScrapSystem"; source=$sources.Scrap; crops=$quadrants; notes="Scrap chute and conveyor assembly; removable bin excluded from primary crop where practical." },
    [ordered]@{ name="Asset04_S05SlugCollectionSystem"; source=$sources.Slug; crops=$quadrants; notes="Slug collector/cyclone cell; bin treated as a detachable gameplay asset." },
    [ordered]@{ name="Asset05_S07InspectUnloadCell"; source=$sources.Inspect; crops=$quadrants; notes="Inspection/unload gantry and conveyor; sensor heads and turntable remain distinct moving modules." },
    [ordered]@{ name="Asset06_DieChangeCart"; source=$sources.DieCart; crops=@(
        (New-CropSpec "front" 15 120 470 400), (New-CropSpec "rear" 642 120 470 400),
        (New-CropSpec "left" 15 747 470 400), (New-CropSpec "right" 642 747 470 400)
    ); notes="Cart only. Detached locator/upright intentionally excluded to prevent fused geometry." },
    [ordered]@{ name="Asset07_HydraulicPowerUnit"; source=$sources.HPU; crops=$quadrants; notes="Reusable hydraulic power unit shared by press stations." },
    [ordered]@{ name="Asset08_ServicePlatformCagedLadder"; source=$sources.Platform; crops=$quadrants; notes="Reusable service platform and caged ladder assembly." },
    [ordered]@{ name="Asset09A_LargeStillage"; source=$sources.Stillages; crops=@(
        (New-CropSpec "front" 10 125 250 380), (New-CropSpec "rear" 637 125 250 380),
        (New-CropSpec "left" 10 752 250 380), (New-CropSpec "right" 637 752 250 380)
    ); notes="Large stillage isolated from the family sheet." },
    [ordered]@{ name="Asset09B_SmallStillage"; source=$sources.Stillages; crops=@(
        (New-CropSpec "front" 250 155 150 350), (New-CropSpec "rear" 877 155 150 350),
        (New-CropSpec "left" 250 782 150 350), (New-CropSpec "right" 877 782 150 350)
    ); notes="Small stillage isolated from the family sheet." },
    [ordered]@{ name="Asset09C_FlatStillage"; source=$sources.Stillages; crops=@(
        (New-CropSpec "front" 405 205 210 300), (New-CropSpec "rear" 1032 205 210 300),
        (New-CropSpec "left" 405 832 210 300), (New-CropSpec "right" 1032 832 210 300)
    ); notes="Flat stillage isolated from the family sheet." },
    [ordered]@{ name="Asset10_PoweredRollerConveyor"; source=$sources.Conveyor; crops=$quadrants; notes="Reusable powered roller conveyor; motor/gearbox should be separated for reuse and animation." }
)

function Export-SquareCrop {
    param([string]$Source, [hashtable]$Crop, [string]$Destination, [int]$CanvasSize=768)
    $image = [System.Drawing.Image]::FromFile($Source)
    try {
        if ($image.Width -ne 1254 -or $image.Height -ne 1254) {
            throw "Unexpected source dimensions $($image.Width)x$($image.Height): $Source"
        }
        $rect = New-Object System.Drawing.Rectangle($Crop.x, $Crop.y, $Crop.width, $Crop.height)
        $cropped = New-Object System.Drawing.Bitmap($rect.Width, $rect.Height)
        try {
            $g = [System.Drawing.Graphics]::FromImage($cropped)
            try { $g.DrawImage($image, 0, 0, $rect, [System.Drawing.GraphicsUnit]::Pixel) } finally { $g.Dispose() }
            $canvas = New-Object System.Drawing.Bitmap($CanvasSize, $CanvasSize)
            try {
                $cg = [System.Drawing.Graphics]::FromImage($canvas)
                try {
                    $cg.Clear([System.Drawing.Color]::White)
                    $cg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                    $scale = [Math]::Min(($CanvasSize - 48) / $cropped.Width, ($CanvasSize - 48) / $cropped.Height)
                    $dw = [int]($cropped.Width * $scale); $dh = [int]($cropped.Height * $scale)
                    $dx = [int](($CanvasSize - $dw) / 2); $dy = [int](($CanvasSize - $dh) / 2)
                    $cg.DrawImage($cropped, $dx, $dy, $dw, $dh)
                } finally { $cg.Dispose() }
                $canvas.Save($Destination, [System.Drawing.Imaging.ImageFormat]::Png)
            } finally { $canvas.Dispose() }
        } finally { $cropped.Dispose() }
    } finally { $image.Dispose() }
}

$manifestAssets = @()
foreach ($asset in $assets) {
    $assetDir = Join-Path $OutputRoot $asset.name
    New-Item -ItemType Directory -Force -Path $assetDir | Out-Null
    $viewFiles = [ordered]@{}
    foreach ($crop in $asset.crops) {
        $dest = Join-Path $assetDir ($crop.view + ".png")
        Export-SquareCrop -Source $asset.source -Crop $crop -Destination $dest
        $viewFiles[$crop.view] = [ordered]@{
            file = $dest
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $dest).Hash
            crop = $crop
        }
    }
    $manifestAssets += [ordered]@{
        name = $asset.name
        source = $asset.source
        source_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $asset.source).Hash
        status = "SOURCE_ONLY_NOT_SUBMITTED"
        notes = $asset.notes
        views = $viewFiles
    }
}

$manifest = [ordered]@{
    revision = "v634"
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    purpose = "Clean Meshy source views for replacement Train A supporting systems. No legacy geometry and no Unreal map changes."
    rules = @(
        "Do not combine separate gameplay objects into one generated mesh.",
        "Keep moving parts separate for pivots, animation and collision.",
        "Use these references as visual modelling inputs only; all engineering dimensions remain TBC.",
        "Generated candidates require Blender QA, scale correction, collision and LOD work before Unreal use."
    )
    assets = $manifestAssets
}

$manifestPath = Join-Path $OutputRoot "MeshySupportingSystemsReferences_v634.manifest.json"
$manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Output $manifestPath
