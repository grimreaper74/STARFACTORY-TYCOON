param(
    [string]$BatchRoot = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\Meshy_S03_ComponentBatch_v624',
    [switch]$Recover
)

$ErrorActionPreference = 'Stop'

function Get-GlbState {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ Exists=$false; Valid=$false; ActualLength=0; DeclaredLength=0; Reason='missing' }
    }

    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $header = New-Object byte[] 12
        $read = $stream.Read($header, 0, 12)
        if ($read -ne 12) {
            return [pscustomobject]@{ Exists=$true; Valid=$false; ActualLength=$stream.Length; DeclaredLength=0; Reason='short_header' }
        }
        $magic = [System.Text.Encoding]::ASCII.GetString($header, 0, 4)
        $version = [BitConverter]::ToUInt32($header, 4)
        $declared = [BitConverter]::ToUInt32($header, 8)
        $valid = ($magic -eq 'glTF' -and $version -eq 2 -and $declared -eq $stream.Length)
        $reason = if ($magic -ne 'glTF') { 'bad_magic' } elseif ($version -ne 2) { 'unsupported_version' } elseif ($declared -ne $stream.Length) { 'length_mismatch' } else { 'ok' }
        return [pscustomobject]@{ Exists=$true; Valid=$valid; ActualLength=$stream.Length; DeclaredLength=$declared; Reason=$reason }
    }
    finally {
        $stream.Dispose()
    }
}

$rows = @()
$jobDirs = Get-ChildItem -LiteralPath $BatchRoot -Directory | Where-Object { $_.Name -like 'Asset*' } | Sort-Object Name
foreach ($jobDir in $jobDirs) {
    $modelPath = Join-Path $jobDir.FullName 'model.glb'
    $before = Get-GlbState -Path $modelPath
    $recovered = $false
    $retainedPath = $null

    if ($Recover -and -not $before.Valid) {
        $metadataPath = Join-Path $jobDir.FullName 'task_complete.json'
        if (-not (Test-Path -LiteralPath $metadataPath)) { throw "Missing task metadata: $metadataPath" }
        $task = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
        $url = $task.model_urls.glb
        if ([string]::IsNullOrWhiteSpace($url)) { throw "No GLB recovery URL in: $metadataPath" }

        $candidatePath = Join-Path $jobDir.FullName 'model.recovery-download.glb'
        Invoke-WebRequest -Uri $url -OutFile $candidatePath
        $candidate = Get-GlbState -Path $candidatePath
        if (-not $candidate.Valid) {
            Remove-Item -LiteralPath $candidatePath -Force
            throw "Recovery download failed structural validation for $($jobDir.Name): $($candidate.Reason)"
        }

        if (Test-Path -LiteralPath $modelPath) {
            $retainedPath = Join-Path $jobDir.FullName 'model.truncated-original.glb'
            if (Test-Path -LiteralPath $retainedPath) {
                $suffix = Get-Date -Format 'yyyyMMdd-HHmmss'
                $retainedPath = Join-Path $jobDir.FullName "model.truncated-original-$suffix.glb"
            }
            Move-Item -LiteralPath $modelPath -Destination $retainedPath
        }
        Move-Item -LiteralPath $candidatePath -Destination $modelPath
        $recovered = $true
    }

    $after = Get-GlbState -Path $modelPath
    $sha256 = if ($after.Valid) { (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash } else { $null }
    $rows += [pscustomobject]@{
        Asset = $jobDir.Name
        ValidBefore = $before.Valid
        ValidAfter = $after.Valid
        Recovered = $recovered
        ActualLength = $after.ActualLength
        DeclaredLength = $after.DeclaredLength
        Reason = $after.Reason
        Sha256 = $sha256
        RetainedOriginal = $retainedPath
    }
}

$reportPath = Join-Path $BatchRoot 'glb_integrity_report_v626.json'
$rows | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $reportPath -Encoding utf8
$rows | Format-Table Asset,ValidBefore,ValidAfter,Recovered,ActualLength,DeclaredLength,Reason -AutoSize
Write-Output "REPORT $reportPath"

if (($rows | Where-Object { -not $_.ValidAfter }).Count -gt 0) { exit 2 }
