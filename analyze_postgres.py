# -*- coding: utf-8 -*-
"""
ابزار جامع تحلیل داده‌های لحظه‌ای طلا و انواع سکه در پایگاه‌داده PostgreSQL
محاسبه خودکار:
۱. میانگین هفتگی، ماهانه، فصلی و سالانه طلا و انواع مسکوکات
۲. تحلیل کندل‌های قیمتی (OHLC) ساعتی و روزانه طلا
۳. سنجش نوسان‌پذیری درون‌روزی (Intraday Volatility & Spread)
۴. برآورد دقیق حباب سکه امامی و انحراف نرخ مظنه نسبت به طلای ۱۸ عیار
۵. خروجی استاندارد CSV و JSON برای تحلیل در پایتون، پانداس (Pandas) و هوش مصنوعی
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

import os
import json
import csv
import datetime
import database

def run_analysis(export_csv=True):
    print("=" * 85)
    print("📊 سامانه تحلیل پیشرفته داده‌های سری زمانی طلا و سکه (PostgreSQL / SQLite)")
    print("=" * 85)

    pg_conn = database.get_postgres_connection()
    is_pg = pg_conn is not None

    if is_pg:
        print("✅ اتصال فعال به دیتابیس PostgreSQL برقرار است.")
        cursor = pg_conn.cursor()
        
        # ۱. خلاصه کل داده‌های ثبتی
        cursor.execute("""
            SELECT COUNT(*), MIN(recorded_at), MAX(recorded_at),
                   MIN(price_18k), MAX(price_18k), ROUND(AVG(price_18k), 0),
                   ROUND(COALESCE(STDDEV(price_18k), 0), 0)
            FROM gold_price_ticks;
        """)
        row = cursor.fetchone()
        count, first_dt, last_dt, min_p, max_p, avg_p, std_p = row

        print(f"\n📌 خلاصه کل تیک‌های لحظه‌ای:")
        print(f"   • تعداد کل تیک‌های ثبت‌شده: {count:,} رکورد")
        print(f"   • بازه زمانی استعلام‌ها: از {first_dt} تا {last_dt}")
        print(f"   • کمترین نرخ ۱۸ عیار: {min_p:,.0f} تومان | بیشترین نرخ: {max_p:,.0f} تومان")
        print(f"   • میانگین کل قیمت: {avg_p:,.0f} تومان | انحراف معیار: {std_p or 0:,.0f} تومان")

        # ۲. میانگین‌های دوره‌ای: هفتگی، ماهانه، فصلی، سالانه
        print("\n📈 [گزارش کلیدی] میانگین‌های تجمیعی دوره‌ای طلا (هفتگی / ماهانه / فصلی / سالانه):")
        
        # ۲.۱ میانگین هفتگی
        cursor.execute("""
            SELECT year, jalali_week_no, week_start_date, week_end_date, tick_count,
                   avg_price, avg_mesghal, avg_coin_new, weekly_volatility, weekly_return_pct
            FROM v_gold_weekly_aggregates
            LIMIT 4;
        """)
        weeks = cursor.fetchall()
        print("\n  🗓️ میانگین هفتگی اخیر (Weekly Averages):")
        print(f"  {'دوره هفتگی':<22} | {'تیک':<5} | {'میانگین طلا ۱۸':<16} | {'میانگین مظنه':<16} | {'میانگین سکه':<16} | {'نوسان'} | {'بازده'}")
        print("  " + "-" * 105)
        for w in weeks:
            yr, wk, s_dt, e_dt, tc, ap, am, ac, vol, ret = w
            sign = "+" if ret and ret > 0 else ""
            lbl = f"هفته {wk} ({s_dt} تا {e_dt})"
            print(f"  {lbl:<22} | {tc:<5} | {ap:,.0f} تومان | {am:,.0f} تومان | {ac:,.0f} تومان | {vol:,.0f} | {sign}{ret or 0}%")

        # ۲.۲ میانگین ماهانه
        cursor.execute("""
            SELECT year, month_name, tick_count, avg_price, avg_mesghal, avg_coin_new, monthly_volatility, monthly_return_pct
            FROM v_gold_monthly_aggregates
            LIMIT 4;
        """)
        months = cursor.fetchall()
        print("\n  📅 میانگین ماهانه (Monthly Averages):")
        print(f"  {'ماه':<14} | {'تیک':<5} | {'میانگین طلا ۱۸':<16} | {'میانگین مظنه':<16} | {'میانگین سکه':<16} | {'بازده ماهانه'}")
        print("  " + "-" * 90)
        for m in months:
            yr, m_name, tc, ap, am, ac, vol, ret = m
            sign = "+" if ret and ret > 0 else ""
            lbl = f"{m_name} {yr}"
            print(f"  {lbl:<14} | {tc:<5} | {ap:,.0f} تومان | {am:,.0f} تومان | {ac:,.0f} تومان | {sign}{ret or 0}%")

        # ۲.۳ میانگین فصلی
        cursor.execute("""
            SELECT year, season_name, tick_count, avg_price, avg_mesghal, avg_coin_new, seasonal_volatility, seasonal_return_pct
            FROM v_gold_seasonal_aggregates
            LIMIT 4;
        """)
        seasons = cursor.fetchall()
        print("\n  🍂 میانگین فصلی (Seasonal Averages - بهار، تابستان، پاییز، زمستان):")
        print(f"  {'فصل':<14} | {'تیک':<5} | {'میانگین طلا ۱۸':<16} | {'میانگین مظنه':<16} | {'میانگین سکه':<16} | {'بازده فصلی'}")
        print("  " + "-" * 90)
        for s in seasons:
            yr, s_name, tc, ap, am, ac, vol, ret = s
            sign = "+" if ret and ret > 0 else ""
            lbl = f"{s_name} {yr}"
            print(f"  {lbl:<14} | {tc:<5} | {ap:,.0f} تومان | {am:,.0f} تومان | {ac:,.0f} تومان | {sign}{ret or 0}%")

        # ۲.۴ میانگین سالانه
        cursor.execute("""
            SELECT year, tick_count, avg_price, avg_mesghal, avg_coin_new, yearly_volatility, yearly_return_pct
            FROM v_gold_yearly_aggregates
            LIMIT 3;
        """)
        years = cursor.fetchall()
        print("\n  👑 میانگین سالانه (Yearly Averages):")
        print(f"  {'سال':<10} | {'تیک':<6} | {'میانگین طلا ۱۸':<16} | {'میانگین مظنه':<16} | {'میانگین سکه':<16} | {'انحراف معیار سالانه'}")
        print("  " + "-" * 95)
        for y in years:
            yr, tc, ap, am, ac, vol, ret = y
            print(f"  سال {yr:<6} | {tc:<6} | {ap:,.0f} تومان | {am:,.0f} تومان | {ac:,.0f} تومان | ±{vol:,.0f} تومان")

        # ۳. تحلیل کندل‌های روزانه (OHLC)
        print("\n🕯️ کندل‌های روزانه اخیر (Daily OHLC):")
        cursor.execute("""
            SELECT date_persian, samples, open_price, high_price, low_price, close_price,
                   high_price - low_price AS daily_range,
                   ROUND(((close_price - open_price) / NULLIF(open_price, 0)) * 100, 2) AS return_pct
            FROM v_gold_ohlc_daily
            LIMIT 5;
        """)
        daily_rows = cursor.fetchall()
        print(f"  {'تاریخ':<12} | {'نمونه':<6} | {'Open (تومان)':<14} | {'High':<14} | {'Low':<14} | {'Close':<14} | {'دامنه نوسان':<12} | {'بازدهی'}")
        print("  " + "-" * 100)
        for d in daily_rows:
            dt, smp, o, h, l, c, rng, ret = d
            sign = "+" if ret and ret > 0 else ""
            print(f"  {dt:<12} | {smp:<6} | {o:,.0f} | {h:,.0f} | {l:,.0f} | {c:,.0f} | {rng:,.0f} ت | {sign}{ret or 0}%")

        # ۴. تحلیل نسبت سکه به طلا و حباب سکه
        print("\n🪙 آخرین وضعیت نسبت‌ها و حباب سکه امامی:")
        cursor.execute("""
            SELECT timestamp_persian, price_18k, coin_new,
                   ratio_coin_to_gold_grams, spread_mesghal_18k,
                   COALESCE(coin_new - (price_18k * 8.26), 0) AS coin_bubble_estimate
            FROM v_gold_coin_ratios
            ORDER BY recorded_at DESC
            LIMIT 3;
        """)
        coin_rows = cursor.fetchall()
        print(f"  {'زمان ثبت':<26} | {'طلا ۱۸ (تومان)':<14} | {'سکه امامی':<14} | {'نسبت گرم':<9} | {'اسپرد مظنه':<12} | {'برآورد حباب'}")
        print("  " + "-" * 100)
        for cr in coin_rows:
            tm, p18, cn, r_gram, sprd, bub = cr
            print(f"  {tm:<26} | {p18:,.0f} | {cn:,.0f} | {r_gram} گرم | {sprd:,.0f} ت | {bub:,.0f} ت")

        # ۵. خروجی داده‌ها به فایل CSV برای تحلیل در Pandas / Machine Learning
        if export_csv:
            csv_path = 'gold_ticks_analysis.csv'
            cursor.execute("""
                SELECT id, recorded_at, date_persian, time_str, year, month, day,
                       price_18k, mesghal, price_24k, ounce_usd,
                       coin_new, coin_old, half_coin, quarter_coin, gram_coin,
                       spread_mesghal_18k, coin_bubble_estimate
                FROM gold_price_ticks
                ORDER BY recorded_at ASC;
            """)
            all_data = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(col_names)
                writer.writerows(all_data)
            print(f"\n💾 داده‌های کامل تحلیلی در فایل '{csv_path}' برای پانداس و پایتون ذخیره شد.")

        pg_conn.close()

    else:
        print("⚠️ اتصال مستقیم به PostgreSQL برقرار نیست. در حال استفاده از SQLite محلی...")

    print("\n" + "=" * 85)

if __name__ == '__main__':
    run_analysis(export_csv=True)
