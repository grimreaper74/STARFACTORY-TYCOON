[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Validator = 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\revalidate_assembly_line_native_kit_incident_v003.py'
$ExpectedPath = 'C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Scripts/revalidate_assembly_line_native_kit_incident_v003.py'
$ExpectedArgument = '-ExecutePythonScript="C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Scripts/revalidate_assembly_line_native_kit_incident_v003.py"'
$Normalized = [IO.Path]::GetFullPath($Validator).Replace('\','/')
$Argument = '-ExecutePythonScript="{0}"' -f $Normalized
$ControlCharacters = [char[]](0..31)

if ($Normalized -cne $ExpectedPath) { throw "Normalized validator path drift: $Normalized" }
if ($Argument -cne $ExpectedArgument) { throw "ExecutePythonScript argument drift: $Argument" }
if ($Normalized.Contains('\') -or $Normalized.IndexOfAny($ControlCharacters) -ge 0) {
    throw 'Normalized validator path contains a backslash or control character'
}
if ($Argument.Contains('\') -or $Argument.IndexOfAny($ControlCharacters) -ge 0) {
    throw 'ExecutePythonScript argument contains a backslash or control character'
}
if ($Argument.Contains("Scripts`revalidate")) {
    throw 'Historical carriage-return regression reproduced'
}

Write-Output 'PASS__EXECUTE_PYTHON_PATH_FORWARD_SLASH_NO_CONTROL_ESCAPE_V003'
