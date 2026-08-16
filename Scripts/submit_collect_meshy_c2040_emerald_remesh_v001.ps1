param(
    [string]$ApiKeyPath = 'C:\Users\greg_\OneDrive\Documents\line boss\linebosskey.txt',
    [string]$InputGlbPath = 'C:\Users\greg_\OneDrive\Documents\ChatGPT\line boss\Cairnwell2040_EmeraldDerivative_Candidate_v001\Cairnwell2040_EmeraldHorizon_BodyShell_RemeshInput_4560mm_v001.glb',
    [string]$ProjectRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8',
    [int]$PollSeconds = 10,
    [int]$TimeoutMinutes = 45
)

$ErrorActionPreference = 'Stop'
$ExpectedInputSha256 = '1DBA1F25CE7E8486AF27183673BA23A23FE661E7ECB2A207B6CD7F85C70A1E5B'
$ExpectedInputBytes = 49737420
$ExpectedAuthoritySha256 = 'BC15A0FDF954ABD27DB362AAED8A99DD0F5F22842F3DC62B8ACACC72E1498307'
$AuthorityPath = Join-Path $ProjectRoot 'SourceAssets\Candidate\Vehicles\Cairnwell2040\PanelPack_v001\Authority\ExteriorVehicle\Meshy_AI_Emerald_Horizon_0811171004_texture.blend'
$DerivativeRoot = Join-Path $ProjectRoot 'SourceAssets\Candidate\Vehicles\Cairnwell2040\FinishedVehicleRuntimeDerivative_v001'
$RunRoot = Join-Path $DerivativeRoot 'Validation\MeshyRemesh_v001'
$InputArchive = Join-Path $RunRoot 'Input\Cairnwell2040_EmeraldHorizon_BodyShell_RemeshInput_4560mm_v001.glb'
$ExportRoot = Join-Path $DerivativeRoot 'Exports\MeshyRemesh_v001'
$RenderRoot = Join-Path $DerivativeRoot 'Renders\MeshyRemesh_v001'
$IntentPath = Join-Path $RunRoot 'paid_submission_intent_v001.json'
$SubmissionPath = Join-Path $RunRoot 'submission_receipt_v001.json'
$SuccessPath = Join-Path $RunRoot 'success_receipt_v001.json'
$FailurePath = Join-Path $RunRoot 'failure_receipt_v001.json'

function Get-ExactHash([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-GuardedRelativePath([string]$BasePath, [string]$FullPath) {
    $ResolvedBase = (Resolve-Path -LiteralPath $BasePath).Path.TrimEnd('\\') + '\\'
    $ResolvedFull = (Resolve-Path -LiteralPath $FullPath).Path
    if (-not $ResolvedFull.StartsWith($ResolvedBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Output escaped the derivative root: $ResolvedFull"
    }
    return $ResolvedFull.Substring($ResolvedBase.Length).Replace('\\', '/')
}

function Write-SanitizedJson([object]$Value, [string]$Path) {
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding UTF8
}

if (-not (Test-Path -LiteralPath $InputGlbPath -PathType Leaf)) {
    throw "Meshy body-shell input is missing: $InputGlbPath"
}
if (-not (Test-Path -LiteralPath $AuthorityPath -PathType Leaf)) {
    throw "Emerald Horizon authority is missing: $AuthorityPath"
}
if ((Get-Item -LiteralPath $InputGlbPath).Length -ne $ExpectedInputBytes) {
    throw 'Meshy body-shell input byte size drifted.'
}
if ((Get-ExactHash $InputGlbPath) -ne $ExpectedInputSha256) {
    throw 'Meshy body-shell input SHA-256 drifted.'
}
if ((Get-ExactHash $AuthorityPath) -ne $ExpectedAuthoritySha256) {
    throw 'Immutable Emerald Horizon authority SHA-256 drifted.'
}
if (-not (Test-Path -LiteralPath $ApiKeyPath -PathType Leaf)) {
    throw "Meshy API key file is missing: $ApiKeyPath"
}

foreach ($GuardPath in @($IntentPath, $SubmissionPath, $SuccessPath, $FailurePath)) {
    if (Test-Path -LiteralPath $GuardPath) {
        throw "Refusing a duplicate paid Meshy remesh attempt; guard exists: $GuardPath"
    }
}
if ((Test-Path -LiteralPath $ExportRoot) -and (Get-ChildItem -LiteralPath $ExportRoot -File -ErrorAction SilentlyContinue)) {
    throw "Refusing to overwrite existing remesh exports: $ExportRoot"
}
if ((Test-Path -LiteralPath $RenderRoot) -and (Get-ChildItem -LiteralPath $RenderRoot -File -ErrorAction SilentlyContinue)) {
    throw "Refusing to overwrite existing remesh renders: $RenderRoot"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $InputArchive), $ExportRoot, $RenderRoot | Out-Null
Copy-Item -LiteralPath $InputGlbPath -Destination $InputArchive
if ((Get-ExactHash $InputArchive) -ne $ExpectedInputSha256) {
    throw 'Archived API input does not match the prepared body-shell input.'
}

$Key = (Get-Content -LiteralPath $ApiKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($Key)) {
    throw 'Meshy API key file is empty.'
}
$Headers = @{ Authorization = "Bearer $Key" }
$BalanceBefore = [int](Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
if ($BalanceBefore -lt 5) {
    throw "Need at least 5 Meshy credits for one remesh; balance is $BalanceBefore."
}

Write-SanitizedJson @{
    schema = 'lineboss.meshy-paid-submission-intent.v1'
    asset = 'Cairnwell2040_EmeraldHorizon_BodyShell'
    endpoint = '/openapi/v1/remesh'
    submitted = $false
    created_utc = (Get-Date).ToUniversalTime().ToString('o')
    expected_maximum_paid_attempts = 1
    expected_credits = 5
    balance_before = $BalanceBefore
    authority_sha256 = $ExpectedAuthoritySha256
    input_sha256 = $ExpectedInputSha256
    input_bytes = $ExpectedInputBytes
    input_contains = 'largest connected body-shell island only; eight wheel/rim islands excluded'
    target = @{
        topology = 'triangle'
        target_polycount = 50000
        target_formats = @('glb', 'fbx', 'blend')
        alpha_thumbnail = $true
        resizing = 'omitted'
    }
} $IntentPath

try {
    $InputBytes = [System.IO.File]::ReadAllBytes($InputArchive)
    $InputDataUri = 'data:application/octet-stream;base64,' + [Convert]::ToBase64String($InputBytes)
    $Payload = @{
        model_url = $InputDataUri
        target_formats = @('glb', 'fbx', 'blend')
        topology = 'triangle'
        target_polycount = 50000
        alpha_thumbnail = $true
    } | ConvertTo-Json -Depth 5 -Compress
    $InputBytes = $null
    $InputDataUri = $null

    $Created = Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/remesh' -Headers $Headers -Method Post -ContentType 'application/json' -Body $Payload
    $Payload = $null
    $TaskId = [string]$Created.result
    if ([string]::IsNullOrWhiteSpace($TaskId)) {
        throw 'Meshy returned no remesh task id.'
    }

    Write-SanitizedJson @{
        schema = 'lineboss.meshy-remesh-submission.v1'
        asset = 'Cairnwell2040_EmeraldHorizon_BodyShell'
        endpoint = '/openapi/v1/remesh'
        task_id = $TaskId
        submitted_utc = (Get-Date).ToUniversalTime().ToString('o')
        balance_before = $BalanceBefore
        authority_sha256 = $ExpectedAuthoritySha256
        input_sha256 = $ExpectedInputSha256
        input_bytes = $ExpectedInputBytes
        target_formats = @('glb', 'fbx', 'blend')
        topology = 'triangle'
        target_polycount = 50000
        alpha_thumbnail = $true
        auto_size = $false
        resize_requested = $false
    } $SubmissionPath

    $Deadline = (Get-Date).AddMinutes($TimeoutMinutes)
    $Task = $null
    do {
        $Task = Invoke-RestMethod -Uri ('https://api.meshy.ai/openapi/v1/remesh/' + $TaskId) -Headers $Headers
        Write-SanitizedJson @{
            task_id = $TaskId
            status = [string]$Task.status
            progress = [int]$Task.progress
            consumed_credits = $Task.consumed_credits
            preceding_tasks = $Task.preceding_tasks
            error_message = [string]$Task.task_error.message
            observed_utc = (Get-Date).ToUniversalTime().ToString('o')
        } (Join-Path $RunRoot 'task_latest_sanitized_v001.json')
        Write-Output "MESHY REMESH status=$($Task.status) progress=$($Task.progress)"
        if ($Task.status -in @('SUCCEEDED', 'FAILED', 'CANCELED')) { break }
        Start-Sleep -Seconds $PollSeconds
    } while ((Get-Date) -lt $Deadline)

    if (-not $Task -or $Task.status -ne 'SUCCEEDED') {
        throw "Meshy remesh did not succeed; final status=$($Task.status), error=$($Task.task_error.message)"
    }

    $Downloads = @(
        @{ Name = 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_v001.glb'; Url = [string]$Task.model_urls.glb; Kind = 'glb'; Root = $ExportRoot },
        @{ Name = 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_v001.fbx'; Url = [string]$Task.model_urls.fbx; Kind = 'fbx'; Root = $ExportRoot },
        @{ Name = 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_v001.blend'; Url = [string]$Task.model_urls.blend; Kind = 'blend'; Root = $ExportRoot },
        @{ Name = 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_preview_v001.png'; Url = [string]$Task.thumbnail_url; Kind = 'preview'; Root = $RenderRoot },
        @{ Name = 'Cairnwell2040_EmeraldHorizon_BodyShell_MeshyRemesh50k_alpha_v001.png'; Url = [string]$Task.alpha_thumbnail_url; Kind = 'alpha_thumbnail'; Root = $RenderRoot }
    )
    $OutputRecords = @()
    foreach ($Download in $Downloads) {
        if ([string]::IsNullOrWhiteSpace($Download.Url)) { continue }
        $OutputPath = Join-Path $Download.Root $Download.Name
        Invoke-WebRequest -Uri $Download.Url -OutFile $OutputPath
        $OutputRecords += @{
            kind = $Download.Kind
            relative_path = Get-GuardedRelativePath $DerivativeRoot $OutputPath
            bytes = (Get-Item -LiteralPath $OutputPath).Length
            sha256 = Get-ExactHash $OutputPath
        }
    }

    foreach ($RequiredKind in @('glb', 'fbx', 'blend', 'preview')) {
        if (-not ($OutputRecords | Where-Object kind -eq $RequiredKind)) {
            throw "Meshy success response omitted required output: $RequiredKind"
        }
    }

    $BalanceAfter = [int](Invoke-RestMethod -Uri 'https://api.meshy.ai/openapi/v1/balance' -Headers $Headers).balance
    if ((Get-ExactHash $AuthorityPath) -ne $ExpectedAuthoritySha256) {
        throw 'Immutable Emerald Horizon authority changed during the Meshy lane.'
    }
    if ((Get-ExactHash $InputArchive) -ne $ExpectedInputSha256) {
        throw 'Archived body-shell input changed during the Meshy lane.'
    }

    Write-SanitizedJson @{
        schema = 'lineboss.meshy-remesh-success.v1'
        status = 'SUCCEEDED__ONE_PAID_REMESH__LOCAL_VISUAL_AND_GEOMETRY_REVIEW_PENDING'
        asset = 'Cairnwell2040_EmeraldHorizon_BodyShell'
        task_id = $TaskId
        finished_utc = (Get-Date).ToUniversalTime().ToString('o')
        balance_before = $BalanceBefore
        balance_after = $BalanceAfter
        observed_balance_delta = $BalanceBefore - $BalanceAfter
        consumed_credits_reported = $Task.consumed_credits
        authority_sha256_unchanged = $ExpectedAuthoritySha256
        input_sha256_unchanged = $ExpectedInputSha256
        target_polycount = 50000
        topology = 'triangle'
        resize_requested = $false
        wheel_rim_islands_submitted = 0
        outputs = $OutputRecords
        signed_urls_persisted = $false
        bearer_token_persisted = $false
        unreal_imported = $false
        promotion_authorized = $false
    } $SuccessPath

    Write-Output "MESHY_REMESH_SUCCESS task=$TaskId credits=$($BalanceBefore-$BalanceAfter) balance_after=$BalanceAfter"
}
catch {
    Write-SanitizedJson @{
        schema = 'lineboss.meshy-remesh-failure.v1'
        status = 'FAILED_CLOSED__NO_AUTOMATIC_RETRY'
        failed_utc = (Get-Date).ToUniversalTime().ToString('o')
        message = $_.Exception.Message
        authority_sha256_expected = $ExpectedAuthoritySha256
        input_sha256_expected = $ExpectedInputSha256
        paid_intent_exists = $true
        automatic_retry_allowed = $false
    } $FailurePath
    throw
}
finally {
    $Key = $null
    $Headers = $null
    $Payload = $null
    $InputBytes = $null
    $InputDataUri = $null
}
