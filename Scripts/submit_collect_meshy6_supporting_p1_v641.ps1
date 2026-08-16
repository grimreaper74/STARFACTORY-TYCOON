param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$SourceRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\TrainA\MeshySupportingSystemsReferences_v634',
    [string]$OutputRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\TrainA\Meshy6SupportingSystemsProduction_v641',
    [int]$PollSeconds = 10,
    [int]$TimeoutMinutes = 45
)

$ErrorActionPreference = 'Stop'
$assets = @(
    @{Id='DIE_CHANGE_CART';Folder='Asset06_DieChangeCart';Output='01_DieChangeCart'},
    @{Id='HYDRAULIC_POWER_UNIT';Folder='Asset07_HydraulicPowerUnit';Output='02_HydraulicPowerUnit'},
    @{Id='LARGE_TRIM_SCRAP_BIN';Folder='Asset09A_LargeStillage';Output='03_LargeTrimScrapBin'},
    @{Id='SMALL_SLUG_BIN';Folder='Asset09B_SmallStillage';Output='04_SmallSlugBin'},
    @{Id='FLAT_PANEL_STILLAGE';Folder='Asset09C_FlatStillage';Output='05_FlatPanelStillage'},
    @{Id='POWERED_ROLLER_CONVEYOR';Folder='Asset10_PoweredRollerConveyor';Output='06_PoweredRollerConveyor'}
)
$views=@('front','rear','left','right')
$apiKey=(Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if([string]::IsNullOrWhiteSpace($apiKey)){throw 'Meshy API key file is empty.'}
$headers=@{Authorization="Bearer $apiKey"}
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

function Get-DataUri([string]$Path){'data:image/png;base64,'+[Convert]::ToBase64String([IO.File]::ReadAllBytes($Path))}
$balanceBefore=(Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $headers).balance
$required=30*$assets.Count
if([int]$balanceBefore -lt $required){throw "Need $required credits; balance is $balanceBefore."}
$jobs=@()
foreach($asset in $assets){
    $sourceDir=Join-Path $SourceRoot $asset.Folder;$outputDir=Join-Path $OutputRoot $asset.Output;$originalDir=Join-Path $outputDir 'Original'
    New-Item -ItemType Directory -Path $originalDir -Force | Out-Null
    $uris=@();$sourceRecords=@()
    foreach($view in $views){
        $source=Join-Path $sourceDir ($view+'.png');if(-not(Test-Path -LiteralPath $source)){throw "Missing source: $source"}
        Copy-Item -LiteralPath $source -Destination (Join-Path $originalDir ($view+'.png')) -Force
        $uris+=Get-DataUri $source;$sourceRecords+=[ordered]@{view=$view;file=$source;sha256=(Get-FileHash $source -Algorithm SHA256).Hash}
    }
    $submissionFile=Join-Path $outputDir 'submission.json'
    if(Test-Path $submissionFile){$taskId=(Get-Content -Raw $submissionFile|ConvertFrom-Json).task_id}
    else{
        $payload=[ordered]@{image_urls=$uris;ai_model='meshy-6';should_texture=$true;enable_pbr=$true;texture_resolution='2k';should_remesh=$false;image_enhancement=$false;remove_lighting=$true;target_formats=@('glb','fbx')}
        $created=Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/multi-image-to-3d' -Headers $headers -Method Post -ContentType 'application/json' -Body ($payload|ConvertTo-Json -Depth 5 -Compress)
        $taskId=$created.result
        $record=[ordered]@{id=$asset.Id;task_id=$taskId;submitted_utc=(Get-Date).ToUniversalTime().ToString('o');expected_credits=30;sources=$sourceRecords;settings=[ordered]@{ai_model='meshy-6';should_texture=$true;enable_pbr=$true;texture_resolution='2k';should_remesh=$false;image_enhancement=$false;remove_lighting=$true;target_formats=@('glb','fbx')}}
        $record|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $submissionFile -Encoding UTF8
    }
    $jobs+=[ordered]@{id=$asset.Id;task_id=$taskId;output_dir=$outputDir;status='SUBMITTED'}
    Write-Output "TRACKING $($asset.Id) $taskId"
}
$deadline=(Get-Date).AddMinutes($TimeoutMinutes)
while((Get-Date)-lt $deadline){
    $pending=0
    foreach($job in $jobs){
        if($job.status -in @('SUCCEEDED','FAILED','CANCELED')){continue}
        $task=Invoke-RestMethod -Uri ('https://api.meshy.ai/openapi/v1/multi-image-to-3d/'+$job.task_id) -Headers $headers
        $job.status=$task.status;$task|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $job.output_dir 'task_latest.json') -Encoding UTF8
        if($task.status -eq 'SUCCEEDED'){
            if($task.model_urls.glb){Invoke-WebRequest $task.model_urls.glb -OutFile (Join-Path $job.output_dir ($job.id+'_Meshy6_Raw.glb'))}
            if($task.model_urls.fbx){Invoke-WebRequest $task.model_urls.fbx -OutFile (Join-Path $job.output_dir ($job.id+'_Meshy6_Raw.fbx'))}
            $task|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $job.output_dir 'task_complete.json') -Encoding UTF8
            Write-Output "SUCCEEDED $($job.id) credits=$($task.consumed_credits)"
        }elseif($task.status -in @('FAILED','CANCELED')){Write-Output "FAILED $($job.id) status=$($task.status)"}else{$pending++}
    }
    if($pending -eq 0){break};Start-Sleep -Seconds $PollSeconds
}
$balanceAfter=(Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $headers).balance
$summary=[ordered]@{revision='v641';generated_utc=(Get-Date).ToUniversalTime().ToString('o');balance_before=$balanceBefore;balance_after=$balanceAfter;consumed=$balanceBefore-$balanceAfter;status=if(($jobs|Where-Object{$_.status-ne'SUCCEEDED'}).Count-eq 0){'ALL_SUCCEEDED'}else{'INCOMPLETE'};jobs=$jobs}
$summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $OutputRoot 'BATCH_SUMMARY_v641.json') -Encoding UTF8
$summary|ConvertTo-Json -Depth 8
if($summary.status-ne'ALL_SUCCEEDED'){exit 2}
