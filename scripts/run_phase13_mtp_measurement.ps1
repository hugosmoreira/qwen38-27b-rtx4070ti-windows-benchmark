[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet(
        'configs/phase13-iq4-xs-mtp-off-prose.json',
        'configs/phase13-iq4-xs-mtp-on-prose.json',
        'configs/phase13-iq4-xs-mtp-on-code.json',
        'configs/phase13-iq4-xs-mtp-off-code.json'
    )]
    [string]$Config,
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
$configObject = Get-Content -LiteralPath (Join-Path $repositoryRoot $Config) -Raw | ConvertFrom-Json
$expectedContext = [int]$configObject.configuration.context_size
$expectedLayers = [int]$configObject.configuration.gpu_layers
$expectedKvK = [string]$configObject.configuration.kv_cache_k_type
$expectedKvV = [string]$configObject.configuration.kv_cache_v_type
$expectedSpeculative = [string]$configObject.configuration.speculative_type
if ([string]$launch.model_manifest -ne 'environment/phase13-iq4-xs-download-manifest.json' -or
    [string]$launch.model_alias -ne 'Qwen3.8-27B-IQ4_XS' -or
    [int]$launch.controlled_configuration.context_size -ne $expectedContext -or
    [int]$launch.controlled_configuration.gpu_layers_requested -ne $expectedLayers -or
    [string]$launch.controlled_configuration.kv_cache_k_type -ne $expectedKvK -or
    [string]$launch.controlled_configuration.kv_cache_v_type -ne $expectedKvV -or
    [string]$launch.speculative_decoding.type -ne $expectedSpeculative -or
    -not [bool]$launch.model_hash_validated) {
    throw 'The server launch does not match the frozen Phase 13F MTP configuration.'
}
if ($expectedSpeculative -eq 'draft-mtp') {
    if ([int]$launch.speculative_decoding.draft_n_max -ne 2 -or
        [int]$launch.speculative_decoding.draft_n_min -ne 0 -or
        [string]$launch.speculative_decoding.draft_cache_k -ne 'f16' -or
        [string]$launch.speculative_decoding.draft_cache_v -ne 'f16') {
        throw 'The server launch does not match the frozen draft-mtp controls.'
    }
}
$placementPattern = "offloaded\s+$expectedLayers/66\s+layers to GPU"
if (@(Select-String -LiteralPath ([string]$launch.log_files.server) -Pattern $placementPattern).Count -lt 1) {
    throw "The startup log does not prove $expectedLayers/66 GPU layers."
}

$env:PYTHONPATH = Join-Path $repositoryRoot 'src'
& $virtualPython -m qwen_bench run --repository-root $repositoryRoot --config $Config --server-pid $ServerProcessId
if ($LASTEXITCODE -ne 0) { throw 'Phase 13F MTP measurement did not complete successfully.' }
