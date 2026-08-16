[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V003_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$Python = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Baseline = Join-Path $Root 'Scripts\assembly_line_native_kit_incident_retry_baseline_v003_final.json'
$Freezer = Join-Path $Root 'Scripts\freeze_assembly_line_native_kit_incident_retry_baseline_v003.py'
$Runtime = Join-Path $Root 'Scripts\assembly_line_native_kit_incident_retry_runtime_v003.py'
$Validator = Join-Path $Root 'Scripts\revalidate_assembly_line_native_kit_incident_v003.py'
$Target = Join-Path $Root 'Content\LineBoss\Candidates\AssemblyShop\AssemblyLineNativeKit_v001'
$FailedV002Run = Join-Path $Root 'Saved\Audits\AssemblyShop\AssemblyLineNativeKit_v001\IncidentRecovery_v002\20260815T030646Z-e8c9a5eb'
$AuditRoot = Join-Path $Root 'Saved\Audits\AssemblyShop\AssemblyLineNativeKit_v001\IncidentRecovery_v003'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'incident_recovery_summary_v003.json'
$PassReceipt = Join-Path $RunRoot 'fresh_load_recovery_validation_receipt_v003.json'
$FailReceipt = Join-Path $RunRoot 'fresh_load_recovery_validation_failure_v003.json'
$ExpectedHashes = [ordered]@{
    baseline = 'A9BA9C499C5A30272BDEB2348A4D2912CEB41AD24396494F0468FA2D2B2C9276'
    freezer = 'A240118EF404682F7515F1CF3EA68064AFF3A873B1D499367CFD6EA3893DD96F'
    runtime = '09269AD61BFA49B11042DD1BDA63E7F7F1C10E0BDE2B4EFAC03BFD42D6CA1714'
    validator = 'FEEDE0765B6525C4847DDF6FFDCA229A5F6F0B865AA071D2D451DE0CF3807060'
    failed_v002_log = '9BC7F87884532B794F4FB49D9B13082A6ED4C48D0C46325730E2DBB4E78E9B72'
    failed_v002_summary = 'CEBFD5239081C66FFCEEE84FCDB593DE5D588D01C06B4B6B5F89CEE7FD3362EC'
}
$ExpectedStatus = 'PASS__V003_FORWARD_SLASH_COMMAND__INDEPENDENT_READ_ONLY_RELOAD__8_ASSETS_24_LODS'
$RunEnvironment = 'LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V003_RUN_ROOT'
$AckEnvironment = 'LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V003_ACK'
$ResultNames = @('fresh_load_recovery_validation_receipt_v003.json',
    'fresh_load_recovery_validation_failure_v003.json','incident_recovery_summary_v003.json')

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required file missing: $Path" }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Assert-Hash([string]$Path,[string]$Expected,[string]$Label) {
    $Actual = Get-Sha256 $Path
    if ($Actual -cne $Expected) { throw "$Label hash drift: expected=$Expected actual=$Actual" }
    return $Actual
}

function Assert-NoProcesses {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -gt 0) {
        throw "Refusing v003 while Unreal/build processes are active: $(($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', ')"
    }
}

function Assert-NoPriorResults {
    if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { return }
    $Found = @(Get-ChildItem -LiteralPath $AuditRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $ResultNames -contains $_.Name })
    if ($Found.Count -gt 0) {
        throw "One-use v003 refuses every prior result (PASS or FAIL): $($Found.FullName -join '; ')"
    }
}

function Convert-ToSafeExecutePythonPath([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "ExecutePythonScript file missing: $Path" }
    $Normalized = [IO.Path]::GetFullPath($Path).Replace('\','/')
    if ($Normalized.Contains('\')) { throw "ExecutePythonScript path retains a forbidden backslash: $Normalized" }
    $ControlCharacters = [char[]](0..31)
    if ($Normalized.IndexOfAny($ControlCharacters) -ge 0) {
        throw 'ExecutePythonScript path contains a forbidden control character'
    }
    if (-not $Normalized.EndsWith('.py',[StringComparison]::OrdinalIgnoreCase) `
            -or -not $Normalized.StartsWith('C:/',[StringComparison]::OrdinalIgnoreCase)) {
        throw "ExecutePythonScript path is not an absolute normalized Python file: $Normalized"
    }
    return $Normalized
}

function Invoke-GuardedProcess([string]$Executable,[string[]]$Arguments,[string]$Stdout,[string]$Stderr,[int]$TimeoutSeconds,[string]$Label) {
    $Process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $Root `
        -WindowStyle Hidden -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru
    $null = $Process.Handle
    $Exited = $Process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $Exited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw "$Label timed out after $TimeoutSeconds seconds"
    }
    $Process.WaitForExit()
    $Process.Refresh()
    $ExitCode = $Process.ExitCode
    if ($null -eq $ExitCode) { throw "$Label lost ExitCode under Windows PowerShell 5.1" }
    return [ordered]@{process_id=$Process.Id;exit_code=[int]$ExitCode}
}

foreach ($Path in @($Project,$Editor,$Python,$Baseline,$Freezer,$Runtime,$Validator)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required v003 input missing: $Path" }
}
if (-not (Test-Path -LiteralPath $Target -PathType Container)) { throw 'Existing eight-package target is missing' }
Assert-NoPriorResults
Assert-NoProcesses
$ValidatorExecutePath = Convert-ToSafeExecutePythonPath $Validator
$ExecutePythonArgument = '-ExecutePythonScript="{0}"' -f $ValidatorExecutePath
if ($ExecutePythonArgument.Contains('\') -or $ExecutePythonArgument.IndexOfAny([char[]](0..31)) -ge 0) {
    throw 'ExecutePythonScript argument regression: backslash/control escape survived normalization'
}
if ($ExecutePythonArgument -cne ('-ExecutePythonScript="C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Scripts/revalidate_assembly_line_native_kit_incident_v003.py"')) {
    throw "ExecutePythonScript exact command-line regression: $ExecutePythonArgument"
}
$ActualHashes = [ordered]@{
    baseline=Assert-Hash $Baseline $ExpectedHashes.baseline 'v003 baseline'
    freezer=Assert-Hash $Freezer $ExpectedHashes.freezer 'v003 freezer/verifier'
    runtime=Assert-Hash $Runtime $ExpectedHashes.runtime 'v003 runtime'
    validator=Assert-Hash $Validator $ExpectedHashes.validator 'v003 validator'
    failed_v002_log=Assert-Hash (Join-Path $FailedV002Run 'fresh_load_recovery_validation.log') $ExpectedHashes.failed_v002_log 'Failed v002 log'
    failed_v002_summary=Assert-Hash (Join-Path $FailedV002Run 'incident_recovery_summary_v002.json') $ExpectedHashes.failed_v002_summary 'Failed v002 summary'
}
$BaselinePayload = Get-Content -Raw -LiteralPath $Baseline | ConvertFrom-Json
if ([string]$BaselinePayload.'$schema' -cne 'lineboss/assembly-native-kit-v001/incident-retry-baseline/v3' `
        -or [string]$BaselinePayload.command_line_contract.execute_python_path_separator -cne '/' `
        -or [bool]$BaselinePayload.command_line_contract.backslash_or_control_character_authorized `
        -or [bool]$BaselinePayload.policy.importer_authorized `
        -or [bool]$BaselinePayload.policy.content_writes_authorized) {
    throw 'v003 baseline command-line/read-only identity drift'
}
$OfflineVerify = (& $Python $Freezer --verify-only 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0 -or $OfflineVerify -notmatch 'PASS__V003_INCIDENT_BOUND_RETRY_BASELINE_FULL_REVERIFY') {
    throw "v003 offline full reverify failed: $OfflineVerify"
}
if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { New-Item -ItemType Directory -Path $AuditRoot | Out-Null }
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Summary = [ordered]@{
    '$schema'='lineboss/audit/assembly-native-kit-v001/incident-retry-summary/v3'
    generated_utc=(Get-Date).ToUniversalTime().ToString('o')
    status='IN_PROGRESS'
    acknowledgement=$Acknowledgement
    run_root=$RunRoot
    target=$Target
    failed_v002_run=$FailedV002Run
    execute_python_path=$ValidatorExecutePath
    execute_python_argument=$ExecutePythonArgument
    command_line_forward_slash_regression_pass=$true
    expected_hashes=$ExpectedHashes
    actual_hashes=$ActualHashes
    offline_baseline_reverify=$OfflineVerify
    importer_process=$null
    validator_process=$null
    validation_receipt=$null
    content_writes_authorized=$false
}
try {
    Set-Item -LiteralPath "Env:\$RunEnvironment" -Value $RunRoot
    Set-Item -LiteralPath "Env:\$AckEnvironment" -Value $Acknowledgement
    $Arguments = @(
        ('"{0}"' -f $Project),'-Unattended','-NoSplash','-NoSound','-NullRHI','-NoCompile','-NoCompileEditor',
        '-NoLoadStartupPackages','-NoRestoreOpenAssetTabs',$ExecutePythonArgument,
        ('-abslog="{0}"' -f ((Join-Path $RunRoot 'fresh_load_recovery_validation.log').Replace('\','/')))
    )
    $Summary.validator_process = Invoke-GuardedProcess $Editor $Arguments `
        (Join-Path $RunRoot 'fresh_load_recovery_validation.stdout.log') `
        (Join-Path $RunRoot 'fresh_load_recovery_validation.stderr.log') 1800 `
        'Independent read-only Assembly v003 recovery validation'
    if ([int]$Summary.validator_process.exit_code -ne 0 -or (Test-Path -LiteralPath $FailReceipt)) {
        throw "v003 validator failed or emitted failure receipt: exit=$($Summary.validator_process.exit_code)"
    }
    if (-not (Test-Path -LiteralPath $PassReceipt -PathType Leaf)) { throw 'v003 PASS receipt missing' }
    $Receipt=Get-Content -Raw -LiteralPath $PassReceipt|ConvertFrom-Json
    if ([string]$Receipt.status -cne $ExpectedStatus `
            -or [int]$Receipt.process_id -ne [int]$Summary.validator_process.process_id `
            -or -not [bool]$Receipt.fresh_process_proof.distinct `
            -or [int]$Receipt.asset_count -ne 8 -or [int]$Receipt.lod_count_per_asset -ne 3 `
            -or [int]$Receipt.failed_v002_evidence_file_count -ne 4 `
            -or -not [bool]$Receipt.no_content_writes `
            -or -not [bool]$Receipt.importer_was_not_launched `
            -or -not [bool]$Receipt.original_and_failed_recovery_evidence_unchanged) {
        throw 'v003 PASS receipt complete retry/read-only contract drift'
    }
    $Summary.validation_receipt=[ordered]@{path=$PassReceipt;sha256=Get-Sha256 $PassReceipt;status=$Receipt.status}
    $Summary.status='PASS__V003_FORWARD_SLASH_COMMAND__READ_ONLY_FRESH_REVALIDATION__NO_IMPORTER_NO_CONTENT_WRITES'
}
catch {
    $Summary.status='FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V003'
    $Summary.error=$_.Exception.Message
    throw
}
finally {
    $Summary.generated_utc=(Get-Date).ToUniversalTime().ToString('o')
    $Encoding=New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($SummaryPath,($Summary|ConvertTo-Json -Depth 20)+"`n",$Encoding)
    if(Test-Path -LiteralPath "Env:\$RunEnvironment"){Remove-Item -LiteralPath "Env:\$RunEnvironment"}
    if(Test-Path -LiteralPath "Env:\$AckEnvironment"){Remove-Item -LiteralPath "Env:\$AckEnvironment"}
    Write-Output "LINE_BOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V003_SUMMARY=$SummaryPath"
}
