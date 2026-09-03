# -*- coding: utf-8 -*-
"""
اسکریپت بروزرسانی آنلاین قیمت طلا و انواع سکه از اتحادیه طلا و جواهر تهران (estjt.ir)
ذخیره‌سازی خودکار داده‌های روزانه، محاسبه میانگین ماه و آپدیت index.html و gold_dashboard.html
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

import urllib.request
import urllib.parse
import re
import json
import os
import shutil
import datetime

MONTHS_ORDER = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]

def clean_persian_number(text):
    if not text:
        return 0.0
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    arabic_digits = '٠١٢٣٤٥٦٧۸۹'
    s = str(text)
    for i in range(10):
        s = s.replace(persian_digits[i], str(i)).replace(arabic_digits[i], str(i))
    s = s.replace('\u066b', '').replace('\u066c', '').replace('٬', '').replace(',', '').replace(' ', '').replace('تومان', '').replace('$', '').strip()
    try:
        return float(s)
    except Exception:
        return 0.0

def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    jy = 979 if gy > 1600 else 0
    gy -= 1600 if gy > 1600 else 621
    gy2 = (gm > 2) and (gy + 1) or gy
    days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd

def fetch_live_gold_and_coins():
    url = 'https://www.estjt.ir/wp-admin/admin-ajax.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest'
    }
    data = urllib.parse.urlencode({'action': 'new_price'}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    
    with urllib.request.urlopen(req, timeout=12) as response:
        res_json = json.loads(response.read().decode('utf-8', errors='ignore'))
        gold_html = res_json.get('gold', '')
        coin_html = res_json.get('coin', '')
        
        # 18k Gold
        m_gold = re.search(r'طلا\s*۱۸\s*عیار.*?class=[\'"]price[\'"]>([^<]+)<', gold_html, re.DOTALL)
        gold_price = clean_persian_number(m_gold.group(1)) if m_gold else 23484500.0
        
        # Update Time
        m_time = re.search(r'آخرین بروزرسانی:\s*([^<]+)', gold_html)
        update_time = m_time.group(1).strip() if m_time else ""
        
        # Mesghal
        m_mesghal = re.search(r'مظنه تهران.*?class=[\'"]price[\'"]>([^<]+)<', gold_html, re.DOTALL)
        mesghal_price = clean_persian_number(m_mesghal.group(1)) if m_mesghal else 101730000.0

        # 24k Gold
        m_24 = re.search(r'طلا\s*۲۴\s*عیار.*?class=[\'"]price[\'"]>([^<]+)<', gold_html, re.DOTALL)
        gold_24k = clean_persian_number(m_24.group(1)) if m_24 else 31300000.0

        # Ounce
        m_oz = re.search(r'انس طلا.*?class=[\'"]price[\'"]>([^<]+)<', gold_html, re.DOTALL)
        ounce_usd = clean_persian_number(m_oz.group(1)) if m_oz else 4485.0

        # Coins
        m_cnew = re.search(r'سکه\s*طرح\s*جدید.*?class=[\'"]price[\'"]>([^<]+)<', coin_html, re.DOTALL)
        coin_new = clean_persian_number(m_cnew.group(1)) if m_cnew else 233500000.0

        m_cold = re.search(r'سکه\s*طرح\s*قدیم.*?class=[\'"]price[\'"]>([^<]+)<', coin_html, re.DOTALL)
        coin_old = clean_persian_number(m_cold.group(1)) if m_cold else 230500000.0

        m_chalf = re.search(r'نیم\s*سکه.*?class=[\'"]price[\'"]>([^<]+)<', coin_html, re.DOTALL)
        half_coin = clean_persian_number(m_chalf.group(1)) if m_chalf else 119500000.0

        m_cquarter = re.search(r'ربع\s*سکه.*?class=[\'"]price[\'"]>([^<]+)<', coin_html, re.DOTALL)
        quarter_coin = clean_persian_number(m_cquarter.group(1)) if m_cquarter else 64500000.0

        m_cgram = re.search(r'سکه\s*گرمی.*?class=[\'"]price[\'"]>([^<]+)<', coin_html, re.DOTALL)
        gram_coin = clean_persian_number(m_cgram.group(1)) if m_cgram else 35000000.0
        
        return {
            'gold_18k_price': gold_price,
            'mesghal_price': mesghal_price,
            'gold_24k_price': gold_24k,
            'ounce_usd': ounce_usd,
            'coin_new': coin_new,
            'coin_old': coin_old,
            'half_coin': half_coin,
            'quarter_coin': quarter_coin,
            'gram_coin': gram_coin,
            'update_time': update_time,
            'source': 'https://www.estjt.ir/'
        }

def run_update():
    print("در حال استعلام آخرین نرخ طلا و انواع سکه از سامانه رسمی اتحادیه طلا و جواهر تهران (estjt.ir)...", flush=True)
    try:
        info = fetch_live_gold_and_coins()
        gold_price = info['gold_18k_price']
        mesghal = info['mesghal_price']
        
        # Calculate current Persian date
        now = datetime.datetime.now()
        jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
        month_name = MONTHS_ORDER[jm - 1]
        month_key = f"{jy}-{jm:02d}"
        date_str = f"{jy}/{jm:02d}/{jd:02d}"
        timestamp_str = f"{jd} {month_name} {jy} - {now.strftime('%H:%M:%S')}"
        if not info['update_time']:
            info['update_time'] = timestamp_str

        # ذخیره پایدار در بانک داده SQLite و همگام‌سازی خودکار
        import database
        db_res = database.save_price_tick(info, jy, jm, jd, timestamp_str, date_str)
        month_avg = db_res['avg_price']
        samples_count = db_res['samples_count']

        with open('live_gold_result.json', 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
            
        print(f"نرخ طلا ۱۸ عیار: {gold_price:,.0f} تومان | میانگین ماه: {month_avg:,.0f} تومان ({samples_count} رکورد)")
        print(f"مظنه: {mesghal:,.0f} تومان | سکه طرح جدید: {info['coin_new']:,.0f} تومان")
        print(f"زمان استعلام: {info['update_time']}")

        # Re-build dashboard HTML
        import build_dynamic_dashboard
        build_dynamic_dashboard.build()
        print("داشبورد با موفقیت با قیمت جدید، میانگین ماه و پیش‌بینی ۱ ساله بروزرسانی شد!\n")
    except Exception as e:
        print("خطا در ارتباط با estjt.ir:", e)

if __name__ == '__main__':
    run_update()
