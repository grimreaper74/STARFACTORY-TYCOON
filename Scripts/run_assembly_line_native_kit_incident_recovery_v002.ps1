[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V002_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$Python = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Baseline = Join-Path $Root 'Scripts\assembly_line_native_kit_incident_recovery_baseline_v002.json'
$Freezer = Join-Path $Root 'Scripts\freeze_assembly_line_native_kit_incident_recovery_baseline_v002.py'
$Runtime = Join-Path $Root 'Scripts\assembly_line_native_kit_incident_recovery_runtime_v002.py'
$Validator = Join-Path $Root 'Scripts\revalidate_assembly_line_native_kit_incident_v002.py'
$Target = Join-Path $Root 'Content\LineBoss\Candidates\AssemblyShop\AssemblyLineNativeKit_v001'
$OriginalRun = Join-Path $Root 'Saved\Audits\AssemblyShop\AssemblyLineNativeKit_v001\UnrealImportLane_v001\20260815T025138Z-2b421583'
$OriginalImportReceipt = Join-Path $OriginalRun 'import_receipt_v001.json'
$OriginalFailureReceipt = Join-Path $OriginalRun 'fresh_load_validation_failure_v001.json'
$AuditRoot = Join-Path $Root 'Saved\Audits\AssemblyShop\AssemblyLineNativeKit_v001\IncidentRecovery_v002'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'incident_recovery_summary_v002.json'
$PassReceipt = Join-Path $RunRoot 'fresh_load_recovery_validation_receipt_v002.json'
$FailReceipt = Join-Path $RunRoot 'fresh_load_recovery_validation_failure_v002.json'
$ExpectedHashes = [ordered]@{
    baseline = 'CDD41027FCBB556ED3A3EF472B804275677F023CDCCA8D394DC454BBF94C1520'
    freezer = 'FDB7A841FED8F6CCC6240CF3DC2F9CC017DC60DE272CE32AC562C4AAB7325E5C'
    runtime = '405244C7CF359085A42AD05B3CC0A17385E7BB6B6BE3463C2F0612298739454F'
    validator = '7263BF87CBA3049555EE36BC378EFE284C9279565A501BDDE81F33700F9455C9'
    original_import_receipt = 'C0E1F8D3E7B6EEBB2780067671AF408C53368DEA9370B3AA56B9F7F3AAFD49F7'
    original_failure_receipt = '269F732E2433EEC7948EB17F6FFE453D18F6CEEA3CF70239A99B67517799D57B'
}
$ExpectedStatus = 'PASS__INCIDENT_BOUND_INDEPENDENT_FRESH_RELOAD__EXISTING_8_ASSETS_24_LODS__NO_CONTENT_WRITES'
$RunEnvironment = 'LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002_RUN_ROOT'
$AckEnvironment = 'LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002_ACK'
$ResultNames = @('fresh_load_recovery_validation_receipt_v002.json',
    'fresh_load_recovery_validation_failure_v002.json','incident_recovery_summary_v002.json')

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
        throw "Refusing recovery while Unreal/build processes are active: $(($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', ')"
    }
}

function Assert-NoPriorResults {
    if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { return }
    $Found = @(Get-ChildItem -LiteralPath $AuditRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $ResultNames -contains $_.Name })
    if ($Found.Count -gt 0) {
        throw "One-use incident recovery v002 refuses every prior result (PASS or FAIL): $($Found.FullName -join '; ')"
    }
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

foreach ($Path in @($Project,$Editor,$Python,$Baseline,$Freezer,$Runtime,$Validator,$OriginalImportReceipt,$OriginalFailureReceipt)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required recovery input missing: $Path" }
}
if (-not (Test-Path -LiteralPath $Target -PathType Container)) { throw 'Existing eight-package target namespace is missing' }
Assert-NoPriorResults
Assert-NoProcesses
$ActualHashes = [ordered]@{
    baseline=Assert-Hash $Baseline $ExpectedHashes.baseline 'Successor baseline'
    freezer=Assert-Hash $Freezer $ExpectedHashes.freezer 'Offline successor freezer/verifier'
    runtime=Assert-Hash $Runtime $ExpectedHashes.runtime 'Recovery runtime'
    validator=Assert-Hash $Validator $ExpectedHashes.validator 'Read-only fresh validator'
    original_import_receipt=Assert-Hash $OriginalImportReceipt $ExpectedHashes.original_import_receipt 'Original PASS import receipt'
    original_failure_receipt=Assert-Hash $OriginalFailureReceipt $ExpectedHashes.original_failure_receipt 'Original failure receipt'
}
$BaselinePayload = Get-Content -Raw -LiteralPath $Baseline | ConvertFrom-Json
if ([string]$BaselinePayload.'$schema' -cne 'lineboss/assembly-native-kit-v001/incident-recovery-baseline/v2' `
        -or [string]$BaselinePayload.status -cne 'FROZEN__ASSEMBLY_NATIVE_KIT_V001_INCIDENT_RECOVERY_BASELINE_V002__READ_ONLY_REVALIDATION_ONLY' `
        -or [bool]$BaselinePayload.policy.importer_authorized `
        -or [bool]$BaselinePayload.policy.content_writes_authorized `
        -or [int]$BaselinePayload.incident.settled_source_count -ne 278 `
        -or @($BaselinePayload.incident.target_packages).Count -ne 8) {
    throw 'Successor incident/read-only baseline identity drift'
}
$OfflineVerify = (& $Python $Freezer --verify-only 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0 -or $OfflineVerify -notmatch 'PASS__INCIDENT_BOUND_SUCCESSOR_BASELINE_FULL_REVERIFY') {
    throw "Full offline successor reverify failed: $OfflineVerify"
}
if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { New-Item -ItemType Directory -Path $AuditRoot | Out-Null }
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Summary = [ordered]@{
    '$schema'='lineboss/audit/assembly-native-kit-v001/incident-recovery-summary/v2'
    generated_utc=(Get-Date).ToUniversalTime().ToString('o')
    status='IN_PROGRESS'
    acknowledgement=$Acknowledgement
    run_root=$RunRoot
    target=$Target
    original_run=$OriginalRun
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
        '-NoLoadStartupPackages','-NoRestoreOpenAssetTabs',('-ExecutePythonScript="{0}"' -f $Validator),
        ('-abslog="{0}"' -f (Join-Path $RunRoot 'fresh_load_recovery_validation.log'))
    )
    $Summary.validator_process = Invoke-GuardedProcess $Editor $Arguments `
        (Join-Path $RunRoot 'fresh_load_recovery_validation.stdout.log') `
        (Join-Path $RunRoot 'fresh_load_recovery_validation.stderr.log') 1800 `
        'Independent read-only Assembly incident recovery validation'
    if ([int]$Summary.validator_process.exit_code -ne 0 -or (Test-Path -LiteralPath $FailReceipt)) {
        throw "Recovery validator failed or emitted failure receipt: exit=$($Summary.validator_process.exit_code)"
    }
    if (-not (Test-Path -LiteralPath $PassReceipt -PathType Leaf)) { throw 'Recovery PASS receipt missing' }
    $Receipt = Get-Content -Raw -LiteralPath $PassReceipt | ConvertFrom-Json
    if ([string]$Receipt.status -cne $ExpectedStatus `
            -or [int]$Receipt.process_id -ne [int]$Summary.validator_process.process_id `
            -or -not [bool]$Receipt.fresh_process_proof.distinct `
            -or [int]$Receipt.asset_count -ne 8 -or [int]$Receipt.lod_count_per_asset -ne 3 `
            -or [int]$Receipt.settled_source_file_count -ne 278 `
            -or [int]$Receipt.exact_incident_addition_count -ne 2 `
            -or -not [bool]$Receipt.no_content_writes `
            -or -not [bool]$Receipt.importer_was_not_launched `
            -or -not [bool]$Receipt.full_settled_protected_state_unchanged `
            -or -not [bool]$Receipt.original_baseline_run_receipts_and_logs_unchanged) {
        throw 'Recovery PASS receipt complete incident/read-only contract drift'
    }
    $Summary.validation_receipt=[ordered]@{path=$PassReceipt;sha256=Get-Sha256 $PassReceipt;status=$Receipt.status}
    $Summary.status='PASS__INCIDENT_RECOVERY_V002__READ_ONLY_FRESH_REVALIDATION__NO_IMPORTER_NO_CONTENT_WRITES'
}
catch {
    $Summary.status='FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002'
    $Summary.error=$_.Exception.Message
    throw
}
finally {
    $Summary.generated_utc=(Get-Date).ToUniversalTime().ToString('o')
    $Encoding=New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($SummaryPath,($Summary|ConvertTo-Json -Depth 20)+"`n",$Encoding)
    if(Test-Path -LiteralPath "Env:\$RunEnvironment"){Remove-Item -LiteralPath "Env:\$RunEnvironment"}
    if(Test-Path -LiteralPath "Env:\$AckEnvironment"){Remove-Item -LiteralPath "Env:\$AckEnvironment"}
    Write-Output "LINE_BOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002_SUMMARY=$SummaryPath"
}
