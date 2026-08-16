$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$project = Join-Path $root 'LineBossCarFactory.uproject'
$editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$logs = Join-Path $root 'Saved\Logs\EngineComparison\CoilAGV_Untouched_v20260810'
New-Item -ItemType Directory -Force -Path $logs | Out-Null

function Invoke-UnrealScript([string]$name, [string]$script, [switch]$Rendered) {
    $scriptPath = (Join-Path $root "Scripts\$script").Replace('\','/')
    $arguments = @($project, "-ExecutePythonScript=$scriptPath", '-unattended', '-nop4', '-nosplash',
        '-stdout', '-FullStdOutLogOutput')
    if ($Rendered) { $arguments += '-RenderOffscreen' } else { $arguments += '-NullRHI' }
    & $editor @arguments *> (Join-Path $logs "$name.log")
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "$name returned $LASTEXITCODE; the JSON receipt and PASS marker are authoritative."
    }
}

Push-Location $root
try {
    Invoke-UnrealScript '01_import' 'import_coil_agv_untouched_engine_comparison_v20260810.py'
    Invoke-UnrealScript '02_capture' 'capture_coil_agv_untouched_engine_comparison_v20260810.py' -Rendered
}
finally {
    Pop-Location
}
