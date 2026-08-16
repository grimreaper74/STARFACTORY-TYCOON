$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$project = Join-Path $root 'LineBossCarFactory.uproject'
$engine = 'C:\Program Files\Epic Games\UE_5.8'
$editor = Join-Path $engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$build = Join-Path $engine 'Engine\Build\BatchFiles\Build.bat'
$scripts = Join-Path $root 'Scripts'
$audit = Join-Path $root 'Saved\Audits\PR009_InMap_v087'
$logs = Join-Path $root 'Saved\Logs\PR009_InMap_v087'
$automation = Join-Path $root 'Saved\Automation\PR009_InMap_v087'
New-Item -ItemType Directory -Force -Path $audit,$logs,$automation | Out-Null

function Invoke-UnrealPython([string]$name,[string]$script,[switch]$Rendered) {
    $path = (Join-Path $scripts $script).Replace('\','/')
    $args = @($project,"-ExecutePythonScript=$path",'-unattended','-nop4','-nosplash','-stdout','-FullStdOutLogOutput')
    if ($Rendered) { $args += '-RenderOffscreen' } else { $args += '-NullRHI' }
    & $editor @args *> (Join-Path $logs ($name + '.log'))
    if ($LASTEXITCODE -ne 0) { Write-Warning "$name returned $LASTEXITCODE; its JSON receipt is authoritative." }
}

function Invoke-Automation([string]$name,[string]$test) {
    $report = Join-Path $automation $name
    New-Item -ItemType Directory -Force -Path $report | Out-Null
    & $editor $project "-ExecCmds=Automation RunTests $test; Quit" "-ReportExportPath=$report" `
        '-TestExit=Automation Test Queue Empty' -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput `
        *> (Join-Path $logs ("automation_$name.log"))
    if ($LASTEXITCODE -ne 0) { Write-Warning "$name returned $LASTEXITCODE; index.json is authoritative." }
}

Push-Location $root
try {
    python (Join-Path $scripts 'snapshot_press_shop_pr009_release_collision_v087_integrity.py') validation_before

    & $build LineBossCarFactoryEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE `
        *> (Join-Path $logs 'native_build.log')
    if ($LASTEXITCODE -ne 0) { Write-Warning "Native compile returned $LASTEXITCODE." }

    Invoke-Automation 'RuntimeAndSave' 'LineBoss.PressShop.PR009.RuntimeAndSave'
    Invoke-Automation 'TraceableBlankHandoff' 'LineBoss.PressShop.MaterialFlow.PR008ToPR009TraceableBlankHandoff'
    Invoke-UnrealPython 'release_collision_static' 'audit_press_shop_pr009_release_collision_static_v087.py'
    Invoke-UnrealPython 'runtime_pie' 'validate_press_shop_pr009_in_map_pie_v087.py'
    Invoke-UnrealPython 'physical_collision_pie' 'validate_press_shop_pr009_physical_collision_pie_v087.py'
    Invoke-UnrealPython 'navigation_pie' 'validate_press_shop_pr009_navigation_pie_v087.py'
    python (Join-Path $scripts 'audit_press_shop_pr009_collision_contract_sweeps_v087.py')

    foreach ($phase in @('parent','target')) {
        $env:LB_PR009_V087_INVENTORY_PHASE = $phase
        Invoke-UnrealPython "visual_invariants_$phase" 'capture_press_shop_pr009_visual_invariants_v087.py'
    }
    Remove-Item Env:LB_PR009_V087_INVENTORY_PHASE -ErrorAction SilentlyContinue

    foreach ($view in @('process','interface','cell','elevated')) {
        $env:LB_PR009_V087_CAPTURE = $view
        Invoke-UnrealPython "capture_$view" 'capture_press_shop_pr009_release_collision_v087.py' -Rendered
    }
    Remove-Item Env:LB_PR009_V087_CAPTURE -ErrorAction SilentlyContinue

    python (Join-Path $scripts 'snapshot_press_shop_pr009_release_collision_v087_integrity.py') validation_after
    python (Join-Path $scripts 'consolidate_press_shop_pr009_release_collision_v087.py')
}
finally {
    Remove-Item Env:LB_PR009_V087_INVENTORY_PHASE -ErrorAction SilentlyContinue
    Remove-Item Env:LB_PR009_V087_CAPTURE -ErrorAction SilentlyContinue
    Pop-Location
}
