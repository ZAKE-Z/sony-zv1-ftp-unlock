@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"
python -X utf8 "%~dp0scripts\en_2_unlock_ftp.py" %*
set "ftp_exit=%ERRORLEVEL%"
echo Press any key to close this window.
pause >nul
exit /b %ftp_exit%
