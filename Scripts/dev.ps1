# Developer task runner for STAR FACTORY TYCOON (2026-08-31).
#
# One entry point for the loop every session repeats: build, run the game
# headlessly, run automation tests, capture a frame, drive the local agent.
# It exists because those commands are long, order-sensitive, and carry
# traps this repo has documented in blood:
#
#   * The project path MUST be absolute. Relative works only when the
#     child process inherits the project directory, and several shells
#     here do not. When it fails the editor logs "Failed to open
#     descriptor file", runs ZERO tests, writes no report - and leaves
#     the PREVIOUS run's log in place, which reads like a clean pass.
#     Two separate sessions accepted a stale log as evidence.
#   * -ExecCmds splits on COMMAS, not semicolons. A semicolon-joined list
#     parses as ONE command whose name ends in ';', matches nothing, and
#     never reaches the trailing Quit - so the game runs forever and
#     looks hung.
#   * A test run is only evidence if <ReportExportPath>/index.json exists.
#     A directory is not a pass.
#   * The scripted lanes refuse to run while the Editor is alive.
#
# Every guard here encodes one of those. Do not remove them to make a
# run succeed.
#
# Usage:
#   .\Scripts\dev.ps1 build              # build the editor target
#   .\Scripts\dev.ps1 build -Target Game # build the packaged game target
#   .\Scripts\dev.ps1 play               # headless spacecraft journey
#   .\Scripts\dev.ps1 play -Iterations 200
#   .\Scripts\dev.ps1 test               # all LineBoss automation tests
#   .\Scripts\dev.ps1 test -Suite LineBoss.Spacecraft
#   .\Scripts\dev.ps1 shot               # build line, capture a frame
#   .\Scripts\dev.ps1 agent              # editor + AgentZet eval bridge
#   .\Scripts\dev.ps1 editor             # plain editor
#   .\Scripts\dev.ps1 status             # what is running / recent evidence
#   .\Scripts\dev.ps1 kill               # stop editor/build processes

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('build', 'play', 'test', 'shot', 'agent', 'editor', 'status', 'kill')]
    [string]$Task,

    [ValidateSet('Editor', 'Game')]
    [string]$Target = 'Editor',

    [string]$Suite = 'LineBoss',

    [int]$Iterations = 90,

    [string]$Name,

    [switch]$KeepEditor
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$uproject = Join-Path $projectRoot 'LineBossCarFactory.uproject'   # ABSOLUTE - see header
$engine = 'C:\Program Files\Epic Games\UE_5.8'
$editorExe = Join-Path $engine 'Engine\Binaries\Win64\UnrealEditor.exe'
$editorCmd = Join-Path $engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$buildBat = Join-Path $engine 'Engine\Build\BatchFiles\Build.bat'
$gameLog = Join-Path $projectRoot 'Saved\Logs\LineBossCarFactory.log'

$blockingNames = @('UnrealEditor', 'UnrealEditor-Cmd', 'UnrealBuildTool',
                   'AutomationTool', 'RunUAT', 'ShaderCompileWorker')

function Get-BlockingProcesses {
    Get-Process -Name $blockingNames -ErrorAction SilentlyContinue
}

function Stop-Blocking {
    $procs = Get-BlockingProcesses
    if ($procs) {
        Write-Host "Stopping: $(($procs | Select-Object -ExpandProperty Name -Unique) -join ', ')"
        $procs | Stop-Process -Force
        Start-Sleep -Seconds 3
    }
}

function Assert-NoBlocking {
    $procs = Get-BlockingProcesses
    if ($procs) {
        $names = ($procs | Select-Object -ExpandProperty Name -Unique) -join ', '
        throw "These must be closed first: $names. Run '.\Scripts\dev.ps1 kill' (or pass -KeepEditor only where supported)."
    }
}

function Invoke-Build([string]$WhichTarget) {
    $targetName = if ($WhichTarget -eq 'Game') { 'LineBossCarFactory' } else { 'LineBossCarFactoryEditor' }
    Write-Host "=== BUILD $targetName ==="
    Assert-NoBlocking
    & $buildBat $targetName Win64 Development $uproject -WaitMutex -NoHotReloadFromIDE 2>&1 |
        Select-String -Pattern 'error|warning C|Result:|Total execution' |
        ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -ne 0) { throw "BUILD FAILED (exit $LASTEXITCODE)." }
    Write-Host "BUILD OK: $targetName"
}

switch ($Task) {

    'kill' { Stop-Blocking; Write-Host 'All clear.'; break }

    'build' { Invoke-Build $Target; break }

    'editor' {
        Assert-NoBlocking
        Start-Process $editorExe -ArgumentList "`"$uproject`"", '-NoSplash'
        Write-Host 'Editor launching.'
        break
    }

    'agent' {
        Assert-NoBlocking
        Remove-Item (Join-Path $projectRoot 'Saved\AgentZetEval\bridge.ready') -ErrorAction SilentlyContinue
        Start-Process $editorExe -ArgumentList "`"$uproject`"", '-AgentZetEvalBridge', '-NoSplash'
        Write-Host 'Editor launching with the AgentZet eval bridge.'
        Write-Host 'Queue work with: .\Scripts\run_agentzet_batch_v001.ps1 -JobsDir <dir>'
        break
    }

    'play' {
        # COMMA-separated - see header. Semicolons silently never run.
        Assert-NoBlocking
        $cmds = "LB.Spacecraft.BuildLine,LB.Spacecraft.Run $Iterations 1.0,LB.Spacecraft.Status,Quit"
        Write-Host "=== HEADLESS RUN ($Iterations iterations) ==="
        $started = Get-Date
        & $editorCmd $uproject -game "-ExecCmds=$cmds" `
            -unattended -nop4 -nosplash -nosound -NullRHI -stdout -FullStdOutLogOutput 2>&1 |
            Select-String -Pattern 'LB\.Spacecraft|LogLineBoss|Error:|Warning:' |
            ForEach-Object { Write-Host "  $_" }
        Write-Host ("Finished in {0:n0}s. Full log: {1}" -f ((Get-Date) - $started).TotalSeconds, $gameLog)
        break
    }

    'test' {
        Assert-NoBlocking
        if (-not $Name) { $Name = 'Run_{0}' -f (Get-Date).ToString('yyyyMMdd_HHmmss') }
        $reportDir = Join-Path $projectRoot "Saved\Automation\$Name"
        Write-Host "=== AUTOMATION TESTS: $Suite ==="
        & $editorCmd $uproject "-ExecCmds=Automation RunTests $Suite" `
            "-ReportExportPath=$reportDir" '-TestExit=Automation Test Queue Empty' `
            -unattended -nop4 -nosplash -nosound -NullRHI -stdout -FullStdOutLogOutput 2>&1 |
            Select-String -Pattern 'Test Completed|Automation Test|LogAutomationController.*(Passed|Failed)|Error:' |
            ForEach-Object { Write-Host "  $_" }

        # EVIDENCE GATE: index.json or it did not happen (see header).
        $indexJson = Join-Path $reportDir 'index.json'
        if (-not (Test-Path -LiteralPath $indexJson)) {
            Write-Host ''
            Write-Warning "NO index.json at $indexJson - this run produced NO usable evidence."
            Write-Warning "Do NOT read Saved\Logs\*.log as the result: it may still hold the PREVIOUS run."
            exit 1
        }
        $report = Get-Content -LiteralPath $indexJson -Raw | ConvertFrom-Json
        $passed = @($report.tests | Where-Object { $_.state -eq 'Success' }).Count
        $failed = @($report.tests | Where-Object { $_.state -ne 'Success' }).Count
        Write-Host ''
        Write-Host "RESULT: $passed passed, $failed failed  (report: $indexJson)"
        if ($failed -gt 0) {
            @($report.tests | Where-Object { $_.state -ne 'Success' }) |
                ForEach-Object { Write-Host "  FAILED: $($_.fullTestPath)" }
            exit 1
        }
        break
    }

    'shot' {
        # Renders a real frame. The standing rule on this project is to
        # LOOK at a frame before claiming a visual change is good - twice
        # the owner saw a fault first because a change was reasoned about
        # instead of captured.
        Assert-NoBlocking
        if (-not $Name) { $Name = 'shot_{0}' -f (Get-Date).ToString('yyyyMMdd_HHmmss') }
        $shotDir = Join-Path $projectRoot 'Saved\Screenshots\WindowsEditor'
        Write-Host '=== FRAME CAPTURE (builds the line, then shoots) ==='
        # NOT -NullRHI: a null renderer cannot produce an image.
        $cmds = "LB.Spacecraft.BuildLine,LB.Spacecraft.Run 30 1.0,HighResShot 1920x1080,Quit"
        & $editorCmd $uproject -game "-ExecCmds=$cmds" `
            -unattended -nop4 -nosplash -nosound -stdout 2>&1 |
            Select-String -Pattern 'HighResShot|screenshot|LB\.Spacecraft|Error:' |
            ForEach-Object { Write-Host "  $_" }
        $newest = Get-ChildItem -LiteralPath $shotDir -Filter '*.png' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($newest) {
            Write-Host "CAPTURED: $($newest.FullName)"
        } else {
            Write-Warning "No screenshot appeared in $shotDir - the capture did NOT happen."
            exit 1
        }
        break
    }

    'status' {
        Write-Host '=== PROCESSES ==='
        $procs = Get-BlockingProcesses
        if ($procs) {
            $procs | Select-Object Name, Id, @{n = 'CPU'; e = { [int]$_.CPU } } | Format-Table -AutoSize
        } else { Write-Host '  (none running)' }

        Write-Host '=== LOCAL AI ==='
        $ollama = Get-Process -Name 'ollama' -ErrorAction SilentlyContinue
        Write-Host ("  ollama: {0}" -f $(if ($ollama) { 'running' } else { 'not running' }))
        $bridge = Join-Path $projectRoot 'Saved\AgentZetEval\bridge.ready'
        Write-Host ("  agent bridge: {0}" -f $(if (Test-Path $bridge) { 'ARMED' } else { 'off' }))

        Write-Host '=== LATEST TEST REPORT ==='
        $latest = Get-ChildItem -LiteralPath (Join-Path $projectRoot 'Saved\Automation') -Directory -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latest) {
            $idx = Join-Path $latest.FullName 'index.json'
            $verdict = if (Test-Path $idx) { 'has index.json (usable)' } else { 'NO index.json - not evidence' }
            Write-Host ("  {0}  [{1}]  {2}" -f $latest.Name, $latest.LastWriteTime, $verdict)
        } else { Write-Host '  (no runs)' }

        Write-Host '=== GIT ==='
        Push-Location $projectRoot
        try {
            $branch = (& git rev-parse --abbrev-ref HEAD 2>$null)
            $dirty = @(& git status --porcelain 2>$null).Count
            Write-Host ("  branch {0}, {1} changed file(s)" -f $branch, $dirty)
            Write-Host ("  last: {0}" -f (& git log --oneline -1 2>$null))
        } finally { Pop-Location }
        break
    }
}
