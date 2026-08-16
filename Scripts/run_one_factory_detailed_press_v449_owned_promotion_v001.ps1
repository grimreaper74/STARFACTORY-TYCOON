[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('PROMOTE_EXACT_PRE_MESHY_V449_PRESS_VISUAL_INTO_ONEFACTORY_NATIVE_ROOT_ONCE')]
    [string]$Acknowledgement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Root = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
$Project = Join-Path $Root 'LineBossCarFactory.uproject'
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Python = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$BaseContract = Join-Path $Root 'Scripts\one_factory_detailed_press_v001_contract.py'
$PromotionContract = Join-Path $Root 'Scripts\one_factory_detailed_press_v449_promotion_contract.py'
$Importer = Join-Path $Root 'Scripts\promote_one_factory_detailed_press_v449_owned_v001.py'
$Validator = Join-Path $Root 'Scripts\validate_one_factory_detailed_press_v449_owned_fresh_load_v001.py'
$EvidenceTest = Join-Path $Root 'Scripts\tests\test_one_factory_detailed_press_v001.py'
$PromotionTest = Join-Path $Root 'Scripts\tests\test_one_factory_detailed_press_v449_promotion_v001.py'
$Destination = Join-Path $Root 'Content\LineBoss\Factory\OneFactory\v001\Native\Press\DetailedPresentation_v001'
$BuildReceipt = Join-Path $Root 'Saved\Audits\OneFactory\DetailedPressPresentation_v001\v449_owned_promotion_build_v001.json'
$ValidationReceipt = Join-Path $Root 'Saved\Audits\OneFactory\DetailedPressPresentation_v001\v449_owned_promotion_fresh_load_validation_v001.json'
$AuditRoot = Join-Path $Root 'Saved\Audits\OneFactory\DetailedPressPresentation_v001\PromotionLane_v001'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$RunRoot = Join-Path $AuditRoot $Stamp
$SummaryPath = Join-Path $RunRoot 'lane_summary_v001.json'
$ExpectedHashes = [ordered]@{
    base_contract = 'E04F279A8704D1D7ED8EE09568B8F8D8DA736CF51E600F31DC2B5B3F89A5578E'
    promotion_contract = '91BA03BCD2BEB402FE47FCD72D2E02FF8AE4D4749AC530066DFCA5648E58580F'
    importer = '9E2003D18CE9F7A6592B6DC9E7AD6EC5D01867CE6D9E516C62352BF35520F3FC'
    validator = '0AEFB2304C1EF4B0A55A2CC9847297CDC5741826B8E53581B74758E3E694A473'
    evidence_test = '841C8BE62D835D46AD8E9A1EBC4F9D39B8ED2B988B2C475E503E5DE2C7E9F0EB'
    promotion_test = '6679684D2A8A239EF2C185C3B7D2953D0D1C67756783D69F231D911A56F769F2'
}
$ExpectedBuildStatus = 'PASS__EXACT_PRE_MESHY_V449_DUPLICATED_AND_REBOUND_IN_ONEFACTORY_NATIVE_PRESS_ROOT__NO_MAP_SAVED'
$ExpectedValidationStatus = 'PASS__FRESH_PROCESS_OWNED_V449_PRESS_PACK_EXACT_14_ASSETS_306_REBOUND_SLOTS__NO_EXTERNAL_PROJECT_DEPENDENCIES'
$ImporterForUnreal = $Importer.Replace('\','/')
$ValidatorForUnreal = $Validator.Replace('\','/')

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Assert-Hash([string]$Path, [string]$Expected, [string]$Label) {
    $Actual = Get-Sha256 $Path
    if ($Actual -cne $Expected) {
        throw "$Label hash drift: expected=$Expected actual=$Actual"
    }
    return $Actual
}

function Assert-NoUnrealOrBuildProcesses {
    $Names = @('UnrealEditor','UnrealEditor-Cmd','UnrealBuildTool','AutomationTool','RunUAT','ShaderCompileWorker')
    $Active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $Names -contains $_.ProcessName })
    if ($Active.Count -gt 0) {
        $Rows = ($Active | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', '
        throw "Refusing isolated promotion while Unreal/build processes are active: $Rows"
    }
}

function Invoke-GuardedProcess(
    [string]$Executable,
    [string[]]$Arguments,
    [string]$Stdout,
    [string]$Stderr,
    [int]$TimeoutSeconds,
    [string]$Label
) {
    $Process = Start-Process -FilePath $Executable -ArgumentList $Arguments `
        -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $Stdout `
        -RedirectStandardError $Stderr -PassThru
    $null = $Process.Handle
    if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw "$Label timed out after $TimeoutSeconds seconds"
    }
    $Process.WaitForExit()
    $Process.Refresh()
    if ($null -eq $Process.ExitCode) {
        throw "$Label lost its process exit code"
    }
    return [ordered]@{ process_id = $Process.Id; exit_code = [int]$Process.ExitCode }
}

function Read-Json([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label missing: $Path"
    }
    return Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
}

if ((Resolve-Path -LiteralPath $Root).Path -cne $Root) {
    throw 'Exact project-root identity drift'
}
foreach ($Path in @($Project,$Editor,$Python,$BaseContract,$PromotionContract,$Importer,$Validator,$EvidenceTest,$PromotionTest)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required lane input missing: $Path"
    }
}
if ($ImporterForUnreal -match '[\x00-\x1F\\]' -or $ValidatorForUnreal -match '[\x00-\x1F\\]') {
    throw 'ExecutePythonScript paths must be forward-slash absolute paths without control characters'
}
if (Test-Path -LiteralPath $Destination) {
    throw "Owned v449 target namespace already exists; overwrite is forbidden: $Destination"
}
if ((Test-Path -LiteralPath $BuildReceipt) `
        -or (Test-Path -LiteralPath $ValidationReceipt)) {
    throw 'One-shot v449 owned promotion receipt already exists; overwrite/retry is forbidden'
}
Assert-NoUnrealOrBuildProcesses

$ActualHashes = [ordered]@{
    base_contract = Assert-Hash $BaseContract $ExpectedHashes.base_contract 'Base evidence contract'
    promotion_contract = Assert-Hash $PromotionContract $ExpectedHashes.promotion_contract 'Promotion contract'
    importer = Assert-Hash $Importer $ExpectedHashes.importer 'Promotion importer'
    validator = Assert-Hash $Validator $ExpectedHashes.validator 'Fresh-load validator'
    evidence_test = Assert-Hash $EvidenceTest $ExpectedHashes.evidence_test 'Base evidence tests'
    promotion_test = Assert-Hash $PromotionTest $ExpectedHashes.promotion_test 'Promotion tests'
}

New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Summary = [ordered]@{
    '$schema' = 'cairnwell/one-factory/detailed-press/v449-owned-promotion-lane/v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'IN_PROGRESS'
    acknowledgement = $Acknowledgement
    project = $Project
    destination = $Destination
    expected_hashes = $ExpectedHashes
    actual_hashes = $ActualHashes
    offline_preflight = $null
    import_process = $null
    build_receipt = $null
    validation_process = $null
    validation_receipt = $null
    no_map_load_or_save = $true
    no_ubt_invoked = $true
    error = $null
}

try {
    $TestProcess = Invoke-GuardedProcess $Python @(
        '-B','-m','unittest',
        'Scripts/tests/test_one_factory_detailed_press_v001.py',
        'Scripts/tests/test_one_factory_detailed_press_v449_promotion_v001.py'
    ) (Join-Path $RunRoot 'offline_tests.stdout.log') `
      (Join-Path $RunRoot 'offline_tests.stderr.log') 300 'Offline promotion tests'
    if ([int]$TestProcess.exit_code -ne 0) {
        throw "Offline promotion tests failed: exit=$($TestProcess.exit_code)"
    }
    $ContractProcess = Invoke-GuardedProcess $Python @(
        '-B',('"{0}"' -f $PromotionContract),'--project-root',
        ('"{0}"' -f $Root),'--require-destination-absent'
    ) (Join-Path $RunRoot 'offline_contract.stdout.log') `
      (Join-Path $RunRoot 'offline_contract.stderr.log') 300 'Offline exact-source contract'
    if ([int]$ContractProcess.exit_code -ne 0) {
        throw "Offline exact-source contract failed: exit=$($ContractProcess.exit_code)"
    }
    $Summary.offline_preflight = [ordered]@{
        tests = $TestProcess
        source_contract = $ContractProcess
    }

    Assert-NoUnrealOrBuildProcesses
    $ImportArgs = @(
        ('"{0}"' -f $Project), '/Engine/Maps/Entry',
        '-unattended','-nop4','-nosplash','-nosound','-NullRHI',
        '-NoCompile','-NoCompileEditor','-NoAutoSave','-NoSaveOnExit',
        '-NoLoadStartupPackages','-NoRestoreOpenAssetTabs','-stdout','-FullStdOutLogOutput',
        ('-ExecutePythonScript="{0}"' -f $ImporterForUnreal),
        ('-abslog="{0}"' -f (Join-Path $RunRoot 'unreal_promotion.log'))
    )
    $Summary.import_process = Invoke-GuardedProcess $Editor $ImportArgs `
        (Join-Path $RunRoot 'unreal_promotion.stdout.log') `
        (Join-Path $RunRoot 'unreal_promotion.stderr.log') 1800 'Owned v449 promotion'
    if ([int]$Summary.import_process.exit_code -ne 0) {
        throw "Owned v449 promotion failed: exit=$($Summary.import_process.exit_code)"
    }
    $Built = Read-Json $BuildReceipt 'Owned v449 build receipt'
    if ([string]$Built.status -cne $ExpectedBuildStatus `
            -or [int]$Built.destination_asset_count -ne 14 `
            -or [int]$Built.material_slot_count -ne 306 `
            -or [string]$Built.editor_bootstrap_world -cne '/Engine/Maps/Entry.Entry' `
            -or [bool]$Built.map_loaded -or [bool]$Built.map_saved `
            -or [bool]$Built.source_assets_modified) {
        throw 'Owned v449 build receipt contract drift'
    }
    $Summary.build_receipt = [ordered]@{
        path = $BuildReceipt
        sha256 = Get-Sha256 $BuildReceipt
        status = [string]$Built.status
    }

    Assert-NoUnrealOrBuildProcesses
    $ValidationArgs = @(
        ('"{0}"' -f $Project), '/Engine/Maps/Entry',
        '-unattended','-nop4','-nosplash','-nosound','-NullRHI',
        '-NoCompile','-NoCompileEditor','-NoAutoSave','-NoSaveOnExit',
        '-NoLoadStartupPackages','-NoRestoreOpenAssetTabs','-stdout','-FullStdOutLogOutput',
        ('-ExecutePythonScript="{0}"' -f $ValidatorForUnreal),
        ('-abslog="{0}"' -f (Join-Path $RunRoot 'fresh_load_validation.log'))
    )
    $Summary.validation_process = Invoke-GuardedProcess $Editor $ValidationArgs `
        (Join-Path $RunRoot 'fresh_load_validation.stdout.log') `
        (Join-Path $RunRoot 'fresh_load_validation.stderr.log') 1800 `
        'Independent owned v449 fresh-load validation'
    if ([int]$Summary.validation_process.exit_code -ne 0) {
        throw "Independent owned v449 fresh-load validation failed: exit=$($Summary.validation_process.exit_code)"
    }
    $Validated = Read-Json $ValidationReceipt 'Owned v449 validation receipt'
    if ([string]$Validated.status -cne $ExpectedValidationStatus `
            -or [int]$Validated.destination_asset_count -ne 14 `
            -or [int]$Validated.material_slot_count -ne 306 `
            -or [string]$Validated.editor_bootstrap_world -cne '/Engine/Maps/Entry.Entry' `
            -or @($Validated.unexpected_project_dependencies).Count -ne 0 `
            -or [bool]$Validated.map_loaded -or [bool]$Validated.map_saved) {
        throw 'Owned v449 fresh-load validation receipt contract drift'
    }
    $Summary.validation_receipt = [ordered]@{
        path = $ValidationReceipt
        sha256 = Get-Sha256 $ValidationReceipt
        status = [string]$Validated.status
    }

    $FinalProcess = Invoke-GuardedProcess $Python @(
        '-B',('"{0}"' -f $PromotionContract),'--project-root',
        ('"{0}"' -f $Root),'--build-receipt',('"{0}"' -f $BuildReceipt)
    ) (Join-Path $RunRoot 'final_offline_contract.stdout.log') `
      (Join-Path $RunRoot 'final_offline_contract.stderr.log') 300 'Final offline receipt/hash contract'
    if ([int]$FinalProcess.exit_code -ne 0) {
        throw "Final offline receipt/hash contract failed: exit=$($FinalProcess.exit_code)"
    }
    Assert-NoUnrealOrBuildProcesses
    $Summary.status = 'PASS__EXACT_V449_OWNED_PRESS_PACK_PROMOTED_AND_FRESH_RELOADED__NO_MAP_SAVE__NO_UBT'
}
catch {
    $Summary.status = 'FAIL_CLOSED__ONEFACTORY_DETAILED_PRESS_V449_OWNED_PROMOTION_LANE_V001'
    $Summary.error = $_.Exception.Message
    throw
}
finally {
    $Summary.generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText(
        $SummaryPath,
        ($Summary | ConvertTo-Json -Depth 24) + "`n",
        $Utf8NoBom
    )
    Write-Output "LINE_BOSS_DETAILED_PRESS_V449_PROMOTION_SUMMARY=$SummaryPath"
}
