function Get-LBFileEvidenceWithBoundedReadRetry {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label,
        [int]$TimeoutMilliseconds = 15000
    )

    if ($TimeoutMilliseconds -lt 250 -or $TimeoutMilliseconds -gt 60000) {
        throw "$Label bounded read timeout is outside 250..60000 ms"
    }
    $Watch = [Diagnostics.Stopwatch]::StartNew()
    $Attempts = 0
    $LastLockError = $null
    while ($Watch.ElapsedMilliseconds -le $TimeoutMilliseconds) {
        $Attempts++
        $Stream = $null
        $Sha = $null
        try {
            # A successful read-open proves Start-Process has released its
            # redirected-log writer. Never hash a still-locked/finalizing file.
            $Stream = [IO.File]::Open(
                $Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
            $Sha = [Security.Cryptography.SHA256]::Create()
            $HashBytes = $Sha.ComputeHash($Stream)
            $Length = $Stream.Length
            $Stream.Position = 0
            $Reader = [IO.StreamReader]::new(
                $Stream, [Text.Encoding]::UTF8, $true, 4096, $true)
            try {
                $Text = $Reader.ReadToEnd()
            }
            finally {
                $Reader.Dispose()
            }
            $Hex = [BitConverter]::ToString($HashBytes).Replace('-', '')
            return [ordered]@{
                path = $Path
                bytes = [long]$Length
                sha256 = $Hex
                text = $Text
                read_open_attempts = $Attempts
                waited_milliseconds = [long]$Watch.ElapsedMilliseconds
            }
        }
        catch [IO.IOException] {
            $LastLockError = $_.Exception.Message
        }
        catch [UnauthorizedAccessException] {
            $LastLockError = $_.Exception.Message
        }
        finally {
            if ($null -ne $Sha) { $Sha.Dispose() }
            if ($null -ne $Stream) { $Stream.Dispose() }
        }
        if ($Watch.ElapsedMilliseconds -ge $TimeoutMilliseconds) { break }
        # Backoff happens only after an actual failed read-open; it is bounded
        # by the stopwatch deadline and capped to keep release detection prompt.
        $Backoff = [Math]::Min(25 * [Math]::Pow(2, [Math]::Min($Attempts - 1, 3)), 200)
        $Remaining = $TimeoutMilliseconds - $Watch.ElapsedMilliseconds
        Start-Sleep -Milliseconds ([int][Math]::Min($Backoff, $Remaining))
    }
    throw "$Label remained unreadable after $Attempts attempts/$($Watch.ElapsedMilliseconds) ms: $LastLockError"
}
