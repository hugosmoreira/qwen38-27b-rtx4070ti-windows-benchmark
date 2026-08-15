[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ManifestPath,
    [string]$RuntimeRecord,
    [string]$BaseUri = 'http://127.0.0.1:8888',
    [string]$PromptFile,
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($PromptFile)) {
    $PromptFile = Join-Path $repositoryRoot 'prompts\phase1-smoke.json'
}
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $repositoryRoot 'results\raw'
}

$resolvedManifestPath = (Resolve-Path -LiteralPath $ManifestPath).Path
$desktopSecretPath = Join-Path $env:USERPROFILE '.unsloth\studio\auth\.desktop_secret'
$tauriLogPath = Join-Path $env:USERPROFILE '.unsloth\studio\tauri.log'

foreach ($requiredPath in @($PromptFile, $resolvedManifestPath, $desktopSecretPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required file not found: $requiredPath"
    }
}

function Get-DesktopAccessToken {
    $secret = (Get-Content -LiteralPath $desktopSecretPath -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($secret)) {
        throw 'The Unsloth Desktop local secret is empty.'
    }

    $body = @{ secret = $secret } | ConvertTo-Json -Compress
    $token = Invoke-RestMethod -Uri "$BaseUri/api/auth/desktop-login" -Method Post -ContentType 'application/json' -Body $body
    if ([string]::IsNullOrWhiteSpace($token.access_token)) {
        throw 'Unsloth Desktop did not return a local access token.'
    }
    return $token.access_token
}

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
        'exact' {
            return $Content.Trim() -ceq [string]$Validator.expected
        }
        'contains' {
            return $Content.Contains([string]$Validator.expected)
        }
        'json_object' {
            try {
                $actual = $Content | ConvertFrom-Json -AsHashtable
                $expected = $Validator.expected | ConvertTo-Json -Compress | ConvertFrom-Json -AsHashtable
                if ($actual.Count -ne $expected.Count) {
                    return $false
                }
                foreach ($key in $expected.Keys) {
                    if (-not $actual.ContainsKey($key) -or [string]$actual[$key] -cne [string]$expected[$key]) {
                        return $false
                    }
                }
                return $true
            }
            catch {
                return $false
            }
        }
        default {
            throw "Unknown validator type: $($Validator.type)"
        }
    }
}

$manifest = Get-Content -LiteralPath $resolvedManifestPath -Raw | ConvertFrom-Json
$suite = Get-Content -LiteralPath $PromptFile -Raw | ConvertFrom-Json
$accessToken = Get-DesktopAccessToken
$headers = @{ Authorization = "Bearer $accessToken" }
$status = Invoke-RestMethod -Uri "$BaseUri/api/inference/status" -Headers $headers -Method Get

$expectedModelPath = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $manifest.relative_local_path))
$activeModelPath = [System.IO.Path]::GetFullPath([string]$status.model_identifier)
if (-not $expectedModelPath.Equals($activeModelPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "The active model does not match the manifest. Expected '$expectedModelPath'; found '$activeModelPath'."
}

$flashAttention = $null
if (Test-Path -LiteralPath $tauriLogPath -PathType Leaf) {
    $launchLines = Select-String -LiteralPath $tauriLogPath -Pattern 'Starting llama-server:' | Where-Object { $_.Line.Contains([string]$manifest.filename) }
    $latestLaunch = $launchLines | Select-Object -Last 1
    if ($null -ne $latestLaunch -and $latestLaunch.Line -match '--flash-attn\s+(on|off|auto)') {
        $flashAttention = $Matches[1]
    }
}

$configurationChecks = [ordered]@{
    context_length_4096 = [int]$status.context_length -eq 4096
    parallel_slots_1 = [int]$status.parallel_slots -eq 1
    q8_kv_cache = [string]$status.cache_type_kv -eq 'q8_0'
    speculative_decoding_off = [string]$status.speculative_type -eq 'off'
    text_only = -not [bool]$status.is_vision
    flash_attention_on = [string]$flashAttention -eq 'on'
}
if ($configurationChecks.Values -contains $false) {
    throw "The active model does not match the controlled smoke configuration: $($configurationChecks | ConvertTo-Json -Compress)"
}

$quantization = if ([string]::IsNullOrWhiteSpace([string]$manifest.quantization)) {
    if ([string]$manifest.filename -match '(UD-[A-Z0-9_]+)\.gguf$') { $Matches[1] } else { 'unknown' }
} else {
    [string]$manifest.quantization
}
$quantSlug = $quantization.ToLowerInvariant().Replace('_', '-')
$manifestRelative = [System.IO.Path]::GetRelativePath($repositoryRoot, $resolvedManifestPath).Replace('\', '/')
$runtimeRecordRelative = if ([string]::IsNullOrWhiteSpace($RuntimeRecord)) { $null } else { $RuntimeRecord.Replace('\', '/') }
$gitCommit = (& git -c "safe.directory=$($repositoryRoot.Replace('\', '/'))" rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
$startedAt = Get-Date
$runId = "quant-smoke-$quantSlug-" + $startedAt.ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$gpuBefore = Get-GpuSnapshot
$runs = @()

foreach ($prompt in $suite.prompts) {
    $request = [ordered]@{
        messages = @(
            [ordered]@{ role = 'system'; content = [string]$prompt.system },
            [ordered]@{ role = 'user'; content = [string]$prompt.user }
        )
        stream = $false
        max_completion_tokens = 128
        temperature = 0.6
        top_p = 0.95
        top_k = 20
        min_p = 0.0
        seed = 42
        enable_thinking = $false
        preserve_thinking = $false
        enable_tools = $false
        enabled_tools = @()
        mcp_enabled = $false
        bypass_permissions = $false
    }

    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri "$BaseUri/api/inference/chat/completions" -Headers $headers -Method Post -ContentType 'application/json' -Body ($request | ConvertTo-Json -Depth 12 -Compress) -TimeoutSec 300
    $timer.Stop()

    $choice = $response.choices[0]
    $completionTokens = [int]$response.usage.completion_tokens
    $elapsedSeconds = $timer.Elapsed.TotalSeconds
    $runs += [ordered]@{
        task_id = [string]$prompt.task_id
        passed = Test-SmokeResponse -Validator $prompt.validator -Content ([string]$choice.message.content)
        elapsed_ms = [math]::Round($timer.Elapsed.TotalMilliseconds, 3)
        end_to_end_completion_tokens_per_second = if ($elapsedSeconds -gt 0) { [math]::Round($completionTokens / $elapsedSeconds, 3) } else { $null }
        finish_reason = [string]$choice.finish_reason
        response = [ordered]@{
            content = [string]$choice.message.content
            reasoning_content = $choice.message.reasoning_content
            usage = $response.usage
        }
        gpu_after = Get-GpuSnapshot
    }
}

$passedCount = @($runs | Where-Object { $_.passed }).Count
$record = [ordered]@{
    schema_version = 'quant-smoke-1.0'
    run_id = $runId
    timestamp = $startedAt.ToString('o')
    git_commit = $gitCommit
    classification = 'proof_of_life_not_formal_benchmark'
    hardware_snapshot = 'environment/machine-snapshot-2026-08-15.json'
    runtime_record = $runtimeRecordRelative
    model_manifest = $manifestRelative
    prompt_suite = 'prompts/phase1-smoke.json'
    runtime = [ordered]@{
        name = 'Unsloth Desktop'
        backend = 'bundled llama.cpp'
        llama_cpp_installed_tag = [string]$status.llama_cpp_installed_tag
    }
    model = [ordered]@{
        repository = [string]$manifest.repository
        revision = [string]$manifest.repository_commit
        filename = [string]$manifest.filename
        quantization = $quantization
        file_size_bytes = [long]$manifest.size_bytes
        sha256 = [string]$manifest.sha256
    }
    configuration = [ordered]@{
        context_size = [int]$status.context_length
        native_context_size = [int]$status.native_context_length
        parallel_slots = [int]$status.parallel_slots
        model_layers = [int]$status.n_layers
        gpu_memory_mode = [string]$status.gpu_memory_mode
        gpu_layers = [int]$status.gpu_layers
        kv_cache_k_type = [string]$status.cache_type_kv
        kv_cache_v_type = [string]$status.cache_type_kv
        flash_attention = $flashAttention
        prompt_batch_size = [int]$status.requested_n_batch
        prompt_micro_batch_size = [int]$status.requested_n_ubatch
        thinking_mode = $false
        preserve_thinking = $false
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
    }
    configuration_checks = $configurationChecks
    gpu_before = $gpuBefore
    runs = $runs
    summary = [ordered]@{
        prompts_attempted = @($runs).Count
        prompts_passed = $passedCount
        all_passed = $passedCount -eq @($runs).Count
        note = 'Short end-to-end rates include API and orchestration overhead and are not decode-only benchmark results.'
    }
}

if (-not (Test-Path -LiteralPath $OutputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}
$outputPath = Join-Path $OutputDirectory "$runId.json"
if (Test-Path -LiteralPath $outputPath) {
    throw "Refusing to overwrite an existing result: $outputPath"
}

$json = $record | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText($outputPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

[ordered]@{
    output_path = $outputPath
    prompts_attempted = @($runs).Count
    prompts_passed = $passedCount
    all_passed = $passedCount -eq @($runs).Count
} | ConvertTo-Json
