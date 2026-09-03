# -*- coding: utf-8 -*-
"""
ماژول بانک داده چندمنظوره (Database) برای ذخیره آنلاین داده‌های لحظه‌ای و تحلیل داده‌ها:
۱. پشتیبانی کامل از PostgreSQL (پایگاه‌داده قدرتمند تحلیلی برای یادگیری ماشین و تحلیل‌های بلادرنگ)
۲. پشتیبانی از SQLite به عنوان پشتیبان محلی امن و پایدار
۳. نماهای تحلیلی پیشرفته (Analytical Views: OHLC ساعتی و روزانه، حباب و نوسان‌سنجی)
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

import os
import json
import datetime
import sqlite3

# Try loading .env if python-dotenv exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Try importing psycopg2 for PostgreSQL
try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor, Json
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gold_database.db')

MONTHS_ORDER = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]

# ----------------------------------------------------
# PostgreSQL Connection Management
# ----------------------------------------------------
def get_postgres_config():
    """دریافت اطلاعات اتصال به PostgreSQL از متغیرهای محیطی یا فایل .env"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return {'dsn': database_url}
    
    host = os.getenv('POSTGRES_HOST')
    if host:
        return {
            'host': host,
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'dbname': os.getenv('POSTGRES_DB', 'gold_db'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', '')
        }
    return None

def get_postgres_connection():
    """ایجاد اتصال به PostgreSQL"""
    if not HAS_PSYCOPG2:
        return None
    
    cfg = get_postgres_config()
    if not cfg:
        return None
    
    try:
        if 'dsn' in cfg:
            conn = psycopg2.connect(cfg['dsn'], connect_timeout=5)
        else:
            conn = psycopg2.connect(
                host=cfg['host'],
                port=cfg['port'],
                dbname=cfg['dbname'],
                user=cfg['user'],
                password=cfg['password'],
                connect_timeout=5
            )
        return conn
    except Exception as e:
        # PostgreSQL is optional / fallback to SQLite
        return None

def is_postgres_available():
    """بررسی در دسترس بودن سرور PostgreSQL"""
    conn = get_postgres_connection()
    if conn:
        try:
            conn.close()
            return True
        except Exception:
            return False
    return False

# ----------------------------------------------------
# SQLite Connection Management
# ----------------------------------------------------
def get_sqlite_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------------------------------
# Database Initialization (PostgreSQL + SQLite)
# ----------------------------------------------------
def init_db():
    """مقداردهی اولیه جداول در SQLite و در صورت اتصال در PostgreSQL"""
    # ۱. مقداردهی SQLite
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                date_persian TEXT NOT NULL,
                time_str TEXT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                price_18k REAL NOT NULL,
                mesghal REAL,
                price_24k REAL,
                ounce_usd REAL,
                coin_new REAL,
                coin_old REAL,
                half_coin REAL,
                quarter_coin REAL,
                gram_coin REAL,
                source TEXT DEFAULT 'https://www.estjt.ir/',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_aggregates (
                month_key TEXT PRIMARY KEY,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                month_name TEXT NOT NULL,
                label TEXT NOT NULL,
                samples_count INTEGER DEFAULT 0,
                avg_price REAL NOT NULL,
                latest_price REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

    # ۲. در صورت اتصال به PostgreSQL، جداول پیشرفته و نماهای تحلیلی ساخته می‌شوند
    pg_conn = get_postgres_connection()
    if pg_conn:
        try:
            with pg_conn.cursor() as cur:
                # جدول اصلی داده‌های سری زمانی با ایندکس‌های بهینه
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS gold_price_ticks (
                        id BIGSERIAL PRIMARY KEY,
                        recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        date_persian VARCHAR(20) NOT NULL,
                        time_str VARCHAR(10),
                        timestamp_persian VARCHAR(50),
                        year INT NOT NULL,
                        month INT NOT NULL,
                        day INT NOT NULL,
                        price_18k NUMERIC(15, 2) NOT NULL,
                        mesghal NUMERIC(15, 2),
                        price_24k NUMERIC(15, 2),
                        ounce_usd NUMERIC(12, 2),
                        coin_new NUMERIC(15, 2),
                        coin_old NUMERIC(15, 2),
                        half_coin NUMERIC(15, 2),
                        quarter_coin NUMERIC(15, 2),
                        gram_coin NUMERIC(15, 2),
                        spread_mesghal_18k NUMERIC(15, 2),
                        coin_bubble_estimate NUMERIC(15, 2),
                        source VARCHAR(100) DEFAULT 'https://www.estjt.ir/',
                        raw_data JSONB
                    );
                ''')

                # ایندکس‌ها برای کوئری‌های پرسرعت تحلیل سری زمانی
                cur.execute('CREATE INDEX IF NOT EXISTS idx_gold_ticks_time ON gold_price_ticks (recorded_at DESC);')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_gold_ticks_date ON gold_price_ticks (year, month, day);')

                # جدول تجمیع ماهانه
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS monthly_aggregates (
                        month_key VARCHAR(10) PRIMARY KEY,
                        year INT NOT NULL,
                        month INT NOT NULL,
                        month_name VARCHAR(30) NOT NULL,
                        label VARCHAR(50) NOT NULL,
                        samples_count INT DEFAULT 0,
                        avg_price NUMERIC(15, 2) NOT NULL,
                        min_price NUMERIC(15, 2),
                        max_price NUMERIC(15, 2),
                        latest_price NUMERIC(15, 2) NOT NULL,
                        last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                ''')

                # جدول لاگ‌ها
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id BIGSERIAL PRIMARY KEY,
                        event_type VARCHAR(50),
                        message TEXT,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                ''')

                # ۱. نمای تحلیلی OHLC ساعتی (تحلیل تکنیکال درون‌روزی طلا)
                cur.execute('''
                    CREATE OR REPLACE VIEW v_gold_ohlc_hourly AS
                    SELECT 
                        DATE_TRUNC('hour', recorded_at) AS hour_window,
                        date_persian,
                        COUNT(*) AS tick_count,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1] AS open_price,
                        MAX(price_18k) AS high_price,
                        MIN(price_18k) AS low_price,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] AS close_price,
                        ROUND(AVG(price_18k), 0) AS avg_price,
                        MAX(price_18k) - MIN(price_18k) AS spread_price,
                        ROUND(AVG(mesghal), 0) AS avg_mesghal,
                        ROUND(AVG(coin_new), 0) AS avg_coin_new
                    FROM gold_price_ticks
                    GROUP BY DATE_TRUNC('hour', recorded_at), date_persian
                    ORDER BY hour_window DESC;
                ''')

                # ۲. نمای تحلیلی OHLC روزانه (کندل‌های روزانه برای پیش‌بینی و یادگیری ماشین)
                cur.execute('''
                    CREATE OR REPLACE VIEW v_gold_ohlc_daily AS
                    SELECT 
                        date_persian,
                        year,
                        month,
                        day,
                        COUNT(*) AS samples,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1] AS open_price,
                        MAX(price_18k) AS high_price,
                        MIN(price_18k) AS low_price,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] AS close_price,
                        ROUND(AVG(price_18k), 0) AS avg_price,
                        ROUND(AVG(coin_new), 0) AS avg_coin_new,
                        ROUND(AVG(mesghal), 0) AS avg_mesghal
                    FROM gold_price_ticks
                    GROUP BY date_persian, year, month, day
                    ORDER BY year DESC, month DESC, day DESC;
                ''')

                # ۳. نمای تحلیلی نسبت انواع سکه به گرم طلا (تحلیل حباب و تغییرات اسپرد)
                cur.execute('''
                    CREATE OR REPLACE VIEW v_gold_coin_ratios AS
                    SELECT 
                        id,
                        recorded_at,
                        timestamp_persian,
                        price_18k,
                        coin_new,
                        ROUND((coin_new / NULLIF(price_18k, 0)), 2) AS ratio_coin_to_gold_grams,
                        ROUND((coin_old / NULLIF(price_18k, 0)), 2) AS ratio_oldcoin_to_gold_grams,
                        ROUND((half_coin / NULLIF(price_18k, 0)), 2) AS ratio_halfcoin_to_gold_grams,
                        ROUND((quarter_coin / NULLIF(price_18k, 0)), 2) AS ratio_quartercoin_to_gold_grams,
                        spread_mesghal_18k
                    FROM gold_price_ticks
                    ORDER BY recorded_at DESC;
                ''')

                # ۴. نمای تحلیلی میانگین هفتگی (Weekly Aggregates)
                cur.execute('''
                    CREATE OR REPLACE VIEW v_gold_weekly_aggregates AS
                    SELECT 
                        year,
                        CEIL(((month - 1) * 30 + LEAST(day, 30)) / 7.0) AS jalali_week_no,
                        COUNT(*) AS tick_count,
                        MIN(date_persian) AS week_start_date,
                        MAX(date_persian) AS week_end_date,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1] AS open_price,
                        MAX(price_18k) AS high_price,
                        MIN(price_18k) AS low_price,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] AS close_price,
                        ROUND(AVG(price_18k), 0) AS avg_price,
                        ROUND(AVG(mesghal), 0) AS avg_mesghal,
                        ROUND(AVG(coin_new), 0) AS avg_coin_new,
                        ROUND(COALESCE(STDDEV(price_18k), 0), 0) AS weekly_volatility,
                        ROUND(((ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] - (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1]) / NULLIF((ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1], 0) * 100, 2) AS weekly_return_pct
                    FROM gold_price_ticks
                    GROUP BY year, CEIL(((month - 1) * 30 + LEAST(day, 30)) / 7.0)
                    ORDER BY year DESC, jalali_week_no DESC;
                ''')

                # ۵. نمای تحلیلی میانگین ماهانه (Monthly Aggregates)
                cur.execute('''
                    CREATE OR REPLACE VIEW v_gold_monthly_aggregates AS
                    SELECT 
                        year,
                        month,
                        CASE month
                            WHEN 1 THEN 'فروردین' WHEN 2 THEN 'اردیبهشت' WHEN 3 THEN 'خرداد'
                            WHEN 4 THEN 'تیر' WHEN 5 THEN 'مرداد' WHEN 6 THEN 'شهریور'
                            WHEN 7 THEN 'مهر' WHEN 8 THEN 'آبان' WHEN 9 THEN 'آذر'
                            WHEN 10 THEN 'دی' WHEN 11 THEN 'بهمن' WHEN 12 THEN 'اسفند'
                        END AS month_name,
                        COUNT(*) AS tick_count,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1] AS open_price,
                        MAX(price_18k) AS high_price,
                        MIN(price_18k) AS low_price,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] AS close_price,
                        ROUND(AVG(price_18k), 0) AS avg_price,
                        ROUND(AVG(mesghal), 0) AS avg_mesghal,
                        ROUND(AVG(coin_new), 0) AS avg_coin_new,
                        ROUND(COALESCE(STDDEV(price_18k), 0), 0) AS monthly_volatility,
                        ROUND(((ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] - (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1]) / NULLIF((ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1], 0) * 100, 2) AS monthly_return_pct
                    FROM gold_price_ticks
                    GROUP BY year, month
                    ORDER BY year DESC, month DESC;
                ''')

                # ۶. نمای تحلیلی میانگین فصلی (Seasonal Aggregates: بهار، تابستان، پاییز، زمستان)
                cur.execute('''
                    CREATE OR REPLACE VIEW v_gold_seasonal_aggregates AS
                    SELECT 
                        year,
                        CASE 
                            WHEN month BETWEEN 1 AND 3 THEN 'بهار'
                            WHEN month BETWEEN 4 AND 6 THEN 'تابستان'
                            WHEN month BETWEEN 7 AND 9 THEN 'پاییز'
                            ELSE 'زمستان'
                        END AS season_name,
                        CASE 
                            WHEN month BETWEEN 1 AND 3 THEN 1
                            WHEN month BETWEEN 4 AND 6 THEN 2
                            WHEN month BETWEEN 7 AND 9 THEN 3
                            ELSE 4
                        END AS season_order,
                        COUNT(*) AS tick_count,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1] AS open_price,
                        MAX(price_18k) AS high_price,
                        MIN(price_18k) AS low_price,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] AS close_price,
                        ROUND(AVG(price_18k), 0) AS avg_price,
                        ROUND(AVG(mesghal), 0) AS avg_mesghal,
                        ROUND(AVG(coin_new), 0) AS avg_coin_new,
                        ROUND(COALESCE(STDDEV(price_18k), 0), 0) AS seasonal_volatility,
                        ROUND(((ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] - (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1]) / NULLIF((ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1], 0) * 100, 2) AS seasonal_return_pct
                    FROM gold_price_ticks
                    GROUP BY year, 
                        CASE WHEN month BETWEEN 1 AND 3 THEN 'بهار' WHEN month BETWEEN 4 AND 6 THEN 'تابستان' WHEN month BETWEEN 7 AND 9 THEN 'پاییز' ELSE 'زمستان' END,
                        CASE WHEN month BETWEEN 1 AND 3 THEN 1 WHEN month BETWEEN 4 AND 6 THEN 2 WHEN month BETWEEN 7 AND 9 THEN 3 ELSE 4 END
                    ORDER BY year DESC, season_order DESC;
                ''')

                # ۷. نمای تحلیلی میانگین سالانه (Yearly Aggregates)
                cur.execute('''
                    CREATE OR REPLACE VIEW v_gold_yearly_aggregates AS
                    SELECT 
                        year,
                        COUNT(*) AS tick_count,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1] AS year_open_price,
                        MAX(price_18k) AS year_high_price,
                        MIN(price_18k) AS year_low_price,
                        (ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] AS year_close_price,
                        ROUND(AVG(price_18k), 0) AS avg_price,
                        ROUND(AVG(mesghal), 0) AS avg_mesghal,
                        ROUND(AVG(coin_new), 0) AS avg_coin_new,
                        ROUND(COALESCE(STDDEV(price_18k), 0), 0) AS yearly_volatility,
                        ROUND(((ARRAY_AGG(price_18k ORDER BY recorded_at DESC))[1] - (ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1]) / NULLIF((ARRAY_AGG(price_18k ORDER BY recorded_at ASC))[1], 0) * 100, 2) AS yearly_return_pct
                    FROM gold_price_ticks
                    GROUP BY year
                    ORDER BY year DESC;
                ''')

                # ۸. جدول نگهداری میانگین‌های تجمیعی ۴ گانه (هفتگی، ماهانه، فصلی، سالانه)
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS gold_periodic_summary (
                        period_id VARCHAR(50) PRIMARY KEY,
                        period_type VARCHAR(20) NOT NULL,
                        year INT NOT NULL,
                        period_title VARCHAR(50) NOT NULL,
                        tick_count INT DEFAULT 0,
                        open_price NUMERIC(15, 2),
                        high_price NUMERIC(15, 2),
                        low_price NUMERIC(15, 2),
                        close_price NUMERIC(15, 2),
                        avg_price NUMERIC(15, 2) NOT NULL,
                        avg_mesghal NUMERIC(15, 2),
                        avg_coin_new NUMERIC(15, 2),
                        volatility NUMERIC(15, 2),
                        return_pct NUMERIC(8, 2),
                        last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                ''')

                pg_conn.commit()
        except Exception as e:
            print("[PostgreSQL Init Notice]:", e)
        finally:
            pg_conn.close()

# ----------------------------------------------------
# Save Live Price Tick (Writes to PostgreSQL + SQLite)
# ----------------------------------------------------
def save_price_tick(info, jy, jm, jd, timestamp_str, date_str):
    """
    ذخیره تیک قیمت در پایگاه‌داده:
    - در صورت در دسترس بودن PostgreSQL، تیک کامل با تمام متریک‌های تحلیلی در آن ذخیره می‌شود.
    - همزمان در SQLite ذخیره شده و daily_prices.json آپدیت می‌گردد تا عملکرد فرانت‌اند تضمین شود.
    """
    init_db()
    
    price = float(info.get('gold_18k_price', 0))
    mesghal = float(info.get('mesghal_price', 0))
    gold_24k = float(info.get('gold_24k_price', 0))
    ounce_usd = float(info.get('ounce_usd', 0))
    coin_new = float(info.get('coin_new', 0))
    coin_old = float(info.get('coin_old', 0))
    half_coin = float(info.get('half_coin', 0))
    quarter_coin = float(info.get('quarter_coin', 0))
    gram_coin = float(info.get('gram_coin', 0))
    source = info.get('source', 'https://www.estjt.ir/')
    
    now_time = datetime.datetime.now().strftime('%H:%M:%S')
    month_name = MONTHS_ORDER[jm - 1] if 1 <= jm <= 12 else ""
    month_key = f"{jy}-{jm:02d}"
    month_label = f"{month_name} {jy}"

    # محاسبات تحلیلی مالی
    # هر مثقال = ۴.۳۳۱۸ گرم طلای ۱۷ عیار (معادل ۴.۶۰۸ گرم ۱۸ عیار)
    spread_mesghal_18k = round(mesghal - (price * 4.3318), 2) if mesghal and price else 0.0
    
    # وزن سکه امامی: ۸.۱۳۶ گرم با عیار ۹۰۰ (معادل ۸.۲۶ گرم ۱۸ عیار)
    coin_intrinsic_gold = price * 8.26 if price else 0.0
    coin_bubble_estimate = round(coin_new - coin_intrinsic_gold, 2) if coin_new and coin_intrinsic_gold else 0.0

    # ۱. ذخیره در PostgreSQL (در صورت اتصال)
    pg_saved = False
    pg_conn = get_postgres_connection()
    if pg_conn:
        try:
            with pg_conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO gold_price_ticks (
                        date_persian, time_str, timestamp_persian, year, month, day,
                        price_18k, mesghal, price_24k, ounce_usd,
                        coin_new, coin_old, half_coin, quarter_coin, gram_coin,
                        spread_mesghal_18k, coin_bubble_estimate, source, raw_data
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    date_str, now_time, timestamp_str, jy, jm, jd,
                    price, mesghal, gold_24k, ounce_usd,
                    coin_new, coin_old, half_coin, quarter_coin, gram_coin,
                    spread_mesghal_18k, coin_bubble_estimate, source, Json(info)
                ))

                # محاسبه آمار ماهانه در PostgreSQL
                cur.execute('''
                    SELECT COUNT(*), AVG(price_18k), MIN(price_18k), MAX(price_18k)
                    FROM gold_price_ticks
                    WHERE year = %s AND month = %s
                ''', (jy, jm))
                row = cur.fetchone()
                pg_count = row[0] if row else 1
                pg_avg = round(row[1]) if row and row[1] else round(price)
                pg_min = round(row[2]) if row and row[2] else round(price)
                pg_max = round(row[3]) if row and row[3] else round(price)

                # آپدیت جدول ماهانه PostgreSQL
                cur.execute('''
                    INSERT INTO monthly_aggregates (
                        month_key, year, month, month_name, label, samples_count,
                        avg_price, min_price, max_price, latest_price, last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT(month_key) DO UPDATE SET
                        samples_count = EXCLUDED.samples_count,
                        avg_price = EXCLUDED.avg_price,
                        min_price = EXCLUDED.min_price,
                        max_price = EXCLUDED.max_price,
                        latest_price = EXCLUDED.latest_price,
                        last_updated = CURRENT_TIMESTAMP
                ''', (month_key, jy, jm, month_name, month_label, pg_count, pg_avg, pg_min, pg_max, price))

                cur.execute('''
                    INSERT INTO system_logs (event_type, message)
                    VALUES ('PG_TICK_SAVED', %s)
                ''', (f"ثبت نرخ {price:,.0f} تومان در PostgreSQL (تعداد نمونه: {pg_count})",))

                pg_conn.commit()
                pg_saved = True
        except Exception as e:
            print("[PostgreSQL Save Error]:", e)
        finally:
            pg_conn.close()

    # ۲. ذخیره در SQLite به عنوان پشتیبان دائمی و آفلاین
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO price_ticks (
                timestamp, date_persian, time_str, year, month, day,
                price_18k, mesghal, price_24k, ounce_usd,
                coin_new, coin_old, half_coin, quarter_coin, gram_coin, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp_str, date_str, now_time, jy, jm, jd,
            price, mesghal, gold_24k, ounce_usd,
            coin_new, coin_old, half_coin, quarter_coin, gram_coin, source
        ))
        
        cursor.execute('''
            SELECT COUNT(*), AVG(price_18k)
            FROM price_ticks
            WHERE year = ? AND month = ?
        ''', (jy, jm))
        count_row = cursor.fetchone()
        samples_count = count_row[0] if count_row else 1
        avg_price = round(count_row[1]) if count_row and count_row[1] else round(price)
        
        cursor.execute('''
            INSERT INTO monthly_aggregates (
                month_key, year, month, month_name, label, samples_count, avg_price, latest_price, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(month_key) DO UPDATE SET
                samples_count = excluded.samples_count,
                avg_price = excluded.avg_price,
                latest_price = excluded.latest_price,
                last_updated = CURRENT_TIMESTAMP
        ''', (month_key, jy, jm, month_name, month_label, samples_count, avg_price, price))
        
        conn.commit()

    # ۳. بروزرسانی daily_prices.json برای فرانت‌اند
    sync_to_daily_json()
    
    return {
        "samples_count": samples_count,
        "avg_price": avg_price,
        "latest_price": price,
        "postgres_saved": pg_saved
    }

def sync_to_daily_json():
    """تولید daily_prices.json از روی بانک اطلاعاتی"""
    try:
        init_db()
        with get_sqlite_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, date_persian, year, month, day, price_18k, mesghal, coin_new
                FROM price_ticks
                ORDER BY id DESC
                LIMIT 200
            ''')
            rows = cursor.fetchall()
            ticks = []
            for r in rows:
                m_idx = r['month']
                m_name = MONTHS_ORDER[m_idx - 1] if 1 <= m_idx <= 12 else ""
                ticks.append({
                    "timestamp": r['timestamp'],
                    "date": r['date_persian'],
                    "year": r['year'],
                    "month": r['month'],
                    "month_name": m_name,
                    "day": r['day'],
                    "price": r['price_18k'],
                    "mesghal": r['mesghal'],
                    "coin_new": r['coin_new']
                })
                
            cursor.execute('''
                SELECT month_key, year, month, month_name, label, samples_count, avg_price, latest_price
                FROM monthly_aggregates
            ''')
            agg_rows = cursor.fetchall()
            aggregates = {}
            for ar in agg_rows:
                aggregates[ar['month_key']] = {
                    "year": ar['year'],
                    "month": ar['month'],
                    "month_name": ar['month_name'],
                    "label": ar['label'],
                    "samples_count": ar['samples_count'],
                    "avg_price": ar['avg_price'],
                    "latest_price": ar['latest_price']
                }
                
            last_sync = ticks[0]['timestamp'] if ticks else ""
            
            store = {
                "ticks": ticks,
                "monthly_aggregates": aggregates,
                "last_sync": last_sync,
                "total_db_records": len(ticks)
            }
            
            with open('daily_prices.json', 'w', encoding='utf-8') as f:
                json.dump(store, f, ensure_ascii=False, indent=2)
                
    except Exception as e:
        print("[Database Sync Error]:", e)

def get_stats():
    """دریافت وضعیت آماری بانک‌های داده"""
    init_db()
    stats = {}
    
    # SQLite Stats
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM price_ticks")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM price_ticks")
        first_last = cursor.fetchone()
        db_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        stats["sqlite"] = {
            "total_ticks": count,
            "first_record": first_last[0] if first_last else None,
            "last_record": first_last[1] if first_last else None,
            "db_size_kb": round(db_size_bytes / 1024, 2)
        }
        stats["total_ticks"] = count
        stats["db_size_kb"] = round(db_size_bytes / 1024, 2)

    # PostgreSQL Stats (if available)
    pg_conn = get_postgres_connection()
    if pg_conn:
        try:
            with pg_conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM gold_price_ticks;")
                pg_count = cur.fetchone()[0]
                cur.execute("SELECT MIN(recorded_at), MAX(recorded_at) FROM gold_price_ticks;")
                pg_dates = cur.fetchone()
                stats["postgres"] = {
                    "connected": True,
                    "total_ticks": pg_count,
                    "first_record": str(pg_dates[0]) if pg_dates and pg_dates[0] else None,
                    "last_record": str(pg_dates[1]) if pg_dates and pg_dates[1] else None
                }
        except Exception as e:
            stats["postgres"] = {"connected": False, "error": str(e)}
        finally:
            pg_conn.close()
    else:
        stats["postgres"] = {"connected": False, "status": "Not configured or offline"}

    return stats

# ----------------------------------------------------
# Data Migration from SQLite to PostgreSQL
# ----------------------------------------------------
def migrate_sqlite_to_postgres():
    """انتقال تمام رکوردهای تاریخی ثبت‌شده در SQLite به PostgreSQL"""
    init_db()
    pg_conn = get_postgres_connection()
    if not pg_conn:
        return {"success": False, "error": "PostgreSQL connection not available. Please check .env or DATABASE_URL."}
    
    migrated_count = 0
    try:
        with get_sqlite_connection() as s_conn:
            s_cur = s_conn.cursor()
            s_cur.execute('''
                SELECT timestamp, date_persian, time_str, year, month, day,
                       price_18k, mesghal, price_24k, ounce_usd,
                       coin_new, coin_old, half_coin, quarter_coin, gram_coin,
                       source, created_at
                FROM price_ticks
                ORDER BY id ASC
            ''')
            rows = s_cur.fetchall()

            with pg_conn.cursor() as pg_cur:
                for r in rows:
                    price = r['price_18k']
                    mesghal = r['mesghal'] or 0
                    coin = r['coin_new'] or 0
                    spread = round(mesghal - (price * 4.3318), 2) if mesghal and price else 0
                    bubble = round(coin - (price * 8.26), 2) if coin and price else 0

                    pg_cur.execute('''
                        INSERT INTO gold_price_ticks (
                            recorded_at, date_persian, time_str, timestamp_persian,
                            year, month, day, price_18k, mesghal, price_24k, ounce_usd,
                            coin_new, coin_old, half_coin, quarter_coin, gram_coin,
                            spread_mesghal_18k, coin_bubble_estimate, source
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        r['created_at'], r['date_persian'], r['time_str'], r['timestamp'],
                        r['year'], r['month'], r['day'], price, r['mesghal'], r['price_24k'], r['ounce_usd'],
                        r['coin_new'], r['coin_old'], r['half_coin'], r['quarter_coin'], r['gram_coin'],
                        spread, bubble, r['source']
                    ))
                    migrated_count += 1
                
                pg_conn.commit()

        return {"success": True, "migrated_records": migrated_count}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        pg_conn.close()

if __name__ == '__main__':
    init_db()
    print("بانک‌های داده مقداردهی شدند.")
    print("آمار جاری:", json.dumps(get_stats(), ensure_ascii=False, indent=2))
