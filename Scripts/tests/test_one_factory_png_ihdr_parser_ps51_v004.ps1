[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$CaptureRoot = Join-Path $Root 'Saved\ValidationScreenshots\OneFactory\v001\ActualPlayerPIE\20260815T024250499Z'

function Get-PngDimensions([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "PNG regression input is missing: $Path"
    }
    $Stream = [IO.File]::OpenRead($Path)
    try {
        $Header = New-Object byte[] 24
        if ($Stream.Read($Header, 0, 24) -ne 24) {
            throw "PNG regression input has a truncated header: $Path"
        }
    }
    finally {
        $Stream.Dispose()
    }
    $Signature = @(137, 80, 78, 71, 13, 10, 26, 10)
    for ($Index = 0; $Index -lt 8; $Index++) {
        if ([int]$Header[$Index] -ne [int]$Signature[$Index]) {
            throw "PNG regression signature drift: $Path"
        }
    }
    if ([Text.Encoding]::ASCII.GetString($Header, 12, 4) -cne 'IHDR') {
        throw "PNG regression IHDR drift: $Path"
    }

    # Each cast and shift is explicitly parenthesized. Windows PowerShell 5.1
    # otherwise binds array indexing/shift expressions in a way that reduced
    # 00 00 07 80 to 128 and 00 00 04 38 to 56 in the rejected v003 parser.
    $Width = (
        (([uint32]$Header[16]) -shl 24) -bor
        (([uint32]$Header[17]) -shl 16) -bor
        (([uint32]$Header[18]) -shl 8) -bor
        ([uint32]$Header[19])
    )
    $Height = (
        (([uint32]$Header[20]) -shl 24) -bor
        (([uint32]$Header[21]) -shl 16) -bor
        (([uint32]$Header[22]) -shl 8) -bor
        ([uint32]$Header[23])
    )
    return [ordered]@{ width = [uint32]$Width; height = [uint32]$Height }
}

$Scene = Get-PngDimensions (Join-Path $CaptureRoot '01_empty_factory_management_overview.png')
$UI = Get-PngDimensions (Join-Path $CaptureRoot '04_populated_press_starter_with_umg.png')
if ([uint32]$Scene.width -ne 1920 -or [uint32]$Scene.height -ne 1080) {
    throw "PS5.1 1920x1080 PNG regression failed: $($Scene.width)x$($Scene.height)"
}
if ([uint32]$UI.width -ne 1300 -or [uint32]$UI.height -ne 740) {
    throw "PS5.1 1300x740 PNG regression failed: $($UI.width)x$($UI.height)"
}

Write-Output 'PASS__WINDOWS_POWERSHELL_5_1_PNG_IHDR_1920X1080_AND_1300X740_V004'
