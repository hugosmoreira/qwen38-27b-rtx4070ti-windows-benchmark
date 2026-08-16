[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet(
        'configs/phase9-mtp-off-prose.json',
        'configs/phase9-mtp-on-prose.json',
        'configs/phase9-mtp-off-code.json',
        'configs/phase9-mtp-on-code.json'
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

$launchRecords = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'runtimes\llama.cpp\b10448\runs') -Filter 'launch.json' -File -Recurse | ForEach-Object {
    $record = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
    if ([int]$record.process_id -eq $ServerProcessId) { $record }
})
if ($launchRecords.Count -ne 1) {
    throw "Expected one launch record for server PID $ServerProcessId; found $($launchRecords.Count)."
}
$launch = $launchRecords[0]
$expectedMtp = $Config.Contains('-mtp-on-')
if ($expectedMtp) {
    if ([string]$launch.speculative_decoding.type -ne 'draft-mtp' -or
        [int]$launch.speculative_decoding.draft_n_max -ne 2 -or
        [int]$launch.speculative_decoding.draft_n_min -ne 0 -or
        [string]$launch.speculative_decoding.draft_cache_k -ne 'f16' -or
        [string]$launch.speculative_decoding.draft_cache_v -ne 'f16') {
        throw 'The selected server launch record does not match the frozen MTP-on controls.'
    }
}
elseif ([string]$launch.speculative_decoding.type -ne 'none') {
    throw 'The selected server launch record does not match the frozen MTP-off control.'
}

$env:PYTHONPATH = Join-Path $repositoryRoot 'src'
& $virtualPython -m qwen_bench run `
    --repository-root $repositoryRoot `
    --config $Config `
    --server-pid $ServerProcessId
if ($LASTEXITCODE -ne 0) { throw 'Phase 9 measurement did not complete successfully.' }
