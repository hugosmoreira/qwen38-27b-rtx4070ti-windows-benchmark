[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet(
        'configs/phase7-iq2-context-4k.json',
        'configs/phase7-iq2-context-8k.json',
        'configs/phase7-iq2-context-16k.json'
    )]
    [string]$Config,
    [ValidateRange(0, 2147483647)][int]$ServerProcessId = 0
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$virtualPython = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$expectedServerPath = Join-Path $repositoryRoot 'runtimes\llama.cpp\b10448\bin\llama-server.exe'
if (-not (Test-Path -LiteralPath $virtualPython -PathType Leaf)) {
    throw 'The isolated .venv is missing. Run .\scripts\setup_python.ps1 first.'
}
if (-not (Test-Path -LiteralPath $expectedServerPath -PathType Leaf)) {
    throw 'The pinned llama.cpp b10448 server executable is missing.'
}

if ($ServerProcessId -eq 0) {
    $candidates = @(Get-Process -Name 'llama-server' -ErrorAction SilentlyContinue | Where-Object {
        $null -ne $_.Path -and $_.Path.Equals($expectedServerPath, [System.StringComparison]::OrdinalIgnoreCase)
    })
    if ($candidates.Count -ne 1) {
        throw "Expected exactly one pinned llama-server process; found $($candidates.Count)."
    }
    $ServerProcessId = $candidates[0].Id
}

$selected = Get-Process -Id $ServerProcessId -ErrorAction Stop
if (-not $selected.Path.Equals($expectedServerPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Process $ServerProcessId is not the pinned llama-server executable."
}

$env:PYTHONPATH = Join-Path $repositoryRoot 'src'
& $virtualPython -m qwen_bench run `
    --repository-root $repositoryRoot `
    --config $Config `
    --server-pid $ServerProcessId
if ($LASTEXITCODE -ne 0) { throw 'Phase 7 measurement did not complete successfully.' }
