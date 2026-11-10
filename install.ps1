#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()][string] $CodexHome,
    [switch] $DryRun,
    [switch] $Yes,
    [switch] $WithOrganization,
    [ValidateNotNullOrEmpty()][string] $Project,
    [switch] $Help
)
$ErrorActionPreference = 'Stop'
if ($Help) {
    Write-Output 'Usage: .\install.ps1 [-CodexHome PATH] [-DryRun] [-Yes] [-Help]'
    exit 0
}
if ($WithOrganization -or $PSBoundParameters.ContainsKey('Project')) {
    [Console]::Error.WriteLine('Organization extensions and project-mode installation are not supported.')
    exit 2
}
try {
    . (Join-Path $PSScriptRoot 'scripts/python-runtime.ps1')
    $arguments = @((Join-Path $PSScriptRoot 'scripts/package_cli.py'), 'install')
    if ($PSBoundParameters.ContainsKey('CodexHome')) {
        # PowerShell 5.1 misquotes a final backslash inside a spaced argument.
        # A final dot keeps directory/root meaning without a trailing backslash.
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
