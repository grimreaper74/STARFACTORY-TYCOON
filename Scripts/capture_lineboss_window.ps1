param([Parameter(Mandatory=$true)][string]$OutputPath)
Add-Type -AssemblyName System.Drawing
$native = @'
using System;
using System.Runtime.InteropServices;
public class LineBossCaptureNative {
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd,out RECT r);
 public struct RECT { public int Left,Top,Right,Bottom; }
}
'@
Add-Type $native -ErrorAction SilentlyContinue
$process = Get-Process LineBossCarFactory -ErrorAction Stop |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
[LineBossCaptureNative]::SetForegroundWindow($process.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 250
$rect = New-Object LineBossCaptureNative+RECT
[LineBossCaptureNative]::GetWindowRect($process.MainWindowHandle,[ref]$rect) | Out-Null
$bitmap = New-Object System.Drawing.Bitmap ($rect.Right-$rect.Left),($rect.Bottom-$rect.Top)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($rect.Left,$rect.Top,0,0,$bitmap.Size)
$bitmap.Save($OutputPath,[System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
Write-Output $OutputPath
