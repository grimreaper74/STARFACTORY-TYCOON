param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$ProjectRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
)

$ErrorActionPreference = 'Stop'
$TaskId = '01a0040d-5094-73ba-8604-9efd4ca888ef'
$ExpectedAuthoritySha256 = 'BC15A0FDF954ABD27DB362AAED8A99DD0F5F22842F3DC62B8ACACC72E1498307'
$ExpectedInputSha256 = '1DBA1F25CE7E8486AF27183673BA23A23FE661E7ECB2A207B6CD7F85C70A1E5B'
$ExpectedSubmissionSha256 = '4DEB0AE8EE597A57F1C07FED9B4B4D58F596E1FD429ED81E75A6DA71CFF08DF2'
$ExpectedTaskSha256 = '6CE416B7B354386994E2593041F708C510A3CC2410BADD4EA597FF64F7715ECC'
$ExpectedFailureSha256 = 'D44888BC656BEDCA0166C3BDC24F83ABB800DF800D3AC2E7451254774AF5EA13'
$ExpectedExistingGlbSha256 = 'BE7C55ABC362DFBF42DA50BB3B2B79F63279F666838A7525D122550513951D3B'

$AuthorityPath = Join-Path $ProjectRoot 'SourceAssets\Candidate\Vehicles\Cairnwell2040\PanelPack_v001\Authority\ExteriorVehicle\Meshy_AI_Emerald_Horizon_0811171004_texture.blend'
$DerivativeRoot = Join-Path $ProjectRoot 'SourceAssets\Candidate\Vehicles\Cairnwell2040\FinishedVehicleRuntimeDerivative_v001'
$RunRoot = Join-Path $DerivativeRoot 'Validation\MeshyRemesh_v001'
$InputArchive = Join-Path $RunRoot 'Input\Cairnwell2040_EmeraldHorizon_BodyShell_RemeshInput_4560mm_v001.glb'
$ExportRoot = Join-Path $DerivativeRoot 'Exports\MeshyRemesh_v001'
$RenderRoot = Join-Path $DerivativeRoot 'Renders\MeshyRemesh_v001'
$SubmissionPath = Join-Path $RunRoot 'submission_receipt_v001.json'
$TaskPath = Join-Path $RunRoot 'task_latest_sanitized_v001.json'
$FailurePath = Join-Path $RunRoot 'failure_receipt_v001.json'
$RecoveryIntentPath = Join-Path $RunRoot 'collection_recovery_intent_v001.json'
$RecoveryReceiptPath = Join-Path $RunRoot 'collection_recovery_receipt_v001.json'
$SuccessPath = Join-Path $RunRoot 'success_receipt_v001.json'
$ExistingGlbPath = Join-Path $ExportRoot 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_v001.glb'

function Get-ExactHash([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Write-SanitizedJson([object]$Value, [string]$Path) {
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-GuardedRelativePath([string]$BasePath, [string]$FullPath) {
    $ResolvedBase = (Resolve-Path -LiteralPath $BasePath).Path.TrimEnd([char]92) + [char]92
    $ResolvedFull = (Resolve-Path -LiteralPath $FullPath).Path
    if (-not $ResolvedFull.StartsWith($ResolvedBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Output escaped the derivative root: $ResolvedFull"
    }
    return $ResolvedFull.Substring($ResolvedBase.Length).Replace([char]92, [char]47)
}

$RequiredEvidence = @(
    @{ Path = $SubmissionPath; Hash = $ExpectedSubmissionSha256 },
    @{ Path = $TaskPath; Hash = $ExpectedTaskSha256 },
    @{ Path = $FailurePath; Hash = $ExpectedFailureSha256 },
    @{ Path = $ExistingGlbPath; Hash = $ExpectedExistingGlbSha256 },
    @{ Path = $InputArchive; Hash = $ExpectedInputSha256 },
    @{ Path = $AuthorityPath; Hash = $ExpectedAuthoritySha256 }
)
foreach ($Record in $RequiredEvidence) {
    if (-not (Test-Path -LiteralPath $Record.Path -PathType Leaf)) {
        throw "Required incident evidence is missing: $($Record.Path)"
    }
    if ((Get-ExactHash $Record.Path) -ne $Record.Hash) {
        throw "Required incident evidence drifted: $($Record.Path)"
    }
}

$Submission = Get-Content -LiteralPath $SubmissionPath -Raw | ConvertFrom-Json
$TaskEvidence = Get-Content -LiteralPath $TaskPath -Raw | ConvertFrom-Json
if ([string]$Submission.task_id -ne $TaskId -or [string]$TaskEvidence.task_id -ne $TaskId) {
    throw 'Incident task id does not match the frozen recovery task id.'
}
if ([string]$TaskEvidence.status -ne 'SUCCEEDED' -or [int]$TaskEvidence.consumed_credits -ne 5) {
    throw 'Frozen task evidence is not a successful five-credit remesh.'
}

foreach ($GuardPath in @($RecoveryIntentPath, $RecoveryReceiptPath, $SuccessPath)) {
    if (Test-Path -LiteralPath $GuardPath) {
        throw "Refusing duplicate collection recovery; guard exists: $GuardPath"
    }
}
if (-not (Test-Path -LiteralPath $ApiKeyPath -PathType Leaf)) {
    throw "Meshy API key file is missing: $ApiKeyPath"
}

Write-SanitizedJson @{
    schema = 'lineboss.meshy-remesh-collection-recovery-intent.v1'
    status = 'READY__GET_EXISTING_SUCCEEDED_TASK_ONLY__NO_POST__NO_NEW_CREDITS'
    created_utc = (Get-Date).ToUniversalTime().ToString('o')
    task_id = $TaskId
    preserved_failure_receipt_sha256 = $ExpectedFailureSha256
    preserved_existing_glb_sha256 = $ExpectedExistingGlbSha256
    new_paid_submission_allowed = $false
} $RecoveryIntentPath

try {
    $Key = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($Key)) {
        throw 'Meshy API key file is empty.'
    }
    $Headers = @{ Authorization = "Bearer $Key" }
    $Task = Invoke-RestMethod -Uri ('https://api.meshy.ai/openapi/v1/remesh/' + $TaskId) -Headers $Headers -Method Get
    if ([string]$Task.id -ne $TaskId -or [string]$Task.status -ne 'SUCCEEDED' -or [int]$Task.consumed_credits -ne 5) {
        throw 'Live Meshy task no longer matches the frozen successful task.'
    }

    $Downloads = @(
        @{ Name = 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_v001.fbx'; Url = [string]$Task.model_urls.fbx; Kind = 'fbx'; Root = $ExportRoot },
        @{ Name = 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_v001.blend'; Url = [string]$Task.model_urls.blend; Kind = 'blend'; Root = $ExportRoot },
        @{ Name = 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_preview_v001.png'; Url = [string]$Task.thumbnail_url; Kind = 'preview'; Root = $RenderRoot },
        @{ Name = 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_alpha_v001.png'; Url = [string]$Task.alpha_thumbnail_url; Kind = 'alpha_thumbnail'; Root = $RenderRoot }
    )
    $OutputRecords = @(@{
        kind = 'glb'
        relative_path = Get-GuardedRelativePath $DerivativeRoot $ExistingGlbPath
        bytes = (Get-Item -LiteralPath $ExistingGlbPath).Length
        sha256 = $ExpectedExistingGlbSha256
        recovered_from_initial_collection = $true
    })
    foreach ($Download in $Downloads) {
        if ([string]::IsNullOrWhiteSpace($Download.Url)) {
            if ($Download.Kind -eq 'alpha_thumbnail') { continue }
            throw "Successful task omitted required URL: $($Download.Kind)"
        }
        $OutputPath = Join-Path $Download.Root $Download.Name
        if (Test-Path -LiteralPath $OutputPath) {
            throw "Refusing to overwrite an existing collection output: $OutputPath"
        }
        Invoke-WebRequest -Uri $Download.Url -OutFile $OutputPath
        $OutputRecords += @{
            kind = $Download.Kind
            relative_path = Get-GuardedRelativePath $DerivativeRoot $OutputPath
            bytes = (Get-Item -LiteralPath $OutputPath).Length
            sha256 = Get-ExactHash $OutputPath
            recovered_from_initial_collection = $false
        }
    }
    foreach ($RequiredKind in @('glb', 'fbx', 'blend', 'preview')) {
        if (-not ($OutputRecords | Where-Object kind -eq $RequiredKind)) {
            throw "Recovered collection omitted required output: $RequiredKind"
        }
    }

    $BalanceAfter = [int](Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers -Method Get).balance
    foreach ($Record in $RequiredEvidence) {
        if ((Get-ExactHash $Record.Path) -ne $Record.Hash) {
            throw "Incident evidence changed during collection recovery: $($Record.Path)"
        }
    }

    $Receipt = @{
        schema = 'lineboss.meshy-remesh-collection-recovery.v1'
        status = 'SUCCEEDED__SAME_PAID_TASK_COLLECTION_RECOVERED__NO_SECOND_SUBMISSION'
        finished_utc = (Get-Date).ToUniversalTime().ToString('o')
        task_id = $TaskId
        consumed_credits_reported = 5
        balance_after = $BalanceAfter
        post_requests = 0
        get_requests = 2
        preserved_failure_receipt_sha256 = $ExpectedFailureSha256
        preserved_submission_receipt_sha256 = $ExpectedSubmissionSha256
        preserved_task_receipt_sha256 = $ExpectedTaskSha256
        authority_sha256_unchanged = $ExpectedAuthoritySha256
        input_sha256_unchanged = $ExpectedInputSha256
        outputs = $OutputRecords
        signed_urls_persisted = $false
        bearer_token_persisted = $false
        local_geometry_review_pending = $true
        unreal_imported = $false
        promotion_authorized = $false
    }
    Write-SanitizedJson $Receipt $RecoveryReceiptPath
    $Receipt.schema = 'lineboss.meshy-remesh-success.v1'
    $Receipt.status = 'SUCCEEDED__ONE_PAID_REMESH__COLLECTION_RECOVERED_AFTER_LOCAL_PATH_GUARD_FAILURE__QA_PENDING'
    Write-SanitizedJson $Receipt $SuccessPath
    Write-Output "MESHY_REMESH_COLLECTION_RECOVERY_SUCCESS task=$TaskId balance_after=$BalanceAfter"
}
finally {
    $Key = $null
    $Headers = $null
    $Task = $null
}
