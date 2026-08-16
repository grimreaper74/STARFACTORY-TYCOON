[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('VALIDATE_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Engine = 'C:\Program Files\Epic Games\UE_5.8'
$Editor = Join-Path $Engine 'Engine\Binaries\Win64\UnrealEditor.exe'
$Python = Join-Path $Engine 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$ContractTool = Join-Path $Root 'Scripts\prepare_cairnwell_2040_panel_modules_recovery_v002_contract.py'
$BaselineTool = Join-Path $Root 'Scripts\prepare_cairnwell_2040_panel_modules_v001_baseline.py'
$Verifier = Join-Path $Root 'Scripts\verify_cairnwell_2040_panel_modules_recovery_v002.py'
$Validator = Join-Path $Root 'Scripts\validate_cairnwell_2040_panel_modules_recovery_v002.py'
$Contract = Join-Path $Root 'Scripts\cairnwell_2040_panel_modules_recovery_v002_contract.json'
$ContractSidecar = Join-Path $Root 'Scripts\cairnwell_2040_panel_modules_recovery_v002_contract.sha256'
$Destination = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Vehicles\Cairnwell2040PanelModules_v001'
$AuditRoot = Join-Path $Root 'Saved\Audits\OneFactory\Vehicles\Cairnwell2040PanelModules_v001\UnrealImportLane_v001'
$IncidentRoot = Join-Path $AuditRoot '20260815T182842Z-0205ac3e'
$RecoveryAuditRoot = Join-Path $AuditRoot 'Recovery_v002'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $RecoveryAuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_recovery_v002.json'
$ReceiptPath = Join-Path $RunRoot 'fresh_process_validation_receipt_recovery_v002.json'
$FailurePath = Join-Path $RunRoot 'fresh_process_validation_failure_recovery_v002.json'
$CrcEvidencePath = Join-Path $RunRoot 'normal_crc_monitor_wait_recovery_v002.json'
$Stem = 'fresh_process_validation_recovery_v002'
$RunEnvironment = 'LINEBOSS_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_RUN_ROOT'
$AckEnvironment = 'LINEBOSS_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_ACK'
$SkipUbtEnvironment = 'UE_SKIP_UBT_SDK_SETUP'
$NoBytecodeEnvironment = 'PYTHONDONTWRITEBYTECODE'
$OldRunEnvironment = [Environment]::GetEnvironmentVariable($RunEnvironment, 'Process')
$OldAckEnvironment = [Environment]::GetEnvironmentVariable($AckEnvironment, 'Process')
$OldSkipUbtEnvironment = [Environment]::GetEnvironmentVariable($SkipUbtEnvironment, 'Process')
$OldNoBytecodeEnvironment = [Environment]::GetEnvironmentVariable($NoBytecodeEnvironment, 'Process')
$MaplessStartupOverride = '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:LoadLevelAtStartup=None'
$UncontrolledOverride = '-ini:Editor:[/Script/SourceControl.SourceControlPreferences]:bEnableUncontrolledChangelists=False'
$PythonStubOverride = '-ini:EditorPerProjectUserSettings:[/Script/PythonScriptPlugin.PythonScriptPluginUserSettings]:bDeveloperMode=False'

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required Recovery_v002 file missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Assert-Sidecar([string]$Payload, [string]$Sidecar, [string]$Label) {
    $Actual = Get-Sha256 $Payload
    if (-not (Test-Path -LiteralPath $Sidecar -PathType Leaf)) {
        throw "$Label sidecar missing"
    }
    $Tokens = ((Get-Content -Raw -LiteralPath $Sidecar).Trim() -split '\s+')
    if ($Tokens.Count -ne 2 -or $Tokens[0].ToUpperInvariant() -cne $Actual -or $Tokens[1] -cne (Split-Path -Leaf $Payload)) {
        throw "$Label exact sidecar token/name drift"
    }
    return $Actual
}

function Write-Utf8Json([string]$Path, [object]$Payload) {
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, ($Payload | ConvertTo-Json -Depth 60) + [Environment]::NewLine, $Utf8NoBom)
}

function Invoke-PythonVerify([string[]]$Arguments, [string]$Marker, [string]$Label) {
    $Output = (& $Python -B @Arguments 2>&1) -join [Environment]::NewLine
    if ($LASTEXITCODE -ne 0 -or $Output -notmatch [Regex]::Escape($Marker)) {
        throw "$Label failed: $Output"
    }
    return $Output
}

function Get-GuardedProcesses {
    $Names = @(
        'UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT',
        'ShaderCompileWorker','CrashReportClient','CrashReportClientEditor'
    )
    return @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
}

function Assert-NoProcesses {
    $Active = @(Get-GuardedProcesses)
    if ($Active.Count -gt 0) {
        $Details = ($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', '
        throw "Recovery_v002 process guard failed: $Details"
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
        throw "Recovery_v002 exact UBT command-line guard failed: $Details"
    }
}

function Get-CrashConfigRow([IO.FileInfo]$File) {
    $Relative = $File.FullName.Substring($Root.Length).TrimStart('\').Replace('\', '/')
    $UnixTicks = [int64]($File.LastWriteTimeUtc.Ticks - 621355968000000000)
    return [ordered]@{
        path = $Relative
        bytes = [int64]$File.Length
        mtime_ns = [int64]($UnixTicks * 100)
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $File.FullName).Hash
    }
}

function Get-CrashConfigDelta([object]$Payload) {
    $BeforeRows = @($Payload.recovery_preflight_crash_reporter_config_tree.files)
    $Before = @{}
    foreach ($Row in $BeforeRows) { $Before[[string]$Row.path] = $Row }
    $ConfigRoot = Join-Path $Root 'Saved\Config\CrashReportClient'
    $AfterRows = @(Get-ChildItem -LiteralPath $ConfigRoot -Recurse -File | ForEach-Object { Get-CrashConfigRow $_ })
    $After = @{}
    foreach ($Row in $AfterRows) { $After[[string]$Row.path] = $Row }
    foreach ($Path in $Before.Keys) {
        if (-not $After.ContainsKey($Path)) { throw "CrashReporter config deletion: $Path" }
        $Old = $Before[$Path]
        $New = $After[$Path]
        if ([string]$Old.bytes -cne [string]$New.bytes -or [string]$Old.mtime_ns -cne [string]$New.mtime_ns -or [string]$Old.sha256 -cne [string]$New.sha256) {
            throw "Existing CrashReporter config row drift: $Path"
        }
    }
    $NewRows = @($AfterRows | Where-Object { -not $Before.ContainsKey([string]$_.path) } | Sort-Object path)
    if ($NewRows.Count -gt 1) { throw "More than one new CrashReporter config row: $($NewRows.Count)" }
    foreach ($Row in $NewRows) {
        if ([string]$Row.path -cnotmatch [string]$Payload.recovery.crash_reporter_config_new_file_pattern -or
            [int64]$Row.bytes -ne [int64]$Payload.recovery.crash_reporter_config_new_file_bytes -or
            [string]$Row.sha256 -cne [string]$Payload.recovery.crash_reporter_config_new_file_sha256) {
            throw "New CrashReporter config row escaped exact allowlist: $($Row.path)"
        }
    }
    return [ordered]@{
        before_file_count = [int]$BeforeRows.Count
        before_inventory_sha256 = [string]$Payload.recovery_preflight_crash_reporter_config_tree.inventory_sha256
        after_file_count = [int]$AfterRows.Count
        existing_rows_unchanged = $true
        new_file_count = [int]$NewRows.Count
        new_files = @($NewRows)
        deleted_file_count = 0
        modified_existing_file_count = 0
    }
}

function Wait-ExactNormalCrcMonitor([int]$EditorProcessId, [object]$Payload) {
    $DeadlineSeconds = 15
    $Started = [DateTime]::UtcNow
    $Deadline = $Started.AddSeconds($DeadlineSeconds)
    $Observed = @{}
    $QuietSince = $null
    do {
        $Rows = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
            $_.Name -in @('CrashReportClient.exe', 'CrashReportClientEditor.exe')
        })
        foreach ($Row in $Rows) {
            $Command = [string]$Row.CommandLine
            $ExactMonitor = $Command -match ('(?i)(?:^|\s)-MONITOR=' + [Regex]::Escape([string]$EditorProcessId) + '(?:\s|$)')
            if (-not $ExactMonitor) {
                throw "Foreign/unbound CrashReporter process during bounded wait: $($Row.Name):$($Row.ProcessId):$Command"
            }
            $PidKey = [string]$Row.ProcessId
            if (-not $Observed.ContainsKey($PidKey)) {
                $CreationUtc = ([DateTime]$Row.CreationDate).ToUniversalTime().ToString('o')
                $Observed[$PidKey] = [ordered]@{
                    process_name = [string]$Row.Name
                    process_id = [int]$Row.ProcessId
                    parent_process_id = [int]$Row.ParentProcessId
                    creation_date_utc = $CreationUtc
                    command_line = $Command
                    monitor_process_id = $EditorProcessId
                    command_line_exact_monitor_binding = $true
                }
            }
        }
        $Now = [DateTime]::UtcNow
        if ($Now -ge $Deadline) {
            throw "Exact editor-bound CrashReporter monitor/quiet-streak exceeded $DeadlineSeconds second total deadline"
        }
        if ($Rows.Count -eq 0) {
            if ($null -eq $QuietSince) { $QuietSince = [DateTime]::UtcNow }
            if (($Now - $QuietSince).TotalMilliseconds -ge 1000) { break }
        } else {
            $QuietSince = $null
        }
        Start-Sleep -Milliseconds 250
    } while ($true)
    $WaitCompleted = [DateTime]::UtcNow
    $WaitElapsed = [int]($WaitCompleted - $Started).TotalMilliseconds
    if ($WaitElapsed -gt ($DeadlineSeconds * 1000)) {
        throw "CRC wait elapsed time escaped exact $DeadlineSeconds second bound"
    }
    $Delta = Get-CrashConfigDelta $Payload
    $Evidence = [ordered]@{
        '$schema' = 'lineboss/audit/cairnwell-2040-panel-modules-v001/recovery-v002/normal-crc-monitor-wait/v2'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'PASS__ONLY_EXACT_COMPLETED_EDITOR_BOUND_CRC_MONITORS_EXITED_NATURALLY'
        completed_editor_process_id = $EditorProcessId
        observed_exact_monitors = @($Observed.Values | Sort-Object process_id)
        unbound_crc_monitor_count = 0
        kill_count = 0
        natural_exit_only = $true
        deadline_seconds = $DeadlineSeconds
        wait_elapsed_milliseconds = $WaitElapsed
        zero_process_stabilization_milliseconds = 1000
        deadline_exceeded = $false
        crash_reporter_config_delta = $Delta
    }
    Write-Utf8Json $CrcEvidencePath $Evidence
    return $Evidence
}

function Invoke-GuardedValidator {
    $LogPath = Join-Path $RunRoot ($Stem + '.log')
    $StdoutPath = Join-Path $RunRoot ($Stem + '.stdout.log')
    $StderrPath = Join-Path $RunRoot ($Stem + '.stderr.log')
    $Arguments = @(
        ('"{0}"' -f $Project), '/Engine/Maps/Entry',
        '-Unattended', '-nop4', '-NoSplash', '-NoSound', '-NullRHI',
        '-NoCompile', '-NoCompileEditor', '-NoAutoSave', '-NoSaveOnExit',
        '-NoLoadStartupPackages', '-NoRestoreOpenAssetTabs',
        '-NoAssetRegistryCacheWrite', '-nowrite',
        $MaplessStartupOverride, $UncontrolledOverride, $PythonStubOverride,
        '-stdout', '-FullStdOutLogOutput',
        ('-ExecutePythonScript="{0}"' -f $Validator),
        ('-abslog="{0}"' -f $LogPath)
    )
    $Process = Start-Process -FilePath $Editor -ArgumentList $Arguments -WorkingDirectory $Root `
        -WindowStyle Hidden -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath -PassThru
    $null = $Process.Handle
    $Exited = $Process.WaitForExit(3600 * 1000)
    if (-not $Exited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw 'Recovery_v002 validator timed out after 3600 seconds'
    }
    $Process.WaitForExit()
    $Process.Refresh()
    if ($null -eq $Process.ExitCode) { throw 'Recovery_v002 validator lost exit code' }
    return [ordered]@{ process_id = [int]$Process.Id; exit_code = [int]$Process.ExitCode }
}

function Write-FailureSummary([object]$ErrorValue, [bool]$EnvironmentRestored, [object]$ValidationProcess) {
    if (-not (Test-Path -LiteralPath $RunRoot -PathType Container)) { return }
    $Payload = [ordered]@{
        '$schema' = 'lineboss/audit/cairnwell-2040-panel-modules-v001/recovery-v002/validation-only-lane-summary/v2'
        generated_utc = (Get-Date).ToUniversalTime().ToString('o')
        status = 'FAIL_CLOSED__CAIRNWELL_2040_PANEL_MODULES_V001_RECOVERY_V002_VALIDATION_ONLY_LANE'
        run_root = $RunRoot
        incident_v001_run_id = '20260815T182842Z-0205ac3e'
        validation_process = $ValidationProcess
        importer_process = $null
        import_reimport_move_delete_count = 0
        environment_restoration_verified = $EnvironmentRestored
        error = [string]$ErrorValue
    }
    Write-Utf8Json $SummaryPath $Payload
}

foreach ($Path in @($Project,$Editor,$Python,$ContractTool,$BaselineTool,$Verifier,$Validator,$Contract,$ContractSidecar)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Recovery_v002 input absent: $Path" }
}
if (-not (Test-Path -LiteralPath $Destination -PathType Container)) { throw 'Preserved exact panel destination is absent' }
if (-not (Test-Path -LiteralPath $IncidentRoot -PathType Container)) { throw 'Preserved v001 incident is absent' }
if (Test-Path -LiteralPath $RecoveryAuditRoot) { throw 'Recovery_v002 is one-use and already consumed' }
Assert-NoProcesses
$ContractHash = Assert-Sidecar $Contract $ContractSidecar 'Recovery_v002 contract'
$null = Invoke-PythonVerify @($ContractTool, '--verify-only') 'PASS__CAIRNWELL_2040_PANEL_MODULES_VALIDATION_ONLY_RECOVERY_V002_CONTRACT_REVERIFIED' 'Recovery_v002 frozen contract preflight'
$null = Invoke-PythonVerify @($Verifier, '--verify-preflight') 'PASS__CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_PREFLIGHT_REVERIFIED' 'Recovery_v002 incident/package/project/topology preflight'
Assert-NoProcesses
$RecoveryPayload = Get-Content -Raw -LiteralPath $Contract | ConvertFrom-Json

New-Item -ItemType Directory -Path $RunRoot | Out-Null
$ValidationProcess = $null
$CaughtError = $null
$RestoreErrors = @()
$EnvironmentRestored = $false
try {
    [Environment]::SetEnvironmentVariable($RunEnvironment, $RunRoot, 'Process')
    [Environment]::SetEnvironmentVariable($AckEnvironment, $Acknowledgement, 'Process')
    [Environment]::SetEnvironmentVariable($SkipUbtEnvironment, '1', 'Process')
    [Environment]::SetEnvironmentVariable($NoBytecodeEnvironment, '1', 'Process')
    if (
        [Environment]::GetEnvironmentVariable($SkipUbtEnvironment, 'Process') -cne '1' -or
        [Environment]::GetEnvironmentVariable($NoBytecodeEnvironment, 'Process') -cne '1'
    ) { throw 'Recovery_v002 process environment write/build suppression failed' }

    $ValidationProcess = Invoke-GuardedValidator
    $null = Wait-ExactNormalCrcMonitor $ValidationProcess.process_id $RecoveryPayload
    Assert-NoProcesses
    if ($ValidationProcess.exit_code -ne 0) { throw "Recovery_v002 validator exit $($ValidationProcess.exit_code)" }
    if (Test-Path -LiteralPath $FailurePath) { throw 'Recovery_v002 validator emitted failure receipt' }
    if (-not (Test-Path -LiteralPath $ReceiptPath -PathType Leaf)) { throw 'Recovery_v002 PASS receipt absent' }
}
catch { $CaughtError = $_ }
finally {
    foreach ($Row in @(
        [pscustomobject]@{ Name = $RunEnvironment; Value = $OldRunEnvironment },
        [pscustomobject]@{ Name = $AckEnvironment; Value = $OldAckEnvironment },
        [pscustomobject]@{ Name = $SkipUbtEnvironment; Value = $OldSkipUbtEnvironment },
        [pscustomobject]@{ Name = $NoBytecodeEnvironment; Value = $OldNoBytecodeEnvironment }
    )) {
        try {
            if ($null -eq $Row.Value) {
                [Environment]::SetEnvironmentVariable($Row.Name, [System.Management.Automation.Language.NullString]::Value, 'Process')
            } else {
                [Environment]::SetEnvironmentVariable($Row.Name, [string]$Row.Value, 'Process')
            }
        } catch { $RestoreErrors += "$($Row.Name):$($_.Exception.Message)" }
    }
}

$EnvironmentRestored = $true
foreach ($Row in @(
    [pscustomobject]@{ Name = $RunEnvironment; Value = $OldRunEnvironment },
    [pscustomobject]@{ Name = $AckEnvironment; Value = $OldAckEnvironment },
    [pscustomobject]@{ Name = $SkipUbtEnvironment; Value = $OldSkipUbtEnvironment },
    [pscustomobject]@{ Name = $NoBytecodeEnvironment; Value = $OldNoBytecodeEnvironment }
)) {
    $Actual = [Environment]::GetEnvironmentVariable($Row.Name, 'Process')
    $Equal = if ($null -eq $Row.Value) { $null -eq $Actual } else { $Actual -ceq [string]$Row.Value }
    if (-not $Equal) { $EnvironmentRestored = $false }
}
if ($RestoreErrors.Count -gt 0) { $EnvironmentRestored = $false }
if (-not $EnvironmentRestored -and $null -eq $CaughtError) {
    $CaughtError = "Recovery_v002 environment restoration drift: $($RestoreErrors -join ',')"
}
try { Assert-NoProcesses } catch {
    if ($null -eq $CaughtError) { $CaughtError = $_ } else { $CaughtError = "$CaughtError; final process gate: $($_.Exception.Message)" }
}
if ($null -ne $CaughtError) {
    Write-FailureSummary $CaughtError $EnvironmentRestored $ValidationProcess
    throw $CaughtError
}

try {
    $null = Invoke-PythonVerify @($Verifier, '--verify-result', $RunRoot) 'PASS__CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_RESULT_REVERIFIED' 'Recovery_v002 post-exit result'
    $null = Invoke-PythonVerify @($Verifier, '--finalize', $RunRoot, '--validator-exit-code', [string]$ValidationProcess.exit_code) 'PASS__CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_SUMMARY_FINALIZED' 'Recovery_v002 final summary'
    $null = Invoke-PythonVerify @($Verifier, '--verify-final', $RunRoot) 'PASS__CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_FINAL_SIX_FILE_REVERIFIED' 'Recovery_v002 exact final closure'
    Assert-NoProcesses
}
catch {
    Write-FailureSummary $_ $EnvironmentRestored $ValidationProcess
    throw
}
Write-Output 'PASS__CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_VALIDATION_ONLY_LANE'
Write-Output "LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_SUMMARY=$SummaryPath"
