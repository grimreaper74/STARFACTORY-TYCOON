[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('IMPORT_FROZEN_CAIRNWELL_2040_PANEL_MODULES_V001_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Engine = 'C:\Program Files\Epic Games\UE_5.8'
$Editor = Join-Path $Engine 'Engine\Binaries\Win64\UnrealEditor.exe'
$Python = Join-Path $Engine 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$ContractTool = Join-Path $Root 'Scripts\prepare_cairnwell_2040_panel_modules_v001_contract.py'
$BaselineTool = Join-Path $Root 'Scripts\prepare_cairnwell_2040_panel_modules_v001_baseline.py'
$Importer = Join-Path $Root 'Scripts\import_cairnwell_2040_panel_modules_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_cairnwell_2040_panel_modules_fresh_process_v001.py'
$Contract = Join-Path $Root 'Scripts\cairnwell_2040_panel_modules_v001_import_contract.json'
$ContractSidecar = Join-Path $Root 'Scripts\cairnwell_2040_panel_modules_v001_import_contract.sha256'
$Baseline = Join-Path $Root 'Scripts\cairnwell_2040_panel_modules_v001_import_baseline_v002.json'
$BaselineSidecar = Join-Path $Root 'Scripts\cairnwell_2040_panel_modules_v001_import_baseline_v002.sha256'
$RuntimeV013Contract = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v013_contract.json'
$RuntimeV013Sidecar = Join-Path $Root 'Scripts\cairnwell_2040_runtime_v001_recovery_v013_contract.sha256'
$Destination = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Vehicles\Cairnwell2040PanelModules_v001'
$AuditRoot = Join-Path $Root 'Saved\Audits\OneFactory\Vehicles\Cairnwell2040PanelModules_v001\UnrealImportLane_v001'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_v001.json'
$MaplessStartupOverride = '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:LoadLevelAtStartup=None'
$RunEnvironment = 'LINEBOSS_CAIRNWELL_2040_PANEL_MODULES_V001_RUN_ROOT'
$AckEnvironment = 'LINEBOSS_CAIRNWELL_2040_PANEL_MODULES_V001_ACK'
$SkipUbtEnvironment = 'UE_SKIP_UBT_SDK_SETUP'
$OldRunEnvironment = [Environment]::GetEnvironmentVariable($RunEnvironment, 'Process')
$OldAckEnvironment = [Environment]::GetEnvironmentVariable($AckEnvironment, 'Process')
$OldSkipUbtEnvironment = [Environment]::GetEnvironmentVariable($SkipUbtEnvironment, 'Process')

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required panel-lane file missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Assert-Sidecar([string]$Payload, [string]$Sidecar, [string]$Label) {
    $Actual = Get-Sha256 $Payload
    if (-not (Test-Path -LiteralPath $Sidecar -PathType Leaf)) {
        throw "$Label sidecar missing"
    }
    $Expected = ((Get-Content -Raw -LiteralPath $Sidecar).Trim() -split '\s+')[0].ToUpperInvariant()
    if ($Actual -cne $Expected) {
        throw "$Label sidecar mismatch"
    }
    return $Actual
}

function Assert-NoProcesses {
    $Names = @(
        'UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT',
        'ShaderCompileWorker','CrashReportClient','CrashReportClientEditor'
    )
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -gt 0) {
        $Details = ($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', '
        throw "Refusing panel lane while Unreal/build processes are active: $Details"
    }
    $Ubt = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        $Command = [string]$_.CommandLine
        $Command -and (
            ($Command -match [Regex]::Escape('UnrealBuildTool.dll') -and
             $Command -match [Regex]::Escape('C:\Program Files\Epic Games\UE_5.8')) -or
            ($Command -match [Regex]::Escape('-Mode=ValidatePlatforms') -and
             ($Command -match [Regex]::Escape('LineBossCarFactory.uproject') -or
              $Command -match [Regex]::Escape('AutoSDKInfo.txt')))
        )
    })
    if ($Ubt.Count -gt 0) {
        $Details = ($Ubt | ForEach-Object { "$($_.Name):$($_.ProcessId):$($_.CommandLine)" }) -join ', '
        throw "Refusing panel lane while exact UBT command line is active: $Details"
    }
}

function Invoke-PythonVerify([string[]]$Arguments, [string]$Marker, [string]$Label, [bool]$RetryReadOnly = $true) {
    $Deadline = [DateTime]::UtcNow.AddSeconds(15)
    do {
        $Output = (& $Python @Arguments 2>&1) -join [Environment]::NewLine
        if ($LASTEXITCODE -eq 0 -and $Output -match [Regex]::Escape($Marker)) {
            return $Output
        }
        if (-not $RetryReadOnly -or [DateTime]::UtcNow -ge $Deadline) {
            throw "$Label failed: $Output"
        }
        Start-Sleep -Milliseconds 500
    } while ($true)
}

function Invoke-GuardedEditor([string]$Script, [string]$Stem, [string]$TimeoutLabel) {
    $LogPath = Join-Path $RunRoot ($Stem + '.log')
    $StdoutPath = Join-Path $RunRoot ($Stem + '.stdout.log')
    $StderrPath = Join-Path $RunRoot ($Stem + '.stderr.log')
    $Arguments = @(
        ('"{0}"' -f $Project), '/Engine/Maps/Entry',
        '-Unattended', '-nop4', '-NoSplash', '-NoSound', '-NullRHI',
        '-NoCompile', '-NoCompileEditor', '-NoAutoSave', '-NoSaveOnExit',
        '-NoLoadStartupPackages', '-NoRestoreOpenAssetTabs',
        '-NoAssetRegistryCacheWrite', $MaplessStartupOverride,
        '-stdout', '-FullStdOutLogOutput',
        ('-ExecutePythonScript="{0}"' -f $Script),
        ('-abslog="{0}"' -f $LogPath)
    )
    $Process = Start-Process -FilePath $Editor -ArgumentList $Arguments -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $StdoutPath -RedirectStandardError $StderrPath -PassThru
    $null = $Process.Handle
    $Exited = $Process.WaitForExit(3600 * 1000)
    if (-not $Exited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw "$TimeoutLabel timed out after 3600 seconds"
    }
    $Process.WaitForExit()
    $Process.Refresh()
    if ($null -eq $Process.ExitCode) {
        throw "$TimeoutLabel lost its process exit code"
    }
    return [ordered]@{ process_id = [int]$Process.Id; exit_code = [int]$Process.ExitCode }
}

function Write-FailureSummary([object]$ErrorValue, [bool]$EnvironmentRestored, [object]$ImportProcess, [object]$ValidationProcess) {
    if (-not (Test-Path -LiteralPath $RunRoot -PathType Container)) {
        return
    }
    $Payload = [ordered]@{
        '$schema' = 'lineboss/audit/cairnwell-2040-panel-modules-v001/import-lane-summary/v1'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'FAIL_CLOSED__CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT_LANE'
        run_root = $RunRoot
        runtime_recovery_v013_contract_sha256 = '5D2B1929086AD33A8354ED0759509BCC6AFFEF8CD4E5BDE77A54546B53E95F12'
        runtime_recovery_v013_run_id = '20260815T172802Z-1389784f'
        vehicle_model_id = 'CAIRNWELL_2040'
        development_geometry_revisionable = $true
        final_release_visual_lock_claimed = $false
        import_process = $ImportProcess
        validation_process = $ValidationProcess
        environment_restoration_verified = $EnvironmentRestored
        no_build_tool_invoked = $false
        content_move_delete_reimport_count = 0
        error = [string]$ErrorValue
    }
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($SummaryPath, ($Payload | ConvertTo-Json -Depth 12) + [Environment]::NewLine, $Utf8NoBom)
}

foreach ($Path in @(
        $Project,$Editor,$Python,$ContractTool,$BaselineTool,$Importer,$Validator,
        $Contract,$ContractSidecar,$Baseline,$BaselineSidecar,
        $RuntimeV013Contract,$RuntimeV013Sidecar)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Prepared panel-lane input missing: $Path"
    }
}
if (Test-Path -LiteralPath $Destination) {
    throw 'Fresh panel destination already exists; overwrite/reimport is forbidden'
}
if (Test-Path -LiteralPath $AuditRoot) {
    throw 'Panel import lane is one-use and its audit root already exists'
}
Assert-NoProcesses
$ContractHash = Assert-Sidecar $Contract $ContractSidecar 'Panel contract'
$BaselineHash = Assert-Sidecar $Baseline $BaselineSidecar 'Panel baseline'
$RuntimeV013Hash = Assert-Sidecar $RuntimeV013Contract $RuntimeV013Sidecar 'Runtime V013'
if ($RuntimeV013Hash -cne '5D2B1929086AD33A8354ED0759509BCC6AFFEF8CD4E5BDE77A54546B53E95F12') {
    throw 'Exact runtime V013 authority hash drift'
}
$null = Invoke-PythonVerify @($ContractTool, '--verify-only') 'PASS__CAIRNWELL_2040_PANEL_MODULES_V001_CONTRACT_REVERIFIED' 'Panel contract preflight'
$null = Invoke-PythonVerify @($BaselineTool, '--verify-only') 'PASS__CAIRNWELL_2040_PANEL_MODULES_V001_FULL_BASELINE_REVERIFIED' 'Panel baseline preflight'
Assert-NoProcesses

New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null
$ImportProcess = $null
$ValidationProcess = $null
$CaughtError = $null
$RestoreErrors = @()
$EnvironmentRestored = $false
try {
    [Environment]::SetEnvironmentVariable($RunEnvironment, $RunRoot, 'Process')
    [Environment]::SetEnvironmentVariable($AckEnvironment, $Acknowledgement, 'Process')
    [Environment]::SetEnvironmentVariable($SkipUbtEnvironment, '1', 'Process')
    if ([Environment]::GetEnvironmentVariable($SkipUbtEnvironment, 'Process') -cne '1') {
        throw 'Failed to set exact UE_SKIP_UBT_SDK_SETUP=1 process guard'
    }

    $ImportProcess = Invoke-GuardedEditor $Importer 'unreal_import' 'Panel importer'
    if ($ImportProcess.exit_code -ne 0) {
        throw "Panel importer returned nonzero exit $($ImportProcess.exit_code)"
    }
    if (Test-Path -LiteralPath (Join-Path $RunRoot 'import_failure_v001.json')) {
        throw 'Panel importer emitted a failure receipt'
    }
    Assert-NoProcesses
    $null = Invoke-PythonVerify @($BaselineTool, '--verify-import-result', $RunRoot) 'PASS__CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT_RESULT_REVERIFIED' 'Panel import post-exit verifier'

    $ValidationProcess = Invoke-GuardedEditor $Validator 'fresh_process_validation' 'Panel fresh-process validator'
    if ($ValidationProcess.exit_code -ne 0) {
        throw "Panel validator returned nonzero exit $($ValidationProcess.exit_code)"
    }
    if (Test-Path -LiteralPath (Join-Path $RunRoot 'fresh_process_validation_failure_v001.json')) {
        throw 'Panel fresh-process validator emitted a failure receipt'
    }
    Assert-NoProcesses
    $null = Invoke-PythonVerify @($BaselineTool, '--verify-validation-result', $RunRoot) 'PASS__CAIRNWELL_2040_PANEL_MODULES_V001_VALIDATION_RESULT_REVERIFIED' 'Panel validation post-exit verifier'
}
catch {
    $CaughtError = $_
}
finally {
    foreach ($Row in @(
            [pscustomobject]@{ Name = $RunEnvironment; Value = $OldRunEnvironment },
            [pscustomobject]@{ Name = $AckEnvironment; Value = $OldAckEnvironment },
            [pscustomobject]@{ Name = $SkipUbtEnvironment; Value = $OldSkipUbtEnvironment })) {
        try {
            if ($null -eq $Row.Value) {
                [Environment]::SetEnvironmentVariable($Row.Name, [System.Management.Automation.Language.NullString]::Value, 'Process')
            }
            else {
                [Environment]::SetEnvironmentVariable($Row.Name, [string]$Row.Value, 'Process')
            }
        }
        catch {
            $RestoreErrors += "$($Row.Name):$($_.Exception.Message)"
        }
    }
}

$ActualRun = [Environment]::GetEnvironmentVariable($RunEnvironment, 'Process')
$ActualAck = [Environment]::GetEnvironmentVariable($AckEnvironment, 'Process')
$ActualSkip = [Environment]::GetEnvironmentVariable($SkipUbtEnvironment, 'Process')
$RunRestored = if ($null -eq $OldRunEnvironment) { $null -eq $ActualRun } else { $ActualRun -ceq $OldRunEnvironment }
$AckRestored = if ($null -eq $OldAckEnvironment) { $null -eq $ActualAck } else { $ActualAck -ceq $OldAckEnvironment }
$SkipRestored = if ($null -eq $OldSkipUbtEnvironment) { $null -eq $ActualSkip } else { $ActualSkip -ceq $OldSkipUbtEnvironment }
$EnvironmentRestored = [bool]($RestoreErrors.Count -eq 0 -and $RunRestored -and $AckRestored -and $SkipRestored)
if (-not $EnvironmentRestored -and $null -eq $CaughtError) {
    $CaughtError = "Panel lane environment restoration failed: $($RestoreErrors -join ',')"
}
try {
    Assert-NoProcesses
}
catch {
    if ($null -eq $CaughtError) { $CaughtError = $_ }
    else { $CaughtError = "$CaughtError; final process gate: $($_.Exception.Message)" }
}
if ($null -ne $CaughtError) {
    Write-FailureSummary $CaughtError $EnvironmentRestored $ImportProcess $ValidationProcess
    throw $CaughtError
}

try {
    $null = Invoke-PythonVerify @(
        $BaselineTool, '--finalize-result', $RunRoot,
        '--import-exit-code', [string]$ImportProcess.exit_code,
        '--validation-exit-code', [string]$ValidationProcess.exit_code
    ) 'PASS__CAIRNWELL_2040_PANEL_MODULES_V001_SUMMARY_FINALIZED' 'Panel lane final summary' $false
    $null = Invoke-PythonVerify @($BaselineTool, '--verify-final-result', $RunRoot) 'PASS__CAIRNWELL_2040_PANEL_MODULES_V001_FINAL_NINE_FILE_REVERIFIED' 'Panel lane exact final closure'
    Assert-NoProcesses
}
catch {
    Write-FailureSummary $_ $EnvironmentRestored $ImportProcess $ValidationProcess
    throw
}
Write-Output 'PASS__CAIRNWELL_2040_PANEL_MODULES_V001_GUARDED_IMPORT_LANE'
Write-Output "LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_V001_SUMMARY=$SummaryPath"
