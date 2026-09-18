# Scheduling — run it without the user, per OS

Common rules: run as the user (their files, their session); log to the
automation's `logs/`; catch up missed runs when the machine was asleep;
random delay to be polite; single-instance lock; the timer calls the
**wrapper** (`run.sh`/`run.bat`/`run.command`), never `python` directly.

## Linux — systemd user units (`templates/service/`)

```
~/.config/systemd/user/<name>.service   # ExecStart=%h/Automations/<name>/run.sh
~/.config/systemd/user/<name>.timer     # OnCalendar=Mon..Fri 08:00, Persistent=true, RandomizedDelaySec=300
systemctl --user daemon-reload && systemctl --user enable --now <name>.timer
loginctl enable-linger $USER            # so it runs without an open session
systemctl --user list-timers; journalctl --user -u <name> -n 50
```
Long-running watchers (folder watcher, WebSocket): `.service` with
`Restart=on-failure`, `RestartSec=30`, no timer.

## macOS — launchd (`templates/service/com.<name>.plist`)

```
~/Library/LaunchAgents/com.automations.<name>.plist
  ProgramArguments → /bin/zsh -lc "~/Automations/<name>/run.command"
  StartCalendarInterval → {Hour 8, Minute 0}  (array for several)
  StandardOutPath/StandardErrorPath → logs/launchd.log
  RunAtLoad false; KeepAlive false (true only for watchers)
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.automations.<name>.plist
launchctl kickstart -k gui/$(id -u)/com.automations.<name>   # run now
launchctl print gui/$(id -u)/com.automations.<name> | head   # status
```
Missed runs: launchd fires a missed `StartCalendarInterval` once at wake.
Give the script "Full Disk Access" only if it reads Mail/Desktop and macOS
blocks it (System Settings → Privacy). `-lc` so PATH includes uv.

## Windows — Task Scheduler (`templates/service/register_task.ps1`)

```powershell
$a = New-ScheduledTaskAction -Execute "$env:USERPROFILE\Automations\<name>\run.bat"
$t = New-ScheduledTaskTrigger -Daily -At 08:00      # or -RepetitionInterval (New-TimeSpan -Minutes 30)
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1) -RandomDelay (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "Automations\<name>" -Action $a -Trigger $t -Settings $s -RunLevel Limited
Start-ScheduledTask -TaskName "Automations\<name>"; Get-ScheduledTaskInfo "Automations\<name>"
```
`-StartWhenAvailable` = catch-up. Runs whether the user is logged on only
if you register with `-LogonType S4U` (no stored password, no interactive
desktop — fine for HTTP scripts, NOT for anything needing a window).
Console flash: point the task at `wscript.exe hidden.vbs` or use
`pythonw`.

## Browser-side schedules

Extension: `chrome.alarms.create('poll', {periodInMinutes: 30})` in the
service worker; runs while the browser is open. Userscripts cannot
schedule; they run when the page is open — for "check every X" use an
extension or a Python script.

## Verification (do all three before handoff)

1. Trigger once by hand (`systemctl --user start`, `launchctl kickstart`,
   `Start-ScheduledTask`) → the human log line appears.
2. Let the real trigger fire once (shorten the schedule to +2 min, watch,
   restore).
3. Reboot/sleep test if feasible: does it catch up?
Write the status command in the README.
