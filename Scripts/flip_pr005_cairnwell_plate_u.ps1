param(
    [string]$Source = "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Brand\Candidate_v001\T_CAIRNWELL_PR005_ASSET_PLATE_v001.png",
    [string]$Destination = "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Brand\Candidate_v001\T_CAIRNWELL_PR005_ASSET_PLATE_FLIPU_v001.png"
)

Add-Type -AssemblyName System.Drawing
$bitmap = [System.Drawing.Bitmap]::FromFile($Source)
try {
    $bitmap.RotateFlip([System.Drawing.RotateFlipType]::RotateNoneFlipX)
    $bitmap.Save($Destination, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $bitmap.Dispose()
}
Write-Output "LINE_BOSS_PR005_CAIRNWELL_FLIPU_PASS destination=$Destination"
