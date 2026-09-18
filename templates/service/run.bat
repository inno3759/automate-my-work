@echo off
rem Wrapper: shortcut/task calls THIS. Use "start "" pythonw" for GUIs.
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
if not exist logs mkdir logs
uv run python run.py %*
