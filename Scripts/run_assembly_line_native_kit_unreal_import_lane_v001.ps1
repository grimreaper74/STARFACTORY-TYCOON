[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('IMPORT_FROZEN_ASSEMBLY_LINE_NATIVE_KIT_V001_BASELINE_V001_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$Python = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$Baseline = Join-Path $Root 'Scripts\assembly_line_native_kit_unreal_import_baseline_v001.json'
$Freezer = Join-Path $Root 'Scripts\freeze_assembly_line_native_kit_unreal_import_baseline_v001.py'
$Common = Join-Path $Root 'Scripts\assembly_line_native_kit_unreal_runtime_v001.py'
$Importer = Join-Path $Root 'Scripts\import_assembly_line_native_kit_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_assembly_line_native_kit_v001.py'
$Destination = Join-Path $Root 'Content\LineBoss\Candidates\AssemblyShop\AssemblyLineNativeKit_v001'
$AuditRoot = Join-Path $Root 'Saved\Audits\AssemblyShop\AssemblyLineNativeKit_v001\UnrealImportLane_v001'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_v001.json'
$ImportReceipt = Join-Path $RunRoot 'import_receipt_v001.json'
$ImportFailure = Join-Path $RunRoot 'import_failure_v001.json'
$ValidationReceipt = Join-Path $RunRoot 'fresh_load_validation_receipt_v001.json'
$ValidationFailure = Join-Path $RunRoot 'fresh_load_validation_failure_v001.json'
$ExpectedHashes = [ordered]@{
    baseline = '041C802023D14ADE7EC418EF7488679D7F4A03550471AE38E2DC80B310E731BA'
    freezer = 'A7CFD24D4A3804EFA0B0003749B1D85D48905533F0A59770BC8AA0256C9397DC'
    common = '597638FE1A11AD67B3F54090B57529C07757C48A8378EAF84F90157DCA2D73F0'
    importer = '15DCBE67A54D0A8E78E4C7D30C9520AD173B02F72003ECFC166DFAF23C8A9B76'
    validator = 'D19420B06776BBDF2FFC2B19ADB3B66458171FB37DD2775BE99906317F82C6BB'
}
$ImportStatus = 'PASS__HASH_GUARDED_FRESH_IMPORT__8_ASSETS__24_AUTHORED_LODS__ASSEMBLY_NATIVE_KIT_V001'
$ValidationStatus = 'PASS__INDEPENDENT_FRESH_PROCESS_RELOAD__8_ASSETS__24_AUTHORED_LODS__ASSEMBLY_NATIVE_KIT_V001'
$RunEnvironment = 'LINEBOSS_ASSEMBLY_NATIVE_KIT_V001_RUN_ROOT'
$AckEnvironment = 'LINEBOSS_ASSEMBLY_NATIVE_KIT_V001_ACK'
$ResultNames = @('import_receipt_v001.json','import_failure_v001.json',
    'fresh_load_validation_receipt_v001.json','fresh_load_validation_failure_v001.json','lane_summary_v001.json')

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required file missing: $Path" }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Assert-Hash([string]$Path, [string]$Expected, [string]$Label) {
    $Actual = Get-Sha256 $Path
    if ($Actual -cne $Expected) { throw "$Label hash drift: expected=$Expected actual=$Actual" }
    return $Actual
}

function Assert-NoProcesses {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -gt 0) {
        throw "Refusing isolated import while Unreal/build processes are active: $(($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', ')"
    }
}

function Assert-NoPriorResults {
    if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { return }
    $Found = @(Get-ChildItem -LiteralPath $AuditRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $ResultNames -contains $_.Name })
    if ($Found.Count -gt 0) {
        throw "One-shot lane v001 refuses every pre-existing v001 result (PASS or FAIL): $($Found.FullName -join '; ')"
    }
}

function Write-Json([string]$Path, [object]$Payload) {
    if (Test-Path -LiteralPath $Path) { throw "Refusing to overwrite evidence: $Path" }
    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, ($Payload | ConvertTo-Json -Depth 20) + "`n", $Encoding)
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
    return [ordered]@{ process_id = $Process.Id; exit_code = [int]$ExitCode }
}

function Read-Receipt([string]$Path,[string]$ExpectedStatus,[string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "$Label receipt missing: $Path" }
    $Payload = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ([string]$Payload.status -cne $ExpectedStatus) { throw "$Label receipt status drift: $($Payload.status)" }
    return $Payload
}

if ((Resolve-Path -LiteralPath $Root).Path -cne $Root) { throw 'Exact project-root identity drift' }
foreach ($Path in @($Project,$Editor,$Python,$Baseline,$Freezer,$Common,$Importer,$Validator)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required lane input missing: $Path" }
}
if (Test-Path -LiteralPath $Destination) { throw "Target namespace exists; overwrite/reimport forbidden: $Destination" }
Assert-NoPriorResults
Assert-NoProcesses
$ActualHashes = [ordered]@{
    baseline = Assert-Hash $Baseline $ExpectedHashes.baseline 'Baseline'
    freezer = Assert-Hash $Freezer $ExpectedHashes.freezer 'Offline freezer/verifier'
    common = Assert-Hash $Common $ExpectedHashes.common 'Shared UE runtime'
    importer = Assert-Hash $Importer $ExpectedHashes.importer 'UE importer'
    validator = Assert-Hash $Validator $ExpectedHashes.validator 'Fresh validator'
}
$BaselinePayload = Get-Content -Raw -LiteralPath $Baseline | ConvertFrom-Json
if ([string]$BaselinePayload.'$schema' -cne 'lineboss/assembly-line-native-kit-v001/unreal-import-baseline/v1' `
        -or [string]$BaselinePayload.status -cne 'FROZEN__ASSEMBLY_LINE_NATIVE_KIT_V001_UNREAL_IMPORT_BASELINE_V001' `
        -or [int]$BaselinePayload.destination.expected_asset_count -ne 8 `
        -or [int]$BaselinePayload.destination.expected_lod_count_per_asset -ne 3 `
        -or [int]$BaselinePayload.destination.expected_source_fbx_count -ne 24 `
        -or [bool]$BaselinePayload.policy.overwrite_reimport_delete_authorized) {
    throw 'Frozen baseline identity/safety drift'
}
$BaselineVerifyOutput = (& $Python $Freezer --verify-only 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0 -or $BaselineVerifyOutput -notmatch 'PASS__FULL_SOURCE_AND_PROTECTED_BASELINE_REVERIFY') {
    throw "Full offline source/protected baseline reverify failed: $BaselineVerifyOutput"
}
if (-not (Test-Path -LiteralPath $AuditRoot -PathType Container)) { New-Item -ItemType Directory -Path $AuditRoot | Out-Null }
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Summary = [ordered]@{
    '$schema' = 'lineboss/audit/assembly-native-kit-v001/import-lane-summary/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'IN_PROGRESS'
    acknowledgement = $Acknowledgement
    project = $Project
    destination = $Destination
    run_root = $RunRoot
    expected_hashes = $ExpectedHashes
    actual_hashes = $ActualHashes
    offline_baseline_reverify = $BaselineVerifyOutput
    import_process = $null
    validation_process = $null
    import_receipt = $null
    validation_receipt = $null
    recovery = 'No automatic cleanup: any partial packages/evidence remain for explicit review.'
}
try {
    Set-Item -LiteralPath "Env:\$RunEnvironment" -Value $RunRoot
    Set-Item -LiteralPath "Env:\$AckEnvironment" -Value $Acknowledgement
    $ImportArgs = @(
        ('"{0}"' -f $Project), '-Unattended','-NoSplash','-NoSound','-NullRHI','-NoCompile','-NoCompileEditor',
        '-NoLoadStartupPackages','-NoRestoreOpenAssetTabs', ('-ExecutePythonScript="{0}"' -f $Importer),
        ('-abslog="{0}"' -f (Join-Path $RunRoot 'unreal_import.log'))
    )
    $Summary.import_process = Invoke-GuardedProcess $Editor $ImportArgs (Join-Path $RunRoot 'unreal_import.stdout.log') `
        (Join-Path $RunRoot 'unreal_import.stderr.log') 1800 'Assembly native-kit import'
    if ([int]$Summary.import_process.exit_code -ne 0 -or (Test-Path -LiteralPath $ImportFailure)) {
        throw "Import failed or emitted failure receipt: exit=$($Summary.import_process.exit_code)"
    }
    $Imported = Read-Receipt $ImportReceipt $ImportStatus 'Import'
    if ([int]$Imported.process_id -ne [int]$Summary.import_process.process_id `
            -or [int]$Imported.asset_count -ne 8 -or [int]$Imported.source_fbx_count -ne 24 `
            -or [int]$Imported.custom_lods_appended -ne 16 `
            -or @($Imported.assets.PSObject.Properties).Count -ne 8 `
            -or -not [bool]$Imported.per_asset_collision_suitability_verified) {
        throw 'Import receipt complete 8-asset/24-LOD contract drift'
    }
    $Guard = $Imported.interchange_fbx_legacy_custom_lod_guard
    if (-not [bool]$Guard.restore_attempted_in_finally -or [int]$Guard.restored_value -ne [int]$Guard.previous_value) {
        throw 'Import receipt lacks legacy FBX custom-LOD CVar restoration proof'
    }
    $Summary.import_receipt = [ordered]@{ path=$ImportReceipt; sha256=Get-Sha256 $ImportReceipt; status=$Imported.status }
    Assert-NoProcesses
    $ValidationArgs = @(
        ('"{0}"' -f $Project), '-Unattended','-NoSplash','-NoSound','-NullRHI','-NoCompile','-NoCompileEditor',
        '-NoLoadStartupPackages','-NoRestoreOpenAssetTabs', ('-ExecutePythonScript="{0}"' -f $Validator),
        ('-abslog="{0}"' -f (Join-Path $RunRoot 'fresh_load_validation.log'))
    )
    $Summary.validation_process = Invoke-GuardedProcess $Editor $ValidationArgs `
        (Join-Path $RunRoot 'fresh_load_validation.stdout.log') `
        (Join-Path $RunRoot 'fresh_load_validation.stderr.log') 1800 'Independent Assembly native-kit reload validation'
    if ([int]$Summary.validation_process.exit_code -ne 0 -or (Test-Path -LiteralPath $ValidationFailure)) {
        throw "Fresh validator failed or emitted failure receipt: exit=$($Summary.validation_process.exit_code)"
    }
    $Validated = Read-Receipt $ValidationReceipt $ValidationStatus 'Fresh validator'
    if ([int]$Validated.process_id -ne [int]$Summary.validation_process.process_id `
            -or -not [bool]$Validated.fresh_process_proof.distinct `
            -or [int]$Validated.asset_count -ne 8 `
            -or -not [bool]$Validated.target_package_hashes_unchanged_by_fresh_load `
            -or -not [bool]$Validated.complete_source_config_savegames_existing_content_and_maps_unchanged `
            -or -not [bool]$Validated.source_manifest_geometry_roundtrip_and_freeze_reverified `
            -or -not [bool]$Validated.per_asset_collision_persisted `
            -or -not [bool]$Validated.nanite_off_all_assets) {
        throw 'Fresh validator receipt complete immutable contract drift'
    }
    $Summary.validation_receipt = [ordered]@{ path=$ValidationReceipt; sha256=Get-Sha256 $ValidationReceipt; status=$Validated.status }
    $Summary.status = 'PASS__ONE_SHOT_FRESH_IMPORT_AND_INDEPENDENT_RELOAD__ASSEMBLY_NATIVE_KIT_V001'
}
catch {
    $Summary.status = 'FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_V001_UNREAL_IMPORT_LANE'
    $Summary.error = $_.Exception.Message
    throw
}
finally {
    $Summary.generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($SummaryPath, ($Summary | ConvertTo-Json -Depth 20) + "`n", $Encoding)
    if (Test-Path -LiteralPath "Env:\$RunEnvironment") { Remove-Item -LiteralPath "Env:\$RunEnvironment" }
    if (Test-Path -LiteralPath "Env:\$AckEnvironment") { Remove-Item -LiteralPath "Env:\$AckEnvironment" }
    Write-Output "LINE_BOSS_ASSEMBLY_NATIVE_KIT_V001_LANE_SUMMARY=$SummaryPath"
}
