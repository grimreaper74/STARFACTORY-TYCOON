$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$projectRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$project = Join-Path $projectRoot 'LineBossCarFactory.uproject'
$engineRoot = 'C:\Program Files\Epic Games\UE_5.8'
$editor = Join-Path $engineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$build = Join-Path $engineRoot 'Engine\Build\BatchFiles\Build.bat'
$scripts = Join-Path $projectRoot 'Scripts'

$targetMap = & python -c "import sys; sys.path.insert(0, r'$scripts'); from press_shop_pr009_in_map_validation_config import TARGET_MAP; print(TARGET_MAP)"
if ($targetMap -notmatch '_v(\d+)$') { throw "Could not derive target version from $targetMap" }
$version = 'v' + $Matches[1]
$auditDir = Join-Path $projectRoot "Saved\Audits\PR009_InMap_$version"
$logDir = Join-Path $projectRoot "Saved\Logs\PR009_InMap_$version"
$automationDir = Join-Path $projectRoot "Saved\Automation\PR009_InMap_$version"
New-Item -ItemType Directory -Force -Path $auditDir, $logDir, $automationDir | Out-Null

function Invoke-UnrealPython([string]$name, [string]$scriptName) {
    $scriptPath = (Join-Path $scripts $scriptName).Replace('\', '/')
    $rawLog = Join-Path $logDir ($name + '.log')
    & $editor $project "-ExecutePythonScript=$scriptPath" -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput *> $rawLog
    if ($LASTEXITCODE -ne 0) { Write-Warning "$name editor process returned $LASTEXITCODE; evidence audit determines the gate" }
}

function Invoke-Automation([string]$name, [string]$testPath) {
    $report = Join-Path $automationDir $name
    $rawLog = Join-Path $logDir ("automation_" + $name + '.log')
    $commands = "Automation RunTests $testPath; Quit"
    & $editor $project "-ExecCmds=$commands" "-ReportExportPath=$report" "-TestExit=Automation Test Queue Empty" -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput *> $rawLog
    if ($LASTEXITCODE -ne 0) { Write-Warning "$name automation process returned $LASTEXITCODE; index.json determines the gate" }
}

Push-Location $projectRoot
try {
    python (Join-Path $scripts 'snapshot_press_shop_pr009_validation_integrity.py') before

    $buildLog = Join-Path $logDir 'native_build.log'
    & $build LineBossCarFactoryEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE *> $buildLog
    if ($LASTEXITCODE -ne 0) { throw "Native editor build failed; see $buildLog" }

    Invoke-Automation 'RuntimeAndSave' 'LineBoss.PressShop.PR009.RuntimeAndSave'
    Invoke-Automation 'TraceableBlankHandoff' 'LineBoss.PressShop.MaterialFlow.PR008ToPR009TraceableBlankHandoff'
    Invoke-UnrealPython 'static_map' 'audit_press_shop_pr009_in_map_static.py'
    Invoke-UnrealPython 'runtime_pie' 'validate_press_shop_pr009_in_map_pie.py'
    Invoke-UnrealPython 'navigation_pie' 'validate_press_shop_pr009_navigation_pie.py'

    python (Join-Path $scripts 'snapshot_press_shop_pr009_validation_integrity.py') after
    python (Join-Path $scripts 'consolidate_press_shop_pr009_in_map_validation.py')
    if ($LASTEXITCODE -ne 0) { throw "PR-009 consolidated verification has failed gates" }
}
finally {
    Pop-Location
}
