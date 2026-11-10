# Shared by native PowerShell entry points. No external modules are required.
function Get-SdlcPython {
    $probe = 'import sys; assert sys.version_info >= (3,11); import tomllib'
    foreach ($name in @('py', 'python', 'python3')) {
        $commands = @(Get-Command $name -All -CommandType Application -ErrorAction SilentlyContinue)
        foreach ($command in $commands) {
            # Batch shims reparse metacharacters through cmd.exe. Only native
            # executables can receive arbitrary target paths without that layer.
            if ([IO.Path]::GetExtension($command.Source) -ine '.exe' -or
                $command.Source -match '[\\/]WindowsApps[\\/]') {
                continue
            }
            $prefix = @()
            if ($name -eq 'py') { $prefix = @('-3') }
            try {
                & $command.Source @prefix -B -c $probe 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    return @{ Executable = $command.Source; Prefix = $prefix }
                }
            } catch {
                # A broken launcher or old interpreter must not hide a later candidate.
            }
        }
    }
    throw 'Python 3.11 or newer is required. Put a working native py.exe or python.exe on PATH; batch shims and Windows Store aliases are not supported.'
}

function Invoke-SdlcPython {
    param([Parameter(Mandatory = $true)][string[]] $Arguments)
    $runtime = Get-SdlcPython
    $prefix = $runtime.Prefix
    $previousEncoding = [Console]::OutputEncoding
    try {
        # Align Python output and PowerShell's native decoder, including redirected
        # Unicode paths. Restore the caller's console setting on every exit path.
        [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
        & $runtime.Executable @prefix -B -X utf8 @Arguments
        $script:SdlcExitCode = $LASTEXITCODE
    } finally {
        [Console]::OutputEncoding = $previousEncoding
    }
}
