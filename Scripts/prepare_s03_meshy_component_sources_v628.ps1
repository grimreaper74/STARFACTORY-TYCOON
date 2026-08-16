param(
    [string]$Source = "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\Shared\MeshyIsolatedIntake_v625\Original\ProReferencePack_v627\S03_ComponentPack_Composite_A_v627.png",
    [string]$OutputRoot = "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\Shared\MeshyIsolatedIntake_v625\Prepared\S03_ComponentPanels_v628"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

if (-not (Test-Path -LiteralPath $Source)) {
    throw "Source sheet not found: $Source"
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$image = [System.Drawing.Bitmap]::FromFile($Source)
try {
    if ($image.Width -ne 1536 -or $image.Height -ne 1024) {
        throw "Unexpected source dimensions $($image.Width)x$($image.Height); expected 1536x1024."
    }

    $panels = @(
        @{ Id = "01"; Name = "RamSlide";         X = 0;    Y = 0;   W = 384; H = 350 },
        @{ Id = "02"; Name = "UpperDie";         X = 384;  Y = 0;   W = 384; H = 350 },
        @{ Id = "03"; Name = "LowerDie";         X = 768;  Y = 0;   W = 384; H = 350 },
        @{ Id = "04"; Name = "LeftAccessDoor";   X = 1152; Y = 0;   W = 384; H = 350 },
        @{ Id = "05"; Name = "RightAccessDoor";  X = 0;    Y = 350; W = 384; H = 350 },
        @{ Id = "06"; Name = "FixedSafetyFence"; X = 384;  Y = 350; W = 384; H = 350 },
        @{ Id = "07"; Name = "InterlockedGate";  X = 768;  Y = 350; W = 384; H = 350 },
        @{ Id = "08"; Name = "ElectricalCabinet";X = 1152; Y = 350; W = 384; H = 350 },
        @{ Id = "09"; Name = "OperatorHMI";      X = 0;    Y = 700; W = 384; H = 324 },
        @{ Id = "10"; Name = "FlywheelHousing";  X = 384;  Y = 700; W = 384; H = 324 },
        @{ Id = "11"; Name = "FlywheelInsert";   X = 768;  Y = 700; W = 384; H = 324 }
    )

    $records = foreach ($panel in $panels) {
        $rectangle = [System.Drawing.Rectangle]::new($panel.X, $panel.Y, $panel.W, $panel.H)
        $crop = $image.Clone($rectangle, $image.PixelFormat)
        try {
            $fileName = "S03_A$($panel.Id)_$($panel.Name)_Panel_v628.png"
            $destination = Join-Path $OutputRoot $fileName
            $crop.Save($destination, [System.Drawing.Imaging.ImageFormat]::Png)
            $hash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
            [ordered]@{
                asset_id = [int]$panel.Id
                asset_name = $panel.Name
                source_panel = $fileName
                crop_pixels = [ordered]@{ x = $panel.X; y = $panel.Y; width = $panel.W; height = $panel.H }
                sha256 = $hash
                generation_status = "NOT_SUBMITTED"
                approval_status = "SOURCE_ONLY"
            }
        }
        finally {
            $crop.Dispose()
        }
    }

    $manifest = [ordered]@{
        schema = "lineboss.meshy-component-source-manifest.v1"
        revision = "v628"
        source_sheet = $Source
        source_sheet_sha256 = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
        source_dimensions_pixels = [ordered]@{ width = $image.Width; height = $image.Height }
        purpose = "Lossless panel isolation for visual review and later single-asset input preparation. No Meshy jobs are submitted by this script."
        production_rules = @(
            "Shape approval precedes texturing.",
            "Generated geometry remains candidate source until Blender and Unreal gates pass.",
            "Moving parts remain separate assets with explicit pivots.",
            "Do not promote high-density Meshy source directly into the game."
        )
        assets = $records
    }
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot "manifest_v628.json") -Encoding utf8
}
finally {
    $image.Dispose()
}

Write-Output "Prepared 11 source panels at $OutputRoot"
