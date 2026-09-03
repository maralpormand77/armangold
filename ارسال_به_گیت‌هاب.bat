@echo off
chcp 65001 > nul
title اتصال و ارسال پروژه به گیت‌هاب (Push to GitHub)
color 0B

echo =========================================================================
echo          🚀 ارسال خودکار پروژه به گیت‌هاب: maralpormand77/armangold
echo =========================================================================
echo.
echo ریپازیتوری شما متصل است به:
echo https://github.com/maralpormand77/armangold.git
echo.
echo [نکته مهم امنیتی گیت‌هاب]:
echo گیت‌هاب برای ارسال کد از ترمینال، به جای رمز اکانت، توکن دسترسی (Personal Access Token) می‌خواهد.
echo اگر توکن ساخته‌اید، آن را اینجا Paste کنید (شبیه ghp_xxxx):
echo (در صورت نداشتن توکن، وارد گیت‌هاب شوید: Settings -> Developer Settings -> Personal access tokens -> Generate new token classic)
echo.
set /p TOKEN="کد GitHub Token خود را وارد کنید (یا اگر از قبل لاگین هستید اینتر بزنید): "

if not "%TOKEN%"=="" (
    echo در حال ارسال به گیت‌هاب با توکن...
    python "%~dp0git_cli.py" push -u https://%TOKEN%@github.com/maralpormand77/armangold.git main
) else (
    echo در حال تلاش برای ارسال استاندارد...
    python "%~dp0git_cli.py" push -u origin main
)

echo.
echo =========================================================================
echo در صورت موفقیت، از این پس سرویس خودکار GitHub Actions هر ۳۰ دقیقه
echo بدون نیاز به روشن بودن کامپیوتر اجرا خواهد شد.
echo =========================================================================
pause
