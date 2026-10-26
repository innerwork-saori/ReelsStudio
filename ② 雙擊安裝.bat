@echo off
rem Reels Studio installer - double-click to run.
rem Keep this file ASCII-only: cmd reads .bat files in the system codepage. Chinese messages live in install.ps1.
rem Finds install.ps1 in any subfolder, so the folder name can stay in Chinese.
set "PS1="
for /d %%D in ("%~dp0*") do if exist "%%D\install.ps1" set "PS1=%%D\install.ps1"
if not defined PS1 (
  rem Not extracted from the zip yet: show a popup in Chinese - message is base64 UTF-16 so this file stays ASCII
  powershell -NoProfile -EncodedCommand QQBkAGQALQBUAHkAcABlACAALQBBAHMAcwBlAG0AYgBsAHkATgBhAG0AZQAgAFAAcgBlAHMAZQBuAHQAYQB0AGkAbwBuAEYAcgBhAG0AZQB3AG8AcgBrADsAIABbAHYAbwBpAGQAXQBbAFMAeQBzAHQAZQBtAC4AVwBpAG4AZABvAHcAcwAuAE0AZQBzAHMAYQBnAGUAQgBvAHgAXQA6ADoAUwBoAG8AdwAoACIAiVvdiAt6D19+Yg1OMFIAl4GJhHaUakhoAjAKAAoAGpA4Xi9m4Fa6cISQKFfTWC5+lGoI/y4AegBpAHAACf/hiGKX9HalY96eaVELTgIwCgAKAMuKSFEoV9NYLn6UagpOCWPzU3WTIACSIQww44nTWC5+aFHokA0wDP8KAI1RU2KLleOJ01gufvpRhk+EdseMmWU+WQz/2ZbKZAwwYSQgANmWymSJW92IDTACMCIALAAgACcAUgBlAGUAbABzACAAUwB0AHUAZABpAG8AIACJW92IJwAsACAAJwBPAEsAJwAsACAAJwBXAGEAcgBuAGkAbgBnACcAKQA=
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %*
echo.
pause
