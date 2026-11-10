#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
try {
    . (Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts/python-runtime.ps1')
    Invoke-SdlcPython -Arguments @('-m', 'unittest', 'discover', '-s', $PSScriptRoot, '-p', 'test_*.py')
    exit $script:SdlcExitCode
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
