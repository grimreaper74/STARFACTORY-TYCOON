[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V004_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$Python = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Baseline = Join-Path $Root 'Scripts\assembly_line_native_kit_incident_retry_baseline_v004.json'
$Freezer = Join-Path $Root 'Scripts\freeze_assembly_line_native_kit_incident_retry_baseline_v004.py'
$Runtime = Join-Path $Root 'Scripts\assembly_line_native_kit_incident_retry_runtime_v004.py'
$Validator = Join-Path $Root 'Scripts\revalidate_assembly_line_native_kit_incident_v004.py'
$Target = Join-Path $Root 'Content\LineBoss\Candidates\AssemblyShop\AssemblyLineNativeKit_v001'
$FailedV002Run = Join-Path $Root 'Saved\Audits\AssemblyShop\AssemblyLineNativeKit_v001\IncidentRecovery_v002\20260815T030646Z-e8c9a5eb'
$FailedV003Run = Join-Path $Root 'Saved\Audits\AssemblyShop\AssemblyLineNativeKit_v001\IncidentRecovery_v003\20260815T032759Z-6c42095d'
$AuditRoot = Join-Path $Root 'Saved\Audits\AssemblyShop\AssemblyLineNativeKit_v001\IncidentRecovery_v004'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'incident_recovery_summary_v004.json'
$PassReceipt = Join-Path $RunRoot 'fresh_load_recovery_validation_receipt_v004.json'
$FailReceipt = Join-Path $RunRoot 'fresh_load_recovery_validation_failure_v004.json'
$ExpectedHashes = [ordered]@{
    baseline = '15E08E11108B4877F97DFC507F27840050352FF44F19833E7FCA2EEDC9D2EAEC'
    freezer = 'F6497D82A043BC1DE34C5DF66A74B2FD0EF7164CD2879BEA9A386E3A48724775'
    runtime = 'C2C8642F03A20EA37E7AFC2BC4C3078CFA7AED35106D55ED285DE27C9B1FE86D'
    validator = 'E2C0AFE1AADCFD03881CAC5689CD2088F61AD15DD863411915659002258ED09A'
    failed_v002_summary = 'CEBFD5239081C66FFCEEE84FCDB593DE5D588D01C06B4B6B5F89CEE7FD3362EC'
    failed_v003_receipt = '6483892E83834472030E513B401B86DD5FA2E2A69B0C43FFA553DFEAAF6B2143'
    failed_v003_summary = '046F877BF247055C7739A29FE8BC9D37C0A6FEB2EB5452977CDD4641915EFA1F'
}
$ExpectedStatus = 'PASS__V004_READ_ONLY_RELOAD__CHRONOLOGY_SEPARATED__8_ASSETS_24_LODS'
$RunEnvironment = 'LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V004_RUN_ROOT'
$AckEnvironment = 'LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V004_ACK'
$ResultNames = @('fresh_load_recovery_validation_receipt_v004.json',
    'fresh_load_recovery_validation_failure_v004.json','incident_recovery_summary_v004.json')

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
        $Details = ($Active | ForEach-Object { '{0}:{1}' -f $_.ProcessName,$_.Id }) -join ', '
        throw "Refusing v004 while Unreal/build processes are active: $Details"
    }
}

function Assert-NoPriorResults {
    if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { return }
    $Found = @(Get-ChildItem -LiteralPath $AuditRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $ResultNames -contains $_.Name })
    if ($Found.Count -gt 0) { throw "One-use v004 refuses every prior result: $($Found.FullName -join '; ')" }
}

function Convert-ToSafeExecutePythonPath([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "ExecutePythonScript file missing: $Path" }
    $Normalized = [IO.Path]::GetFullPath($Path).Replace('\','/')
    if ($Normalized.Contains('\') -or $Normalized.IndexOfAny([char[]](0..31)) -ge 0) {
        throw 'ExecutePythonScript path contains a forbidden backslash/control character'
    }
    if (-not $Normalized.EndsWith('.py',[StringComparison]::OrdinalIgnoreCase) -or
            -not $Normalized.StartsWith('C:/',[StringComparison]::OrdinalIgnoreCase)) {
        throw "ExecutePythonScript path is not an absolute normalized Python file: $Normalized"
    }
    return $Normalized
}

function Invoke-GuardedProcess([string]$Executable,[string[]]$Arguments,[string]$Stdout,[string]$Stderr,[int]$TimeoutSeconds) {
    $Process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $Root `
        -WindowStyle Hidden -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru
    $null = $Process.Handle
    if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw "v004 validator timed out after $TimeoutSeconds seconds"
    }
    $Process.WaitForExit(); $Process.Refresh()
    if ($null -eq $Process.ExitCode) { throw 'v004 validator lost ExitCode under Windows PowerShell 5.1' }
    return [ordered]@{process_id=$Process.Id;exit_code=[int]$Process.ExitCode}
}

foreach ($Path in @($Project,$Editor,$Python,$Baseline,$Freezer,$Runtime,$Validator)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required v004 input missing: $Path" }
}
if (-not (Test-Path -LiteralPath $Target -PathType Container)) { throw 'Existing eight-package target is missing' }
Assert-NoPriorResults
Assert-NoProcesses
$ValidatorExecutePath = Convert-ToSafeExecutePythonPath $Validator
$ExecutePythonArgument = '-ExecutePythonScript="{0}"' -f $ValidatorExecutePath
$ExactExecuteArgument = '-ExecutePythonScript="C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Scripts/revalidate_assembly_line_native_kit_incident_v004.py"'
if ($ExecutePythonArgument -cne $ExactExecuteArgument -or $ExecutePythonArgument.Contains('\') -or
        $ExecutePythonArgument.IndexOfAny([char[]](0..31)) -ge 0) {
    throw "v004 ExecutePythonScript command-line regression: $ExecutePythonArgument"
}
$ActualHashes = [ordered]@{
    baseline=Assert-Hash $Baseline $ExpectedHashes.baseline 'v004 baseline'
    freezer=Assert-Hash $Freezer $ExpectedHashes.freezer 'v004 freezer'
    runtime=Assert-Hash $Runtime $ExpectedHashes.runtime 'v004 runtime'
    validator=Assert-Hash $Validator $ExpectedHashes.validator 'v004 validator'
    failed_v002_summary=Assert-Hash (Join-Path $FailedV002Run 'incident_recovery_summary_v002.json') $ExpectedHashes.failed_v002_summary 'failed v002 summary'
    failed_v003_receipt=Assert-Hash (Join-Path $FailedV003Run 'fresh_load_recovery_validation_failure_v003.json') $ExpectedHashes.failed_v003_receipt 'failed v003 receipt'
    failed_v003_summary=Assert-Hash (Join-Path $FailedV003Run 'incident_recovery_summary_v003.json') $ExpectedHashes.failed_v003_summary 'failed v003 summary'
}
$BaselinePayload = Get-Content -Raw -LiteralPath $Baseline | ConvertFrom-Json
if ([string]$BaselinePayload.'$schema' -cne 'lineboss/assembly-native-kit-v001/incident-retry-baseline/v4' -or
        [bool]$BaselinePayload.policy.historical_hashes_applied_to_live_files -or
        [bool]$BaselinePayload.policy.importer_authorized -or [bool]$BaselinePayload.policy.content_writes_authorized) {
    throw 'v004 baseline chronology/read-only identity drift'
}
$OfflineVerify = (& $Python $Freezer --verify-only 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0 -or $OfflineVerify -notmatch 'PASS__V004_CHRONOLOGY_SEPARATED_BASELINE_FULL_REVERIFY') {
    throw "v004 offline full reverify failed: $OfflineVerify"
}
if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { New-Item -ItemType Directory -Path $AuditRoot | Out-Null }
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Summary = [ordered]@{
    '$schema'='lineboss/audit/assembly-native-kit-v001/incident-retry-summary/v4'
    generated_utc=(Get-Date).ToUniversalTime().ToString('o'); status='IN_PROGRESS'
    acknowledgement=$Acknowledgement; run_root=$RunRoot; target=$Target
    failed_v002_run=$FailedV002Run; failed_v003_run=$FailedV003Run
    execute_python_path=$ValidatorExecutePath; execute_python_argument=$ExecutePythonArgument
    chronology_separated_from_current_source=$true; expected_hashes=$ExpectedHashes
    actual_hashes=$ActualHashes; offline_baseline_reverify=$OfflineVerify
    importer_process=$null; validator_process=$null; validation_receipt=$null
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
        (Join-Path $RunRoot 'fresh_load_recovery_validation.stderr.log') 1800
    if ([int]$Summary.validator_process.exit_code -ne 0 -or (Test-Path -LiteralPath $FailReceipt)) {
        throw "v004 validator failed or emitted failure receipt: exit=$($Summary.validator_process.exit_code)"
    }
    if (-not (Test-Path -LiteralPath $PassReceipt -PathType Leaf)) { throw 'v004 PASS receipt missing' }
    $Receipt=Get-Content -Raw -LiteralPath $PassReceipt|ConvertFrom-Json
    if ([string]$Receipt.status -cne $ExpectedStatus -or
            [int]$Receipt.process_id -ne [int]$Summary.validator_process.process_id -or
            -not [bool]$Receipt.fresh_process_proof.distinct -or
            [int]$Receipt.asset_count -ne 8 -or [int]$Receipt.lod_count_per_asset -ne 3 -or
            [int]$Receipt.failed_v002_evidence_file_count -ne 4 -or
            [int]$Receipt.failed_v003_evidence_file_count -ne 5 -or
            [bool]$Receipt.historical_hashes_applied_to_live_files -or
            -not [bool]$Receipt.no_content_writes -or -not [bool]$Receipt.importer_was_not_launched) {
        throw 'v004 PASS receipt chronology/read-only contract drift'
    }
    $Summary.validation_receipt=[ordered]@{path=$PassReceipt;sha256=Get-Sha256 $PassReceipt;status=$Receipt.status}
    $Summary.status='PASS__V004_CHRONOLOGY_SEPARATED__READ_ONLY_FRESH_REVALIDATION'
}
catch {
    $Summary.status='FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V004'
    $Summary.error=$_.Exception.Message
    throw
}
finally {
    $Summary.generated_utc=(Get-Date).ToUniversalTime().ToString('o')
    $Encoding=New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($SummaryPath,($Summary|ConvertTo-Json -Depth 20)+"`n",$Encoding)
    if(Test-Path -LiteralPath "Env:\$RunEnvironment"){Remove-Item -LiteralPath "Env:\$RunEnvironment"}
    if(Test-Path -LiteralPath "Env:\$AckEnvironment"){Remove-Item -LiteralPath "Env:\$AckEnvironment"}
    Write-Output "LINE_BOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V004_SUMMARY=$SummaryPath"
}
