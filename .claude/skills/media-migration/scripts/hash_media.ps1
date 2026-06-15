# hash_media.ps1 - 计算媒体文件MD5哈希（用于去重）
# 用法: powershell.exe -ExecutionPolicy Bypass -File hash_media.ps1
# 输出格式: md5|filesize|filepath

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$allExt = @('jpg','jpeg','png','bmp','gif','webp','heic','tif','tiff','mp4','avi','mkv','mov','wmv','flv','3gp','webm','m4v')
$skipDirs = @('Program Files','Program Files (x86)','Windows','$RECYCLE.BIN','System Volume Information')

$dirs = @('D:\DCIM','D:\DCIMScreenshots','C:\Users\zhangyanbo\Pictures')
$dirs += Get-ChildItem E:\ -Directory -ErrorAction SilentlyContinue |
    Where-Object { $skipDirs -notcontains $_.Name } |
    Select-Object -ExpandProperty FullName

foreach ($d in $dirs) {
    if (Test-Path $d) {
        Get-ChildItem -Path $d -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $allExt -contains $_.Extension.TrimStart('.').ToLower() } |
            ForEach-Object {
                $raw = certutil -hashfile $_.FullName MD5
                $h = ''
                foreach ($line in $raw) {
                    $trimmed = $line.Trim()
                    if ($trimmed -match '^[0-9a-fA-F]{32}$') { $h += $trimmed.ToLower() }
                }
                if ($h -ne '') {
                    Write-Output ($h + '|' + $_.Length + '|' + $_.FullName)
                }
            }
    }
}
