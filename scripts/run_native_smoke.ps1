[CmdletBinding()]
param(
    [string]$BaseUri = 'http://127.0.0.1:8090',
    [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$ModelAlias = 'Qwen3.8-27B-UD-IQ2_XXS',
    [string]$ModelManifest = 'environment/model-download-manifest.json',
    [string]$PromptFile = 'prompts/phase1-smoke.json',
    [string]$OutputDirectory = 'results/raw'
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$modelManifestPath = (Resolve-Path -LiteralPath (Join-Path $repositoryRoot $ModelManifest)).Path
$promptPath = (Resolve-Path -LiteralPath (Join-Path $repositoryRoot $PromptFile)).Path
$releaseManifestPath = (Resolve-Path -LiteralPath (Join-Path $repositoryRoot 'environment/llama-cpp-b10448-manifest.json')).Path
$resolvedOutputDirectory = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $OutputDirectory))

function Get-GpuSnapshot {
    $line = & nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw --format=csv,noheader,nounits 2>$null | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($line)) {
        return $null
    }
    $fields = $line -split ','
    if ($fields.Count -lt 8) {
        return $null
    }
    return [ordered]@{
        name = $fields[0].Trim()
        driver_version = $fields[1].Trim()
        vram_total_mib = [int]$fields[2].Trim()
        vram_used_mib = [int]$fields[3].Trim()
        vram_free_mib = [int]$fields[4].Trim()
        utilization_percent = [int]$fields[5].Trim()
        temperature_c = [int]$fields[6].Trim()
        power_draw_w = [double]$fields[7].Trim()
    }
}

function Test-SmokeResponse {
    param(
        [Parameter(Mandatory)]$Validator,
        [AllowEmptyString()][string]$Content
    )
    switch ($Validator.type) {
        'exact' { return $Content.Trim() -ceq [string]$Validator.expected }
        'contains' { return $Content.Contains([string]$Validator.expected) }
        'json_object' {
            try {
                $actual = $Content | ConvertFrom-Json -AsHashtable
                $expected = $Validator.expected | ConvertTo-Json -Compress | ConvertFrom-Json -AsHashtable
                if ($actual.Count -ne $expected.Count) { return $false }
                foreach ($key in $expected.Keys) {
                    if (-not $actual.ContainsKey($key) -or [string]$actual[$key] -cne [string]$expected[$key]) { return $false }
                }
                return $true
            }
            catch { return $false }
        }
        default { throw "Unknown validator type: $($Validator.type)" }
    }
}

$health = Invoke-RestMethod -Uri "$BaseUri/health" -Method Get -TimeoutSec 10
if ([string]$health.status -ne 'ok') {
    throw "Native llama.cpp server is not healthy at $BaseUri."
}
$modelsResponse = Invoke-RestMethod -Uri "$BaseUri/v1/models" -Method Get -TimeoutSec 10
$servedModelIds = @($modelsResponse.data | ForEach-Object { [string]$_.id })
if ($servedModelIds -notcontains $ModelAlias) {
    throw "Expected model alias '$ModelAlias' was not served. Available IDs: $($servedModelIds -join ', ')"
}

$modelManifestObject = Get-Content -LiteralPath $modelManifestPath -Raw | ConvertFrom-Json
$releaseManifestObject = Get-Content -LiteralPath $releaseManifestPath -Raw | ConvertFrom-Json
$suite = Get-Content -LiteralPath $promptPath -Raw | ConvertFrom-Json
$gitCommit = (& git -c "safe.directory=$($repositoryRoot.Replace('\', '/'))" rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
$startedAt = Get-Date
$runId = 'native-smoke-iq2-xxs-' + $startedAt.ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$gpuBefore = Get-GpuSnapshot
$runs = @()

foreach ($prompt in $suite.prompts) {
    $request = [ordered]@{
        model = $ModelAlias
        messages = @(
            [ordered]@{ role = 'system'; content = [string]$prompt.system },
            [ordered]@{ role = 'user'; content = [string]$prompt.user }
        )
        stream = $false
        max_tokens = 128
        temperature = 0.6
        top_p = 0.95
        top_k = 20
        min_p = 0.0
        seed = 42
        chat_template_kwargs = [ordered]@{
            enable_thinking = $false
            preserve_thinking = $false
        }
    }

    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri "$BaseUri/v1/chat/completions" -Method Post -ContentType 'application/json' -Body ($request | ConvertTo-Json -Depth 12 -Compress) -TimeoutSec 300
    $timer.Stop()
    $choice = $response.choices[0]
    $runs += [ordered]@{
        task_id = [string]$prompt.task_id
        passed = Test-SmokeResponse -Validator $prompt.validator -Content ([string]$choice.message.content)
        elapsed_ms = [math]::Round($timer.Elapsed.TotalMilliseconds, 3)
        finish_reason = [string]$choice.finish_reason
        response = [ordered]@{
            content = [string]$choice.message.content
            reasoning_content = $choice.message.reasoning_content
            usage = $response.usage
            timings = $response.timings
        }
        gpu_after = Get-GpuSnapshot
    }
}

$passedCount = @($runs | Where-Object { $_.passed }).Count
$record = [ordered]@{
    schema_version = 'native-smoke-1.0'
    run_id = $runId
    timestamp = $startedAt.ToString('o')
    git_commit = $gitCommit
    classification = 'phase3_native_api_proof_of_life_not_formal_benchmark'
    hardware_snapshot = 'environment/machine-snapshot-2026-08-15.json'
    runtime_manifest = 'environment/llama-cpp-b10448-manifest.json'
    model_manifest = [System.IO.Path]::GetRelativePath($repositoryRoot, $modelManifestPath).Replace('\', '/')
    prompt_suite = [System.IO.Path]::GetRelativePath($repositoryRoot, $promptPath).Replace('\', '/')
    runtime = [ordered]@{
        name = 'llama.cpp'
        release_tag = [string]$releaseManifestObject.source.release_tag
        commit = [string]$releaseManifestObject.source.target_commitish
        backend = 'CUDA'
        api = 'OpenAI-compatible /v1/chat/completions'
        bind = '127.0.0.1'
        cors_origins = 'localhost'
    }
    model = [ordered]@{
        repository = [string]$modelManifestObject.repository
        revision = [string]$modelManifestObject.repository_commit
        filename = [string]$modelManifestObject.filename
        quantization = 'UD-IQ2_XXS'
        file_size_bytes = [long]$modelManifestObject.size_bytes
        sha256 = [string]$modelManifestObject.sha256
        served_alias = $ModelAlias
    }
    configuration = [ordered]@{
        context_size = 4096
        parallel_slots = 1
        device = 'CUDA0'
        gpu_layers = -1
        fit = 'off'
        flash_attention = 'on'
        prompt_batch_size = 512
        prompt_micro_batch_size = 128
        threads = 2
        threads_batch = 2
        kv_cache_k_type = 'q8_0'
        kv_cache_v_type = 'q8_0'
        cache_ram_mib = 0
        context_checkpoints = 0
        context_shift = $false
        thinking_mode = $false
        preserve_thinking = $false
        reasoning_format = 'none'
        mtp_enabled = $false
        tools_enabled = $false
        mcp_enabled = $false
        vision_enabled = $false
        seed = 42
        temperature = 0.6
        top_p = 0.95
        top_k = 20
        min_p = 0.0
        max_output_tokens = 128
        startup_log_verbosity = 4
    }
    server_health = $health
    served_model_ids = $servedModelIds
    gpu_before = $gpuBefore
    runs = $runs
    summary = [ordered]@{
        prompts_attempted = @($runs).Count
        prompts_passed = $passedCount
        all_passed = $passedCount -eq @($runs).Count
        note = 'This verifies the native OpenAI-compatible path. Phase 4 adds warm-up, repetitions, telemetry, and variance analysis.'
    }
}

if (-not (Test-Path -LiteralPath $resolvedOutputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $resolvedOutputDirectory | Out-Null
}
$outputPath = Join-Path $resolvedOutputDirectory "$runId.json"
if (Test-Path -LiteralPath $outputPath) {
    throw "Refusing to overwrite an existing result: $outputPath"
}
$record | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $outputPath -Encoding utf8

[ordered]@{
    output_path = $outputPath
    prompts_attempted = @($runs).Count
    prompts_passed = $passedCount
    all_passed = $passedCount -eq @($runs).Count
} | ConvertTo-Json
