# Windows Task Scheduler — run as the user, daily 08:00, catch up missed runs.
param([string]$Name = "NAME", [string]$At = "08:00")
$dir = "$env:USERPROFILE\Automations\$Name"
$a = New-ScheduledTaskAction -Execute "$dir\run.bat" -WorkingDirectory $dir
$t = New-ScheduledTaskTrigger -Daily -At $At
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1) -RandomDelay (New-TimeSpan -Minutes 5) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "Automations\$Name" -Action $a -Trigger $t -Settings $s -RunLevel Limited -Force
Start-ScheduledTask -TaskName "Automations\$Name"
Get-ScheduledTaskInfo -TaskName "Automations\$Name" | Select-Object LastRunTime, LastTaskResult, NextRunTime
