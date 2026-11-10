#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
try {
    $root = Split-Path -Parent $PSScriptRoot
    $files = @(Get-ChildItem -LiteralPath $root -Filter '*.ps1')
    $files += @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1')
    $files += @(Get-ChildItem -LiteralPath (Join-Path $root 'tests') -Filter '*.ps1')
    foreach ($file in $files) {
        $tokens = $null
        $parseErrors = $null
        [System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref] $tokens, [ref] $parseErrors) | Out-Null
        if ($parseErrors.Count -gt 0) { throw "PowerShell syntax error in $($file.FullName): $parseErrors" }
    }
    . (Join-Path $PSScriptRoot 'python-runtime.ps1')
    Invoke-SdlcPython -Arguments @((Join-Path $PSScriptRoot 'package_cli.py'), 'validate')
    exit $script:SdlcExitCode
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
