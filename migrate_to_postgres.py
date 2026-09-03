# -*- coding: utf-8 -*-
"""
اسکریپت انتقال آسان داده‌های ثبت‌شده از SQLite به پایگاه‌داده PostgreSQL
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

import database

def main():
    print("در حال انتقال رکوردهای ذخیره‌شده از SQLite به PostgreSQL...")
    res = database.migrate_sqlite_to_postgres()
    if res.get('success'):
        print(f"✅ با موفقیت {res.get('migrated_records')} رکورد به جدول gold_price_ticks در PostgreSQL منتقل شد!")
    else:
        print("❌ خطا در انتقال داده‌ها:")
        print("   ", res.get('error'))
        print("\nراهنما: لطفاً از اتصال سرور PostgreSQL و تنظیم مشخصات در فایل .env اطمینان حاصل فرمایید.")

if __name__ == '__main__':
    main()
