$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$project = Join-Path $root 'LineBossCarFactory.uproject'
$engine = 'C:\Program Files\Epic Games\UE_5.8'
$editor = Join-Path $engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$build = Join-Path $engine 'Engine\Build\BatchFiles\Build.bat'
$scripts = Join-Path $root 'Scripts'
$logs = Join-Path $root 'Saved\Logs\PR009_InMap_v096'
$automation = Join-Path $root 'Saved\Automation\PR009_InMap_v096'
New-Item -ItemType Directory -Force $logs,$automation | Out-Null

function UnrealPython([string]$name,[string]$script) {
    $path = (Join-Path $scripts $script).Replace('\','/')
    & $editor $project "-ExecutePythonScript=$path" -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput *> (Join-Path $logs ($name+'.log'))
    if($LASTEXITCODE -ne 0) { Write-Warning "$name returned $LASTEXITCODE; audit content determines the gate" }
}
function Automation([string]$name,[string]$test) {
    & $editor $project "-ExecCmds=Automation RunTests $test; Quit" "-ReportExportPath=$(Join-Path $automation $name)" `
        '-TestExit=Automation Test Queue Empty' -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput `
        *> (Join-Path $logs ('automation_'+$name+'.log'))
    if($LASTEXITCODE -ne 0) { Write-Warning "$name returned $LASTEXITCODE; index.json determines the gate" }
}

Push-Location $root
try {
    & $build LineBossCarFactoryEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE *> (Join-Path $logs 'native_build.log')
    if($LASTEXITCODE -ne 0) { throw 'Native editor build failed' }
    Automation 'RuntimeAndSave' 'LineBoss.PressShop.PR009.RuntimeAndSave'
    Automation 'TraceableBlankHandoff' 'LineBoss.PressShop.MaterialFlow.PR008ToPR009TraceableBlankHandoff'
    UnrealPython 'static' 'audit_press_shop_pr009_enclosure_release_static_v096.py'
    UnrealPython 'runtime' 'validate_press_shop_pr009_in_map_pie_v096.py'
    UnrealPython 'physical' 'validate_press_shop_pr009_enclosure_physical_pie_v096.py'
    UnrealPython 'navigation' 'validate_press_shop_pr009_navigation_pie_v096.py'
    python (Join-Path $scripts 'audit_press_shop_pr009_collision_contract_sweeps_v096.py')
    if($LASTEXITCODE -ne 0) { throw 'Full-contract collision sweep failed' }
}
finally { Pop-Location }
