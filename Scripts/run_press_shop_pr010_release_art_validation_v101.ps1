$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$project = Join-Path $root 'LineBossCarFactory.uproject'
$engine = 'C:\Program Files\Epic Games\UE_5.8'
$editor = Join-Path $engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$build = Join-Path $engine 'Engine\Build\BatchFiles\Build.bat'
$logs = Join-Path $root 'Saved\Logs\PR010_ReleaseArt_v101'
$automation = Join-Path $root 'Saved\Automation\PR010_V101_Final'
New-Item -ItemType Directory -Force $logs,$automation | Out-Null

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
    Automation 'PR010_RuntimeAndSave' 'LineBoss.PressShop.PR010.RuntimeAndSave'
    Automation 'PR009_RuntimeAndSave' 'LineBoss.PressShop.PR009.RuntimeAndSave'
    Automation 'PR008_RuntimeAndSave' 'LineBoss.PressShop.PR008.RuntimeAndSave'
    Automation 'PR008ToPR009TraceableBlankHandoff' 'LineBoss.PressShop.MaterialFlow.PR008ToPR009TraceableBlankHandoff'
}
finally { Pop-Location }
