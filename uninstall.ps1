#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()][string] $CodexHome,
    [switch] $DryRun,
    [switch] $Yes,
    [switch] $Help
)
$ErrorActionPreference = 'Stop'
if ($Help) {
    Write-Output 'Usage: .\uninstall.ps1 [-CodexHome PATH] [-DryRun] [-Yes] [-Help]'
    exit 0
}
try {
    . (Join-Path $PSScriptRoot 'scripts/python-runtime.ps1')
    $arguments = @((Join-Path $PSScriptRoot 'scripts/package_cli.py'), 'uninstall')
    if ($PSBoundParameters.ContainsKey('CodexHome')) {
        if ($CodexHome.EndsWith('\')) { $CodexHome += '.' }
        $arguments += @('--codex-home', $CodexHome)
    }
    if ($DryRun) { $arguments += '--dry-run' }
    if ($Yes) { $arguments += '--yes' }
    Invoke-SdlcPython -Arguments $arguments
    exit $script:SdlcExitCode
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
