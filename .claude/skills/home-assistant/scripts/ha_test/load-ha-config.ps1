#!/usr/bin/env pwsh
# Home Assistant Configuration Loader
# Scans HA instance and generates/updates TOOLS.md configuration

param(
    [string]$HaUrl = "http://192.168.3.172:8123",
    [string]$HaToken,
    [string]$ToolsPath = "$(Split-Path $PSScriptRoot -Parent | Split-Path -Parent | Split-Path -Parent)\TOOLS.md",
    [switch]$Verbose
)

# Set console output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Load token from TOOLS.md if not provided
if (-not $HaToken) {
    if (Test-Path $ToolsPath) {
        $toolsContent = Get-Content $ToolsPath -Raw
        if ($toolsContent -match 'HA Token.*?`([^`]+)`') {
            $HaToken = $matches[1]
            if ($Verbose) { Write-Host "Loaded token from TOOLS.md" -ForegroundColor Cyan }
        }
    }
    if (-not $HaToken) {
        Write-Error "HA Token not found in TOOLS.md. Please provide -HaToken"
        exit 1
    }
}

$headers = @{
    "Authorization" = "Bearer $HaToken"
    "Content-Type" = "application/json"
}

Write-Host "Home Assistant Configuration Loader" -ForegroundColor Cyan
Write-Host "URL: $HaUrl" -ForegroundColor Gray
Write-Host ""

# Test connection
try {
    $test = Invoke-WebRequest -Uri "$HaUrl/api/config" -Headers $headers -Method GET -UseBasicParsing -ErrorAction Stop
    $config = $test.Content | ConvertFrom-Json
    Write-Host "Connected to Home Assistant $($config.version)" -ForegroundColor Green
} catch {
    Write-Error "Failed to connect: $($_.Exception.Message)"
    exit 1
}

# Function to fix double-encoded UTF-8 (common HA encoding issue)
function Fix-DoubleEncodedUTF8 {
    param([string]$Text)
    if (-not $Text) { return $Text }
    try {
        $latin1 = [System.Text.Encoding]::GetEncoding("iso-8859-1")
        $utf8Bytes = $latin1.GetBytes($Text)
        return [System.Text.Encoding]::UTF8.GetString($utf8Bytes)
    } catch {
        return $Text
    }
}

# Fetch all states
Write-Host "`nScanning entities..." -ForegroundColor Cyan
$response = Invoke-WebRequest -Uri "$HaUrl/api/states" -Headers $headers -Method GET -UseBasicParsing
$jsonContent = $response.Content
$entities = $jsonContent | ConvertFrom-Json

# Fix encoding for all entity names
foreach ($entity in $entities) {
    if ($entity.attributes.friendly_name) {
        $entity.attributes.friendly_name = Fix-DoubleEncodedUTF8 -Text $entity.attributes.friendly_name
    }
}

# Count by domain
$domains = @{}
foreach ($entity in $entities) {
    $domain = ($entity.entity_id -split '\.')[0]
    if (-not $domains.ContainsKey($domain)) { $domains[$domain] = 0 }
    $domains[$domain]++
}

Write-Host "Found $($entities.Count) entities across $($domains.Count) domains" -ForegroundColor Green

# Build configuration sections
$config_data = @{
    connection = @{
        url = $HaUrl
        token = $HaToken
    }
    meta = @{
        generated = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
        totalEntities = $entities.Count
        haVersion = $config.version
    }
    domains = $domains
    lights = @()
    switches = @()
    covers = @()
    climates = @()
    media_players = @()
    cameras = @()
    vacuums = @()
    fans = @()
    sensors = @()
    areas = @()
}

# Categorize entities
foreach ($entity in $entities) {
    $domain = ($entity.entity_id -split '\.')[0]
    $info = @{
        entity_id = $entity.entity_id
        name = $entity.attributes.friendly_name
        area_id = $entity.attributes.area_id
        device_id = $entity.attributes.device_id
    }
    
    switch ($domain) {
        "light" { $config_data.lights += $info }
        "switch" { $config_data.switches += $info }
        "cover" { $config_data.covers += $info }
        "climate" { $config_data.climates += $info }
        "media_player" { $config_data.media_players += $info }
        "camera" { $config_data.cameras += $info }
        "vacuum" { $config_data.vacuums += $info }
        "fan" { $config_data.fans += $info }
        "sensor" { 
            if ($entity.attributes.device_class -or $entity.attributes.unit_of_measurement) {
                $info.device_class = $entity.attributes.device_class
                $info.unit = $entity.attributes.unit_of_measurement
                $config_data.sensors += $info
            }
        }
    }
}

# Get unique areas
$areaIds = @{}
foreach ($entity in $entities) {
    if ($entity.attributes.area_id) {
        $areaIds[$entity.attributes.area_id] = $true
    }
}
$config_data.areas = @($areaIds.Keys)

# Remove old auto-generated section if exists
if (Test-Path $ToolsPath) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    $content = [System.IO.File]::ReadAllText($ToolsPath, [System.Text.Encoding]::UTF8)
    
    if ($content -match '(?s)(.*?)(## .* Auto-Generated Config.*)') {
        $content = $matches[1]
        [System.IO.File]::WriteAllText($ToolsPath, $content, $utf8NoBom)
        Write-Host "Removed old auto-generated section" -ForegroundColor Yellow
    }
}

# Generate markdown using StringBuilder for better UTF-8 handling
$sb = New-Object System.Text.StringBuilder

# Use emoji directly (PowerShell 6+ handles UTF-8 in strings)
$sb.AppendLine("") >> $null
$sb.AppendLine("---") >> $null
$sb.AppendLine("") >> $null
$sb.AppendLine("## 🏠 Home Assistant Auto-Generated Config") >> $null
$sb.AppendLine("_Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm")_") >> $null
$sb.AppendLine("_Instance: $($config.version) ($($HaUrl))_") >> $null
$sb.AppendLine("") >> $null
$sb.AppendLine("### 📊 Entity Summary") >> $null
$sb.AppendLine("") >> $null
$sb.AppendLine("| Domain | Count |") >> $null
$sb.AppendLine("|--------|-------|") >> $null

foreach ($domain in $domains.GetEnumerator() | Sort-Object Value -Descending) {
    $sb.AppendLine("| $($domain.Name) | $($domain.Value) |") >> $null
}

# Lights
if ($config_data.lights.Count -gt 0) {
    $sb.AppendLine("") >> $null
    $sb.AppendLine("### 💡 Lights ($($config_data.lights.Count))") >> $null
    $sb.AppendLine("") >> $null
    $sb.AppendLine("| Entity ID | Name | Area |") >> $null
    $sb.AppendLine("|-----------|------|------|") >> $null
    foreach ($light in $config_data.lights) {
        $sb.AppendLine("| ``$($light.entity_id)`` | $($light.name) | ``$($light.area_id)`` |") >> $null
    }
}

# Switches
if ($config_data.switches.Count -gt 0) {
    $sb.AppendLine("") >> $null
    $sb.AppendLine("### 🔌 Switches ($($config_data.switches.Count))") >> $null
    $sb.AppendLine("") >> $null
    $sb.AppendLine("| Entity ID | Name | Area |") >> $null
    $sb.AppendLine("|-----------|------|------|") >> $null
    foreach ($switch in $config_data.switches) {
        $sb.AppendLine("| ``$($switch.entity_id)`` | $($switch.name) | ``$($switch.area_id)`` |") >> $null
    }
}

# Covers
if ($config_data.covers.Count -gt 0) {
    $sb.AppendLine("") >> $null
    $sb.AppendLine("### 🪟 Covers ($($config_data.covers.Count))") >> $null
    $sb.AppendLine("") >> $null
    $sb.AppendLine("| Entity ID | Name | Area |") >> $null
    $sb.AppendLine("|-----------|------|------|") >> $null
    foreach ($cover in $config_data.covers) {
        $sb.AppendLine("| ``$($cover.entity_id)`` | $($cover.name) | ``$($cover.area_id)`` |") >> $null
    }
}

# Climates
if ($config_data.climates.Count -gt 0) {
    $sb.AppendLine("") >> $null
    $sb.AppendLine("### 🌡️ Climates ($($config_data.climates.Count))") >> $null
    $sb.AppendLine("") >> $null
    $sb.AppendLine("| Entity ID | Name | Area |") >> $null
    $sb.AppendLine("|-----------|------|------|") >> $null
    foreach ($climate in $config_data.climates) {
        $sb.AppendLine("| ``$($climate.entity_id)`` | $($climate.name) | ``$($climate.area_id)`` |") >> $null
    }
}

# Media Players
if ($config_data.media_players.Count -gt 0) {
    $sb.AppendLine("") >> $null
    $sb.AppendLine("### 🔊 Media Players ($($config_data.media_players.Count))") >> $null
    $sb.AppendLine("") >> $null
    $sb.AppendLine("| Entity ID | Name | Area |") >> $null
    $sb.AppendLine("|-----------|------|------|") >> $null
    foreach ($mp in $config_data.media_players) {
        $sb.AppendLine("| ``$($mp.entity_id)`` | $($mp.name) | ``$($mp.area_id)`` |") >> $null
    }
}

# Vacuums
if ($config_data.vacuums.Count -gt 0) {
    $sb.AppendLine("") >> $null
    $sb.AppendLine("### 🧹 Vacuums ($($config_data.vacuums.Count))") >> $null
    $sb.AppendLine("") >> $null
    $sb.AppendLine("| Entity ID | Name | Area |") >> $null
    $sb.AppendLine("|-----------|------|------|") >> $null
    foreach ($vac in $config_data.vacuums) {
        $sb.AppendLine("| ``$($vac.entity_id)`` | $($vac.name) | ``$($vac.area_id)`` |") >> $null
    }
}

# Cameras
if ($config_data.cameras.Count -gt 0) {
    $sb.AppendLine("") >> $null
    $sb.AppendLine("### 📷 Cameras ($($config_data.cameras.Count))") >> $null
    $sb.AppendLine("") >> $null
    $sb.AppendLine("| Entity ID | Name | Area |") >> $null
    $sb.AppendLine("|-----------|------|------|") >> $null
    foreach ($cam in $config_data.cameras) {
        $sb.AppendLine("| ``$($cam.entity_id)`` | $($cam.name) | ``$($cam.area_id)`` |") >> $null
    }
}

# Write to file with UTF-8 without BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$md = $sb.ToString()
[System.IO.File]::AppendAllText($ToolsPath, $md, $utf8NoBom)
Write-Host "Configuration appended to $ToolsPath" -ForegroundColor Green

# Export JSON for skill consumption
$jsonPath = "$(Split-Path $PSScriptRoot -Parent)\ha-config.json"
$jsonContent = $config_data | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($jsonPath, $jsonContent, $utf8NoBom)
Write-Host "JSON config saved to $jsonPath" -ForegroundColor Green

Write-Host "`nDone!" -ForegroundColor Green
