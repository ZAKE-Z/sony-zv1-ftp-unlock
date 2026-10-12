@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"
python -X utf8 "%~dp0scripts\zh_4_还原.py" %*
set "ftp_exit=%ERRORLEVEL%"
echo 按任意键关闭窗口。
pause >nul
exit /b %ftp_exit%
