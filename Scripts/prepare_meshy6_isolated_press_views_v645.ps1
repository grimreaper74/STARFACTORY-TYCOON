param(
 [string]$PanelRoot='C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\Shared\MeshyIsolatedIntake_v625\Prepared\S03_ComponentPanels_v628',
 [string]$RotorSheet='C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\Shared\MeshyIsolatedIntake_v625\Original\ProReferencePack_v627\S03_A11_FlywheelSpokedRotor_Orthographic_v629.png',
 [string]$OutputRoot='C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\Shared\MeshyIsolatedIntake_v625\Prepared\Meshy6Views_v645'
)
$ErrorActionPreference='Stop';Add-Type -AssemblyName System.Drawing
$assets=@(
 @{Id='01_RamSlide';File='S03_A01_RamSlide_Panel_v628.png'},@{Id='02_UpperDie';File='S03_A02_UpperDie_Panel_v628.png'},
 @{Id='03_LowerDie';File='S03_A03_LowerDie_Panel_v628.png'},@{Id='04_LeftAccessDoor';File='S03_A04_LeftAccessDoor_Panel_v628.png'},
 @{Id='05_RightAccessDoor';File='S03_A05_RightAccessDoor_Panel_v628.png'},@{Id='06_FixedSafetyFence';File='S03_A06_FixedSafetyFence_Panel_v628.png'},
 @{Id='07_InterlockedGate';File='S03_A07_InterlockedGate_Panel_v628.png'},@{Id='08_ElectricalCabinet';File='S03_A08_ElectricalCabinet_Panel_v628.png'},
 @{Id='09_OperatorHMI';File='S03_A09_OperatorHMI_Panel_v628.png'},@{Id='10_FlywheelHousing';File='S03_A10_FlywheelHousing_Panel_v628.png'}
)
function Export-Crop([string]$Source,[int]$X,[int]$Y,[int]$W,[int]$H,[string]$Destination){
 $img=[Drawing.Image]::FromFile($Source);try{$crop=New-Object Drawing.Bitmap($W,$H);try{$g=[Drawing.Graphics]::FromImage($crop);try{$g.DrawImage($img,0,0,(New-Object Drawing.Rectangle($X,$Y,$W,$H)),[Drawing.GraphicsUnit]::Pixel)}finally{$g.Dispose()};$canvas=New-Object Drawing.Bitmap(768,768);try{$cg=[Drawing.Graphics]::FromImage($canvas);try{$cg.Clear([Drawing.Color]::White);$cg.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$scale=[Math]::Min(720/$W,720/$H);$dw=[int]($W*$scale);$dh=[int]($H*$scale);$cg.DrawImage($crop,[int]((768-$dw)/2),[int]((768-$dh)/2),$dw,$dh)}finally{$cg.Dispose()};$canvas.Save($Destination,[Drawing.Imaging.ImageFormat]::Png)}finally{$canvas.Dispose()}}finally{$crop.Dispose()}}finally{$img.Dispose()}
}
New-Item -ItemType Directory -Path $OutputRoot -Force|Out-Null
$manifest=@()
$panelCrops=@{front=@(5,55,184,120);rear=@(195,55,184,120);left=@(5,255,184,88);right=@(195,255,184,88)}
foreach($a in $assets){$dir=Join-Path $OutputRoot $a.Id;New-Item -ItemType Directory -Path $dir -Force|Out-Null;$source=Join-Path $PanelRoot $a.File;$views=@{};foreach($name in @('front','rear','left','right')){$c=$panelCrops[$name];$dest=Join-Path $dir ($name+'.png');Export-Crop $source $c[0] $c[1] $c[2] $c[3] $dest;$views[$name]=@{file=$dest;sha256=(Get-FileHash $dest -Algorithm SHA256).Hash}};$manifest+=@{id=$a.Id;source=$source;views=$views;status='PREPARED_NOT_SUBMITTED'}}
$rotorDir=Join-Path $OutputRoot '11_FlywheelRotorShaft';New-Item -ItemType Directory -Path $rotorDir -Force|Out-Null
$rotorCrops=@{front=@(20,20,590,530);rear=@(645,20,590,530);left=@(20,625,590,490);right=@(645,625,590,490)};$rotorViews=@{}
foreach($name in @('front','rear','left','right')){$c=$rotorCrops[$name];$dest=Join-Path $rotorDir ($name+'.png');Export-Crop $RotorSheet $c[0] $c[1] $c[2] $c[3] $dest;$rotorViews[$name]=@{file=$dest;sha256=(Get-FileHash $dest -Algorithm SHA256).Hash}}
$manifest+=@{id='11_FlywheelRotorShaft';source=$RotorSheet;views=$rotorViews;status='PREPARED_NOT_SUBMITTED'}
@{revision='v645';purpose='Label-free four-view Meshy 6 inputs for eleven isolated press components';assets=$manifest}|ConvertTo-Json -Depth 8|Set-Content (Join-Path $OutputRoot 'MANIFEST_v645.json') -Encoding UTF8
Write-Output (Join-Path $OutputRoot 'MANIFEST_v645.json')
