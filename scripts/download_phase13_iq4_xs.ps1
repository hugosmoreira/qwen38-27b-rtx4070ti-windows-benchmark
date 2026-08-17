[CmdletBinding()]
param(
    [string]$Manifest = 'environment/phase13-iq4-xs-download-manifest.json',
    [ValidateRange(1, 100)][int]$AdditionalSafetyGiB = 10,
    [switch]$PreflightOnly
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $Manifest))
if (-not $manifestPath.StartsWith($repositoryRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The manifest must resolve inside the repository.'
}
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Model manifest not found: $manifestPath"
}

$model = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
foreach ($required in @('repository_commit', 'filename', 'relative_local_path', 'size_bytes', 'sha256', 'download_url')) {
    if ($null -eq $model.$required -or [string]::IsNullOrWhiteSpace([string]$model.$required)) {
        throw "Model manifest field is missing: $required"
    }
}
if ([string]$model.repository_commit -notmatch '^[0-9a-f]{40}$') {
    throw 'The repository revision must be a full lowercase Git commit.'
}
if ([string]$model.sha256 -notmatch '^[0-9a-f]{64}$') {
    throw 'The model SHA-256 must contain 64 lowercase hexadecimal characters.'
}

$destination = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot ([string]$model.relative_local_path)))
if (-not $destination.StartsWith($repositoryRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The model destination must resolve inside the repository.'
}
$destinationDirectory = Split-Path -Parent $destination
if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $destinationDirectory | Out-Null
}
$directoryInfo = Get-Item -LiteralPath $destinationDirectory -Force
if (($directoryInfo.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'The model destination directory may not be a symbolic link, junction, or other reparse point.'
}

$partial = $destination + '.partial'
$expectedBytes = [long]$model.size_bytes
$safetyBytes = [long]$AdditionalSafetyGiB * 1GB
$requiredFreeBytes = [long](2 * $expectedBytes + $safetyBytes)
$driveRoot = [System.IO.Path]::GetPathRoot($destination)
$drive = [System.IO.DriveInfo]::new($driveRoot)
$freeBefore = [long]$drive.AvailableFreeSpace

if (Test-Path -LiteralPath $destination -PathType Leaf) {
    $existing = Get-Item -LiteralPath $destination
    if ($existing.Length -ne $expectedBytes) {
        throw "Existing destination has the wrong size. Expected $expectedBytes bytes; found $($existing.Length)."
    }
    $existingHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($existingHash -cne ([string]$model.sha256)) {
        throw "Existing destination failed SHA-256 validation: $existingHash"
    }
    [ordered]@{
        status = 'already_present_and_validated'
        relative_local_path = [string]$model.relative_local_path
        size_bytes = $existing.Length
        sha256 = $existingHash
        free_bytes_before = $freeBefore
        network_download_performed = $false
    } | ConvertTo-Json -Depth 4
    exit 0
}

if ($freeBefore -lt $requiredFreeBytes) {
    throw "Insufficient free space. Required safety gate: $requiredFreeBytes bytes; available: $freeBefore bytes."
}
if ($PreflightOnly) {
    [ordered]@{
        status = 'preflight_passed'
        relative_local_path = [string]$model.relative_local_path
        download_url = [string]$model.download_url
        expected_size_bytes = $expectedBytes
        expected_sha256 = [string]$model.sha256
        free_bytes = $freeBefore
        required_free_bytes = $requiredFreeBytes
        existing_partial_bytes = if (Test-Path -LiteralPath $partial -PathType Leaf) { (Get-Item -LiteralPath $partial).Length } else { 0 }
        network_download_performed = $false
    } | ConvertTo-Json -Depth 4
    exit 0
}
if (Test-Path -LiteralPath $partial -PathType Leaf) {
    $partialItem = Get-Item -LiteralPath $partial
    if ($partialItem.Length -gt $expectedBytes) {
        throw "Partial download is larger than the pinned artifact: $($partialItem.Length) bytes."
    }
}

$curl = Get-Command curl.exe -ErrorAction Stop
& $curl.Source `
    --location `
    --fail `
    --retry 5 `
    --retry-delay 5 `
    --continue-at - `
    --output $partial `
    ([string]$model.download_url)
if ($LASTEXITCODE -ne 0) {
    throw "curl download failed with exit code $LASTEXITCODE. The partial file was retained for a safe resume."
}

$downloaded = Get-Item -LiteralPath $partial
if ($downloaded.Length -ne $expectedBytes) {
    throw "Downloaded size mismatch. Expected $expectedBytes bytes; found $($downloaded.Length)."
}
$actualHash = (Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -cne ([string]$model.sha256)) {
    throw "Downloaded SHA-256 mismatch. Expected $($model.sha256); found $actualHash. The partial file was retained for inspection."
}

Move-Item -LiteralPath $partial -Destination $destination
$freeAfter = [long]([System.IO.DriveInfo]::new($driveRoot).AvailableFreeSpace)
[ordered]@{
    status = 'downloaded_and_sha256_validated'
    relative_local_path = [string]$model.relative_local_path
    size_bytes = $downloaded.Length
    sha256 = $actualHash
    free_bytes_before = $freeBefore
    free_bytes_after = $freeAfter
    network_download_performed = $true
} | ConvertTo-Json -Depth 4
