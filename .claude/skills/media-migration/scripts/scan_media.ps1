# scan_media.ps1 - 扫描Windows机器上的媒体文件
# 用法: powershell.exe -ExecutionPolicy Bypass -File scan_media.ps1

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$photoExts = @('jpg','jpeg','png','bmp','gif','webp','heic','tif','tiff')
$videoExts = @('mp4','avi','mkv','mov','wmv','flv','3gp','webm','m4v')
$allExts = $photoExts + $videoExts

$scanDirs = @('D:\','E:\','C:\Users\zhangyanbo\Pictures')
$skipDirs = @('Program Files','Program Files (x86)','Windows','$RECYCLE.BIN','System Volume Information')

Write-Output "=== Media Scan Report ==="
Write-Output "Scan time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Output ""

foreach ($dir in $scanDirs) {
    if (-not (Test-Path $dir)) { continue }

    Write-Output "--- Scanning $dir ---"

    $photos = 0
    $videos = 0
    $photoSize = 0
    $videoSize = 0

    Get-ChildItem -Path $dir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            $ext = $_.Extension.TrimStart('.').ToLower()
            $allExts -contains $ext -and
            ($skipDirs | ForEach-Object { $_ -notcontains $_.Directory.Name }) -notcontains $false
        } |
        ForEach-Object {
            $ext = $_.Extension.TrimStart('.').ToLower()
            if ($photoExts -contains $ext) {
                $photos++
                $photoSize += $_.Length
            } elseif ($videoExts -contains $ext) {
                $videos++
                $videoSize += $_.Length
            }
        }

    Write-Output "  Photos: $photos ($([math]::Round($photoSize/1GB, 2)) GB)"
    Write-Output "  Videos: $videos ($([math]::Round($videoSize/1GB, 2)) GB)"
    Write-Output ""
}

Write-Output "=== Scan Complete ==="
