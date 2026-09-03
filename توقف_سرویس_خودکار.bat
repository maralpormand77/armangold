@echo off
chcp 65001 > nul
echo در حال توقف سرویس زمان‌بند خودکار طلا...
taskkill /F /FI "WINDOWTITLE eq سرویس بروزرسانی خودکار هر ۳۰ دقیقه قیمت طلا در PostgreSQL*" /T > nul 2>&1
taskkill /F /IM python.exe /FI "COMMANDLINE eq *scheduler_daemon.py*" > nul 2>&1
echo سرویس با موفقیت متوقف شد.
pause
