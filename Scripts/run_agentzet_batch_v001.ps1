# AgentZet batch runner (2026-08-31).
#
# Hand the local agent a QUEUE of jobs and walk away. The eval bridge
# already processes inbox prompts one at a time in sorted order (it must:
# generation and inference share one GPU), so a batch is simply N prompt
# files dropped at once plus this driver waiting on the done markers and
# summarising what happened.
#
# The editor must already be running with -AgentZetEvalBridge.
#
# Job file format: a directory of .txt files, one prompt per file. They
# run in FILENAME ORDER, so name them 01_..., 02_... to sequence work.
#
# Usage:
#   .\Scripts\run_agentzet_batch_v001.ps1 -JobsDir .\MyJobs
#   .\Scripts\run_agentzet_batch_v001.ps1 -JobsDir .\MyJobs -TimeoutMinutes 90
#
# Every job writes a transcript to Saved\AgentZetEval\outbox\<id>.jsonl and
# a completion marker <id>.done; this prints a PASS/FAIL table at the end
# and exits nonzero if any job failed, so it can gate a larger lane.

param(
    [Parameter(Mandatory = $true)]
    [string]$JobsDir,

    [int]$TimeoutMinutes = 120,

    [string]$Prefix = 'batch'
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$evalRoot = Join-Path $projectRoot 'Saved\AgentZetEval'
$inbox = Join-Path $evalRoot 'inbox'
$outbox = Join-Path $evalRoot 'outbox'
$ready = Join-Path $evalRoot 'bridge.ready'

if (-not (Test-Path -LiteralPath $JobsDir)) { throw "Jobs directory not found: $JobsDir" }
if (-not (Test-Path -LiteralPath $ready)) {
    throw "The eval bridge is not running. Start the editor with -AgentZetEvalBridge first (no bridge.ready at $ready)."
}

$jobFiles = @(Get-ChildItem -LiteralPath $JobsDir -Filter '*.txt' | Sort-Object Name)
if ($jobFiles.Count -eq 0) { throw "No .txt job files in $JobsDir" }

New-Item -ItemType Directory -Force $inbox | Out-Null
$stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$ids = @()

# Enqueue every job up front - the bridge serialises them itself.
$index = 0
foreach ($job in $jobFiles) {
    $index++
    $id = '{0}_{1}_{2:d3}_{3}' -f $Prefix, $stamp, $index, ($job.BaseName -replace '[^A-Za-z0-9_]', '_')
    $ids += $id
    $tmp = Join-Path $inbox "$id.prompt.txt.tmp"
    Copy-Item -LiteralPath $job.FullName -Destination $tmp -Force
    Move-Item -LiteralPath $tmp -Destination (Join-Path $inbox "$id.prompt.txt") -Force
    Write-Host "queued [$index/$($jobFiles.Count)] $id  <- $($job.Name)"
}

Write-Host ''
Write-Host "Waiting for $($ids.Count) job(s), timeout $TimeoutMinutes min..."

$deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$done = @{}
while ($done.Count -lt $ids.Count) {
    if ((Get-Date) -gt $deadline) {
        Write-Warning "Batch timed out with $($done.Count)/$($ids.Count) complete."
        break
    }
    foreach ($id in $ids) {
        if ($done.ContainsKey($id)) { continue }
        $marker = Join-Path $outbox "$id.done"
        if (Test-Path -LiteralPath $marker) {
            # The bridge writes the marker LAST, so it is safe to read now.
            $summary = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
            $done[$id] = $summary
            $state = if ($summary.reason -eq 'Task completed.') { 'OK  ' } else { 'FAIL' }
            Write-Host ("  [{0}] {1}  {2:n0}s, {3} msgs  ({4})" -f `
                $state, $id, $summary.seconds, $summary.messages, $summary.reason)
        }
    }
    Start-Sleep -Seconds 5
}

Write-Host ''
Write-Host '===== BATCH SUMMARY ====='
$failed = 0
foreach ($id in $ids) {
    if (-not $done.ContainsKey($id)) {
        Write-Host ("  NEVER FINISHED  {0}" -f $id)
        $failed++
        continue
    }
    $s = $done[$id]
    if ($s.reason -ne 'Task completed.') { $failed++ }
    Write-Host ("  {0,-14} {1}  ({2:n0}s)" -f $s.reason, $id, $s.seconds)
}
Write-Host ("Transcripts: {0}" -f $outbox)

# A completed job is not a CORRECT job: the transcripts still have to be
# read. This exit code only reports whether each job ran to completion.
if ($failed -gt 0) {
    Write-Host ("{0} of {1} job(s) did not complete." -f $failed, $ids.Count)
    exit 1
}
Write-Host ("All {0} job(s) completed. Read the transcripts to judge the WORK." -f $ids.Count)
exit 0
