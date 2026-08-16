$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$projectRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$project = Join-Path $projectRoot 'LineBossCarFactory.uproject'
$engineRoot = 'C:\Program Files\Epic Games\UE_5.8'
$editor = Join-Path $engineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$build = Join-Path $engineRoot 'Engine\Build\BatchFiles\Build.bat'
$scripts = Join-Path $projectRoot 'Scripts'
$auditDir = Join-Path $projectRoot 'Saved\Audits\PR009_InMap_v095'
$logDir = Join-Path $projectRoot 'Saved\Logs\PR009_InMap_v095'
$automationDir = Join-Path $projectRoot 'Saved\Automation\PR009_InMap_v095'
New-Item -ItemType Directory -Force -Path $auditDir, $logDir, $automationDir | Out-Null

function Invoke-UnrealPython([string]$name, [string]$scriptName) {
    $scriptPath = (Join-Path $scripts $scriptName).Replace('\', '/')
    $rawLog = Join-Path $logDir ($name + '.log')
    & $editor $project "-ExecutePythonScript=$scriptPath" -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput *> $rawLog
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "$name editor process returned $LASTEXITCODE; its audit file determines the gate"
    }
}

function Invoke-Automation([string]$name, [string]$testPath) {
    $report = Join-Path $automationDir $name
    $rawLog = Join-Path $logDir ("automation_" + $name + '.log')
    & $editor $project "-ExecCmds=Automation RunTests $testPath; Quit" "-ReportExportPath=$report" `
        '-TestExit=Automation Test Queue Empty' -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput `
        *> $rawLog
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "$name automation process returned $LASTEXITCODE; index.json determines the gate"
    }
}

Push-Location $projectRoot
try {
    python (Join-Path $scripts 'snapshot_press_shop_pr009_enclosure_v095_integrity.py') gate_before
    if ($LASTEXITCODE -ne 0) { throw 'v095 pre-gate integrity snapshot failed' }

    $buildLog = Join-Path $logDir 'native_build.log'
    & $build LineBossCarFactoryEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE *> $buildLog
    if ($LASTEXITCODE -ne 0) { throw "Native editor build failed; see $buildLog" }

    Invoke-Automation 'RuntimeAndSave' 'LineBoss.PressShop.PR009.RuntimeAndSave'
    Invoke-Automation 'TraceableBlankHandoff' 'LineBoss.PressShop.MaterialFlow.PR008ToPR009TraceableBlankHandoff'
    Invoke-UnrealPython 'static_map' 'audit_press_shop_pr009_enclosure_release_static_v095.py'
    Invoke-UnrealPython 'runtime_pie' 'validate_press_shop_pr009_in_map_pie_v095.py'
    Invoke-UnrealPython 'physical_pie' 'validate_press_shop_pr009_enclosure_physical_pie_v095.py'
    Invoke-UnrealPython 'navigation_pie' 'validate_press_shop_pr009_navigation_pie_v095.py'

    python (Join-Path $scripts 'audit_press_shop_pr009_collision_contract_sweeps_v095.py')
    if ($LASTEXITCODE -ne 0) { throw 'v095 collision-contract sweep failed' }

    python (Join-Path $scripts 'snapshot_press_shop_pr009_enclosure_v095_integrity.py') gate_after
    if ($LASTEXITCODE -ne 0) { throw 'v095 post-gate integrity snapshot failed' }
}
finally {
    Pop-Location
}
