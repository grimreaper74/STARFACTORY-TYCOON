param(
 [string]$ApiKeyPath='C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
 [string]$OutputRoot='C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\Shared\Meshy6PressUnloadRobot_v719',
 [int]$PollSeconds=10,[int]$TimeoutMinutes=20
)
$ErrorActionPreference='Stop';$submission=Join-Path $OutputRoot 'submission.json';$summary=Join-Path $OutputRoot 'MESHY_V719_SUMMARY.json'
if(Test-Path $summary){throw 'v719 already collected'}
$meta=Get-Content -LiteralPath $submission -Raw|ConvertFrom-Json;$taskId=$meta.task_id
$apiKey=(Get-Content -LiteralPath $ApiKeyPath -Raw).Trim();if([string]::IsNullOrWhiteSpace($apiKey)){throw 'Empty Meshy key'};$headers=@{Authorization="Bearer $apiKey"}
$deadline=(Get-Date).AddMinutes($TimeoutMinutes);$task=$null
while((Get-Date)-lt$deadline){$task=Invoke-RestMethod ('https://api.meshy.ai/openapi/v1/multi-image-to-3d/'+$taskId) -Headers $headers;$task|ConvertTo-Json -Depth 12|Set-Content (Join-Path $OutputRoot 'task_latest.json') -Encoding UTF8;Write-Output "STATUS $($task.status) progress=$($task.progress)";if($task.status-in@('SUCCEEDED','FAILED','CANCELED')){break};Start-Sleep $PollSeconds}
if($task.status-ne'SUCCEEDED'){throw "Meshy v719 ended $($task.status)"}
$glb=Join-Path $OutputRoot 'SM_CA_MW_PressUnloadRobot_Meshy6_Raw_v719.glb';$fbx=Join-Path $OutputRoot 'SM_CA_MW_PressUnloadRobot_Meshy6_Raw_v719.fbx'
if($task.model_urls.glb){Invoke-WebRequest $task.model_urls.glb -OutFile $glb};if($task.model_urls.fbx){Invoke-WebRequest $task.model_urls.fbx -OutFile $fbx}
$after=(Invoke-RestMethod 'https://api.meshy.ai/openapi/v1/balance' -Headers $headers).balance;$task|ConvertTo-Json -Depth 12|Set-Content (Join-Path $OutputRoot 'task_complete.json') -Encoding UTF8
@{revision='v719';status='SUCCEEDED';task_id=$taskId;balance_before=$meta.balance_before;balance_after=$after;consumed=$meta.balance_before-$after;reported_consumed_credits=$task.consumed_credits;glb=(Test-Path $glb);fbx=(Test-Path $fbx)}|ConvertTo-Json -Depth 6|Set-Content $summary -Encoding UTF8
Write-Output "COLLECTED v719 consumed=$($meta.balance_before-$after) balance_after=$after";$apiKey=$null;$headers=$null
