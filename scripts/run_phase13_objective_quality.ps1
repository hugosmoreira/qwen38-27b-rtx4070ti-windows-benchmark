[CmdletBinding()]
param(
    [ValidateSet('configs/phase13-iq4-xs-quality-4k-q8.json')]
    [string]$Config = 'configs/phase13-iq4-xs-quality-4k-q8.json',
    [ValidateRange(0, 2147483647)][int]$ServerProcessId = 0
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$virtualPython = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$expectedServerPath = Join-Path $repositoryRoot 'runtimes\llama.cpp\b10448\bin\llama-server.exe'
if (-not (Test-Path -LiteralPath $virtualPython -PathType Leaf)) { throw 'The isolated .venv is missing.' }
if (-not (Test-Path -LiteralPath $expectedServerPath -PathType Leaf)) { throw 'The pinned server executable is missing.' }

if ($ServerProcessId -eq 0) {
    $candidates = @(Get-Process -Name 'llama-server' -ErrorAction SilentlyContinue | Where-Object {
        $null -ne $_.Path -and $_.Path.Equals($expectedServerPath, [System.StringComparison]::OrdinalIgnoreCase)
    })
    if ($candidates.Count -ne 1) { throw "Expected exactly one pinned server; found $($candidates.Count)." }
    $ServerProcessId = $candidates[0].Id
}
$selected = Get-Process -Id $ServerProcessId -ErrorAction Stop
if ($null -eq $selected.Path -or -not $selected.Path.Equals($expectedServerPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Process $ServerProcessId is not the pinned server."
}

$launchRecords = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'runtimes\llama.cpp\b10448\runs') -Filter 'launch.json' -File -Recurse | ForEach-Object {
    $record = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
    if ([int]$record.process_id -eq $ServerProcessId) { $record }
})
if ($launchRecords.Count -ne 1) { throw "Expected one launch record for PID $ServerProcessId; found $($launchRecords.Count)." }
$launch = $launchRecords[0]
if ([string]$launch.model_manifest -ne 'environment/phase13-iq4-xs-download-manifest.json' -or
    [string]$launch.model_alias -ne 'Qwen3.8-27B-IQ4_XS' -or
    [int]$launch.controlled_configuration.context_size -ne 4096 -or
    [int]$launch.controlled_configuration.gpu_layers_requested -ne 45 -or
    [string]$launch.controlled_configuration.kv_cache_k_type -ne 'q8_0' -or
    [string]$launch.controlled_configuration.kv_cache_v_type -ne 'q8_0' -or
    [string]$launch.speculative_decoding.type -ne 'none' -or
    -not [bool]$launch.model_hash_validated) {
    throw 'The server launch does not match the frozen Phase 13 objective-quality configuration.'
}
if (@(Select-String -LiteralPath ([string]$launch.log_files.server) -Pattern 'offloaded\s+45/66\s+layers to GPU').Count -lt 1) {
    throw 'The startup log does not prove 45/66 GPU layers.'
}

$env:PYTHONPATH = Join-Path $repositoryRoot 'src'
& $virtualPython -m qwen_bench quality-run --repository-root $repositoryRoot --config $Config --server-pid $ServerProcessId
if ($LASTEXITCODE -ne 0) { throw 'Phase 13 objective quality evaluation did not complete every request.' }
