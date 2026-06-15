$ErrorActionPreference='Stop'
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$args = '--remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --user-data-dir=C:\chrome-debug-profile --no-first-run --no-default-browser-check --new-window https://www.goofish.com'
$action = New-ScheduledTaskAction -Execute $chrome -Argument $args
$principal = New-ScheduledTaskPrincipal -UserId 'mobile-computer\zhangyanbo' -LogonType Interactive
$task = New-ScheduledTask -Action $action -Principal $principal
Register-ScheduledTask -TaskName 'ChromeDebug' -InputObject $task -Force | Out-Null
Start-ScheduledTask -TaskName 'ChromeDebug'
Start-Sleep -Seconds 7
$c = (Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Output ("PORT9222_LISTEN=" + $c)
$proc = (Get-Process chrome -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Output ("CHROME_PROCS=" + $proc)
$info = Get-ScheduledTaskInfo -TaskName 'ChromeDebug'
Write-Output ("LAST_RESULT=" + $info.LastTaskResult)
