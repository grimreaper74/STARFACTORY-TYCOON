param(
 [string]$ApiKeyPath='C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
 [string]$SourceSheet='C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\TrainA\AssemblyStudy_v012\Reference\Cairnwell_Robot_Family_Robot_Variants.png',
 [string]$OutputRoot='C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\Shared\Meshy6PressUnloadRobot_v719',
 [int]$PollSeconds=10,
 [int]$TimeoutMinutes=45
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
if(-not(Test-Path -LiteralPath $SourceSheet)){throw "Missing robot sheet: $SourceSheet"}
New-Item -ItemType Directory -Path $OutputRoot -Force|Out-Null
$submission=Join-Path $OutputRoot 'submission.json'
if(Test-Path $submission){throw 'Refusing duplicate paid submission v719'}
Copy-Item -LiteralPath $SourceSheet -Destination (Join-Path $OutputRoot 'approved_robot_family_sheet.png')

$source=[System.Drawing.Image]::FromFile($SourceSheet)
$views=@(
 @{name='front';x=28;y=105;w=104;h=255},
 @{name='side';x=132;y=105;w=105;h=255},
 @{name='hero';x=232;y=100;w=120;h=270}
)
$uris=@();$sources=@()
try{
 foreach($v in $views){
  $bitmap=New-Object System.Drawing.Bitmap(512,512)
  $g=[System.Drawing.Graphics]::FromImage($bitmap)
  try{
   $g.Clear([System.Drawing.Color]::White)
   $g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
   $scale=[Math]::Min(460.0/$v.w,460.0/$v.h);$dw=[int]($v.w*$scale);$dh=[int]($v.h*$scale)
   $dest=New-Object System.Drawing.Rectangle([int]((512-$dw)/2),[int]((512-$dh)/2),$dw,$dh)
   $crop=New-Object System.Drawing.Rectangle($v.x,$v.y,$v.w,$v.h)
   $g.DrawImage($source,$dest,$crop,[System.Drawing.GraphicsUnit]::Pixel)
   $path=Join-Path $OutputRoot ($v.name+'.png');$bitmap.Save($path,[System.Drawing.Imaging.ImageFormat]::Png)
   $uris+='data:image/png;base64,'+[Convert]::ToBase64String([IO.File]::ReadAllBytes($path))
   $sources+=@{view=$v.name;file=$path;sha256=(Get-FileHash $path -Algorithm SHA256).Hash}
  }finally{$g.Dispose();$bitmap.Dispose()}
 }
}finally{$source.Dispose()}

$apiKey=(Get-Content -LiteralPath $ApiKeyPath -Raw).Trim();if([string]::IsNullOrWhiteSpace($apiKey)){throw 'Empty Meshy key'}
$headers=@{Authorization="Bearer $apiKey"}
$before=(Invoke-RestMethod 'https://api.meshy.ai/openapi/v1/balance' -Headers $headers).balance
if($before-lt 30){throw "Need 30 credits; balance $before"}
$payload=@{
 image_urls=$uris;ai_model='meshy-6';should_texture=$true;enable_pbr=$true;texture_resolution='2k';
 should_remesh=$false;image_enhancement=$false;remove_lighting=$true;target_formats=@('glb','fbx');
 texture_prompt='Cairnwell automotive press-handling unload robot. Dark charcoal cast housings, restrained safety-orange joint rings and caps, machined steel vacuum crossbar and rails, black hoses, small green status indicators. Clean production industrial finish. No floor, background, text, labels, people, cage, or surrounding machinery.'
}
$created=Invoke-RestMethod 'https://api.meshy.ai/openapi/v1/multi-image-to-3d' -Headers $headers -Method Post -ContentType 'application/json' -Body ($payload|ConvertTo-Json -Depth 6 -Compress)
$taskId=$created.result
@{revision='v719';task_id=$taskId;submitted_utc=(Get-Date).ToUniversalTime().ToString('o');expected_credits=30;balance_before=$before;sources=$sources;settings=@{ai_model='meshy-6';pbr=$true;texture_resolution='2k';remesh=$false}}|ConvertTo-Json -Depth 8|Set-Content $submission -Encoding UTF8
Write-Output "SUBMITTED v719 $taskId balance_before=$before"
$deadline=(Get-Date).AddMinutes($TimeoutMinutes);$task=$null
while((Get-Date)-lt$deadline){
 $task=Invoke-RestMethod ('https://api.meshy.ai/openapi/v1/multi-image-to-3d/'+$taskId) -Headers $headers
 $task|ConvertTo-Json -Depth 12|Set-Content (Join-Path $OutputRoot 'task_latest.json') -Encoding UTF8
 Write-Output "STATUS $($task.status) progress=$($task.progress)"
 if($task.status-in@('SUCCEEDED','FAILED','CANCELED')){break}
 Start-Sleep $PollSeconds
}
if($task.status-ne'SUCCEEDED'){throw "Meshy v719 ended $($task.status)"}
if($task.model_urls.glb){Invoke-WebRequest $task.model_urls.glb -OutFile (Join-Path $OutputRoot 'SM_CA_MW_PressUnloadRobot_Meshy6_Raw_v719.glb')}
if($task.model_urls.fbx){Invoke-WebRequest $task.model_urls.fbx -OutFile (Join-Path $OutputRoot 'SM_CA_MW_PressUnloadRobot_Meshy6_Raw_v719.fbx')}
$after=(Invoke-RestMethod 'https://api.meshy.ai/openapi/v1/balance' -Headers $headers).balance
$task|ConvertTo-Json -Depth 12|Set-Content (Join-Path $OutputRoot 'task_complete.json') -Encoding UTF8
@{revision='v719';status='SUCCEEDED';task_id=$taskId;balance_before=$before;balance_after=$after;consumed=$before-$after;reported_consumed_credits=$task.consumed_credits;glb=(Test-Path (Join-Path $OutputRoot 'SM_CA_MW_PressUnloadRobot_Meshy6_Raw_v719.glb'));fbx=(Test-Path (Join-Path $OutputRoot 'SM_CA_MW_PressUnloadRobot_Meshy6_Raw_v719.fbx'))}|ConvertTo-Json -Depth 6|Set-Content (Join-Path $OutputRoot 'MESHY_V719_SUMMARY.json') -Encoding UTF8
Write-Output "SUCCEEDED v719 consumed=$($before-$after) balance_after=$after"
$apiKey=$null;$headers=$null
