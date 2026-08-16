param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z][A-Za-z0-9_-]{0,63}$')]
    [string]$Type,

    [string]$ArgsJson = '{}',

    [ValidatePattern('^[A-Za-z0-9_-]{1,64}$')]
    [string]$CommandId = "codex-$([guid]::NewGuid().ToString('N').Substring(0, 12))",

    [ValidateRange(1, 120)]
    [int]$WaitSeconds = 30,

    [string]$BridgeRoot
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($BridgeRoot)) {
    $BridgeRoot = Join-Path $projectRoot 'Saved\AutomationBridge'
}
$bridgeRoot = [System.IO.Path]::GetFullPath($BridgeRoot)
$sessionPath = Join-Path $bridgeRoot 'session.ready'
if (-not (Test-Path -LiteralPath $sessionPath)) {
    throw "Line Boss automation session not found. Launch a Development build with -LineBossAutomationBridge."
}

$session = Get-Content -LiteralPath $sessionPath -Raw | ConvertFrom-Json
if ($session.protocol -ne 'lineboss.automation' -or $session.version -ne 1 -or -not $session.enabled) {
    throw 'The current Line Boss automation session descriptor is not valid or enabled.'
}

try {
    $argsObject = $ArgsJson | ConvertFrom-Json
}
catch {
    throw "ArgsJson must be one JSON object: $($_.Exception.Message)"
}
if (($null -eq $argsObject) -or ($argsObject -is [System.Array]) -or ($argsObject -is [string]) -or ($argsObject -is [ValueType])) {
    throw 'ArgsJson must be a JSON object, not an array or scalar.'
}

$sequence = [int64]$session.next_sequence
$inbox = if ([System.IO.Path]::IsPathRooted([string]$session.inbox)) {
    [string]$session.inbox
} else {
    Join-Path $bridgeRoot "sessions\$($session.session_id)\inbox"
}
$outbox = if ([System.IO.Path]::IsPathRooted([string]$session.outbox)) {
    [string]$session.outbox
} else {
    Join-Path $bridgeRoot "sessions\$($session.session_id)\outbox"
}
$command = [ordered]@{
    protocol   = 'lineboss.automation'
    version    = 1
    kind       = 'command'
    session_id = [string]$session.session_id
    command_id = $CommandId
    sequence   = $sequence
    type       = $Type
    args       = $argsObject
}

$filename = '{0:D12}_{1}.ready' -f $sequence, $CommandId
$finalPath = Join-Path $inbox $filename
$temporaryPath = "$finalPath.tmp"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($temporaryPath, ($command | ConvertTo-Json -Depth 12 -Compress), $utf8NoBom)
if (Test-Path -LiteralPath $finalPath) {
    throw "Command destination already exists: $finalPath"
}
[System.IO.File]::Move($temporaryPath, $finalPath)

$replyName = '{0:D12}_{1}.reply.ready' -f $sequence, $CommandId
$replyPath = Join-Path $outbox $replyName
$deadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)
while (-not (Test-Path -LiteralPath $replyPath)) {
    if ([DateTime]::UtcNow -ge $deadline) {
        throw "Timed out waiting for Line Boss reply: $replyPath"
    }
    Start-Sleep -Milliseconds 100
}

Get-Content -LiteralPath $replyPath -Raw
