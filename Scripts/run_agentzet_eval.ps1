# AgentZet eval driver (2026-08-31).
# Feeds one prompt to a running (or freshly launched) editor that has the
# AgentZet eval bridge active, waits for completion, and prints the
# transcript. See Plugins/AgentZet/Source/AgentZetUI/Private/AgentZetEvalBridge.h
# for the file protocol.
#
# Usage:
#   .\Scripts\run_agentzet_eval.ps1 -EvalId step4-inspect -PromptFile p.txt
#   .\Scripts\run_agentzet_eval.ps1 -EvalId quick -Prompt "list Source dirs" -TimeoutSec 600
# The editor is NOT launched by this script (launch it once, run many
# evals against it):
#   UnrealEditor.exe <project.uproject> -AgentZetEvalBridge -nosplash

param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_-]{1,64}$')]
    [string]$EvalId,

    [string]$Prompt,
    [string]$PromptFile,

    [ValidateRange(30, 3600)]
    [int]$TimeoutSec = 900
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$evalRoot = Join-Path $projectRoot 'Saved\AgentZetEval'
$readyPath = Join-Path $evalRoot 'bridge.ready'
$inbox = Join-Path $evalRoot 'inbox'
$outbox = Join-Path $evalRoot 'outbox'

if (-not (Test-Path -LiteralPath $readyPath)) {
    throw "No bridge.ready at $readyPath - launch the editor with -AgentZetEvalBridge first."
}

if ([string]::IsNullOrWhiteSpace($Prompt)) {
    if ([string]::IsNullOrWhiteSpace($PromptFile)) {
        throw 'Provide -Prompt or -PromptFile.'
    }
    $Prompt = Get-Content -LiteralPath $PromptFile -Raw
}

$donePath = Join-Path $outbox "$EvalId.done"
$transcriptPath = Join-Path $outbox "$EvalId.jsonl"
if (Test-Path -LiteralPath $donePath) { Remove-Item -LiteralPath $donePath -Force }
if (Test-Path -LiteralPath $transcriptPath) { Remove-Item -LiteralPath $transcriptPath -Force }

# Atomic drop: write .tmp then rename, so the bridge never reads a
# half-written prompt.
$finalPrompt = Join-Path $inbox "$EvalId.prompt.txt"
$tmpPrompt = "$finalPrompt.tmp"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($tmpPrompt, $Prompt, $utf8NoBom)
if (Test-Path -LiteralPath $finalPrompt) { Remove-Item -LiteralPath $finalPrompt -Force }
[System.IO.File]::Move($tmpPrompt, $finalPrompt)

Write-Host "Eval '$EvalId' submitted; waiting up to $TimeoutSec s..."
$deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
while (-not (Test-Path -LiteralPath $donePath)) {
    if ([DateTime]::UtcNow -ge $deadline) {
        Write-Host '--- TIMEOUT. Transcript so far: ---'
        if (Test-Path -LiteralPath $transcriptPath) {
            Get-Content -LiteralPath $transcriptPath
        }
        throw "Eval '$EvalId' did not complete within $TimeoutSec s."
    }
    Start-Sleep -Milliseconds 500
}

Write-Host '--- DONE ---'
Get-Content -LiteralPath $donePath
Write-Host '--- TRANSCRIPT ---'
Get-Content -LiteralPath $transcriptPath
