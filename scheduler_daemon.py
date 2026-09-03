# -*- coding: utf-8 -*-
"""
سرویس زمان‌بندی خودکار ۲۴ ساعته (Scheduler Daemon)
این اسکریپت هر ۳۰ دقیقه یکبار به طور کاملاً مستقل و خودکار:
۱. نرخ‌های جدید را از اتحادیه طلا و جواهر استعلام می‌کند.
۲. داده‌ها را مستقیماً در دیتابیس PostgreSQL و SQLite ذخیره می‌کند.
۳. میانگین‌های هفتگی، ماهانه، فصلی و سالانه را بروزرسانی می‌کند.
۴. فایل‌های داشبورد را دوباره بازسازی می‌کند.
کاملاً مستقل از باز بودن سایت، بدون نیاز به رفرش یا تعامل کاربر.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

import time
import datetime
import traceback
import os

# فاصله زمانی استعلام به ثانیه (پیش‌فرض: ۳۰ دقیقه = ۱۸۰۰ ثانیه)
INTERVAL_SECONDS = int(os.getenv('SYNC_INTERVAL_SECONDS', 1800))

def main():
    print("=" * 70)
    print("🚀 سرویس هوشمند استعلام و ذخیره‌سازی خودکار نرخ طلا در PostgreSQL")
    print(f"⏱️ بازه زمانی بروزرسانی: هر {INTERVAL_SECONDS // 60} دقیقه یکبار")
    print(f"🕒 زمان شروع سرویس: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70, flush=True)

    iteration = 0
    while True:
        iteration += 1
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[نوبت {iteration} - {now_str}] در حال استعلام نرخ و بروزرسانی دیتابیس...", flush=True)

        try:
            import update_live_price
            update_live_price.run_update()
            print(f"✅ نوبت {iteration} با موفقیت در دیتابیس PostgreSQL ثبت و تجمیع شد.", flush=True)
        except Exception as e:
            print(f"⚠️ بروز خطا در این نوبت: {e}", flush=True)
            traceback.print_exc()

        next_run = datetime.datetime.now() + datetime.timedelta(seconds=INTERVAL_SECONDS)
        print(f"⏳ استعلام بعدی در ساعت: {next_run.strftime('%H:%M:%S')} ({INTERVAL_SECONDS // 60} دقیقه دیگر)...", flush=True)
        
        try:
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\n🛑 سرویس توسط کاربر متوقف شد.")
            break

if __name__ == '__main__':
    main()
