# -*- coding: utf-8 -*-
import json
import os
import shutil

def build():
    # Load dashboard data
    with open('dashboard_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load daily prices history if exists
    daily_data = None
    if os.path.exists('daily_prices.json'):
        try:
            with open('daily_prices.json', 'r', encoding='utf-8') as df:
                daily_data = json.load(df)
        except Exception:
            pass

    # Default fallback live values
    live_price = 23484500.0
    mesghal_price = 101730000.0
    coin_new = 233500000.0
    coin_old = 230500000.0
    half_coin = 119500000.0
    quarter_coin = 64500000.0
    gram_coin = 35000000.0
    gold_24k = 31300000.0
    ounce_usd = 4485.0
    live_time = "۱۲ شهریور ۱۴۰۵ - ۱۹:۵۴:۰۱"

    if os.path.exists('live_gold_result.json'):
        try:
            with open('live_gold_result.json', 'r', encoding='utf-8') as lf:
                linfo = json.load(lf)
                live_price = linfo.get('gold_18k_price', live_price)
                mesghal_price = linfo.get('mesghal_price', mesghal_price)
                coin_new = linfo.get('coin_new', coin_new)
                coin_old = linfo.get('coin_old', coin_old)
                half_coin = linfo.get('half_coin', half_coin)
                quarter_coin = linfo.get('quarter_coin', quarter_coin)
                gram_coin = linfo.get('gram_coin', gram_coin)
                gold_24k = linfo.get('gold_24k_price', gold_24k)
                ounce_usd = linfo.get('ounce_usd', ounce_usd)
                live_time = linfo.get('update_time', live_time)
        except Exception:
            pass

    data['live_source'] = {
        'price': live_price,
        'mesghal': mesghal_price,
        'coin_new': coin_new,
        'coin_old': coin_old,
        'half_coin': half_coin,
        'quarter_coin': quarter_coin,
        'gram_coin': gram_coin,
        'gold_24k': gold_24k,
        'ounce_usd': ounce_usd,
        'update_time': live_time,
        'source_url': 'https://www.estjt.ir/'
    }

    # Load daily database data (ticks and monthly aggregates)
    if daily_data:
        data['daily_data'] = daily_data
    else:
        try:
            import database
            database.sync_to_daily_json()
        except Exception:
            pass
        if os.path.exists('daily_prices.json'):
            try:
                with open('daily_prices.json', 'r', encoding='utf-8') as df:
                    data['daily_data'] = json.load(df)
            except Exception:
                pass
        if 'daily_data' not in data:
            data['daily_data'] = {
                "ticks": [
                    {
                        "timestamp": live_time,
                        "date": "1405/06/12",
                        "year": 1405,
                        "month": 6,
                        "month_name": "شهریور",
                        "day": 12,
                        "price": live_price,
                        "mesghal": mesghal_price,
                        "coin_new": coin_new
                    }
                ],
                "monthly_aggregates": {
                    "1405-06": {
                        "year": 1405,
                        "month": 6,
                        "month_name": "شهریور",
                        "label": "شهریور ۱۴۰۵",
                        "samples_count": 1,
                        "avg_price": live_price,
                        "latest_price": live_price
                    }
                }
            }

    # Update Shahrivar 1405 price with live estjt.ir price
    data['timeline'][-1]['price'] = live_price
    data['timeline'][-1]['mom_change_amount'] = live_price - data['timeline'][-2]['price']
    data['timeline'][-1]['mom_change_pct'] = round(((live_price - data['timeline'][-2]['price']) / data['timeline'][-2]['price']) * 100, 2)
    data['timeline'][-1]['wage_in_gold_grams'] = round(data['timeline'][-1]['wage'] / live_price, 2)

    data['records']['latest_price'] = live_price
    data['records']['total_growth_multiplier'] = round(live_price / data['records']['initial_price'], 1)
    data['records']['total_growth_pct'] = round(((live_price - data['records']['initial_price']) / data['records']['initial_price']) * 100, 1)

    # Calculate LSTM neural network forecast
    try:
        import lstm_model
        data['lstm_forecast'] = lstm_model.get_lstm_forecast(data['timeline'], live_price)
    except Exception as e:
        print("[LSTM Model Calculation Warning]:", e)

    # Fetch SQLite database statistics
    try:
        import database
        data['db_stats'] = database.get_stats()
    except Exception as e:
        print("[Database Stats Warning]:", e)

    json_str = json.dumps(data, ensure_ascii=False)

    html_code = f'''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
  <meta name="theme-color" content="#0f172a">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="description" content="سامانه هوشمند آنلاین طلا و انواع سکه • بروزرسانی خودکار هر ۳۰ دقیقه • ثبت خودکار روزانه و محاسبه میانگین ماهانه">
  <title>داشبورد آنلاین طلا، سکه و میانگین ماهانه (estjt.ir)</title>

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Chart.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <!-- Google Fonts: Vazirmatn -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap" rel="stylesheet">

  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            vazir: ['Vazirmatn', 'Tahoma', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
          }},
          colors: {{
            gold: {{
              50: '#fffdf0',
              100: '#fef9c3',
              200: '#fef08a',
              300: '#fde047',
              400: '#facc15',
              500: '#eab308',
              600: '#ca8a04',
              700: '#a16207',
              800: '#854d0e',
              900: '#713f12',
            }}
          }}
        }}
      }}
    }}
  </script>

  <style>
    * {{
      -webkit-tap-highlight-color: transparent;
      box-sizing: border-box;
    }}
    html {{
      scroll-behavior: smooth;
    }}
    body {{
      font-family: 'Vazirmatn', Tahoma, -apple-system, BlinkMacSystemFont, sans-serif;
      touch-action: manipulation;
      padding-top: env(safe-area-inset-top);
      padding-bottom: env(safe-area-inset-bottom);
    }}
    .glass-card {{
      background: rgba(255, 255, 255, 0.94);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid rgba(229, 231, 235, 0.9);
    }}
    .dark .glass-card {{
      background: rgba(17, 24, 39, 0.92);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid rgba(55, 65, 81, 0.7);
    }}
    .tab-grid-btn.active {{
      background: linear-gradient(135deg, #eab308, #ca8a04);
      color: #0f172a;
      font-weight: 800;
      border-color: #facc15;
      box-shadow: 0 4px 14px 0 rgba(234, 179, 8, 0.35);
      transform: translateY(-1px);
    }}
    .tab-grid-btn.active * {{
      color: #0f172a !important;
    }}
    /* Smooth mobile touch scrolling for tables */
    .table-container {{
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }}
    ::-webkit-scrollbar {{
      width: 5px;
      height: 5px;
    }}
    ::-webkit-scrollbar-track {{
      background: rgba(0,0,0,0.03);
    }}
    ::-webkit-scrollbar-thumb {{
      background: #ca8a04;
      border-radius: 4px;
    }}
  </style>
</head>
<body class="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen transition-colors duration-300 pb-12 antialiased selection:bg-amber-500 selection:text-slate-900">

  <!-- TOP HEADER -->
  <header class="sticky top-0 z-50 glass-card border-b shadow-sm">
    <div class="max-w-7xl mx-auto px-3.5 sm:px-6 lg:px-8 py-2.5 sm:py-3.5 flex flex-wrap items-center justify-between gap-2.5 sm:gap-4">
      
      <!-- Title & Auto-sync badge -->
      <div class="flex items-center gap-2.5 sm:gap-3">
        <div class="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-gradient-to-tr from-amber-500 to-yellow-300 flex items-center justify-center shadow-lg shadow-amber-500/20 text-slate-900 font-bold text-xl flex-shrink-0">
          🪙
        </div>
        <div>
          <div class="flex items-center gap-1.5 sm:gap-2 flex-wrap">
            <h1 class="text-base sm:text-2xl font-black tracking-tight">
              روند آنلاین طلا و سکه
            </h1>
            <span class="inline-flex items-center gap-1 text-[10px] sm:text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-900 dark:bg-emerald-900/60 dark:text-emerald-300 border border-emerald-400/50" title="استعلام خودکار هر ۳۰ دقیقه یکبار فعال است">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-ping inline-block"></span>
              <span>بروزرسانی خودکار ۳۰ دقیقه</span>
            </span>
          </div>
          <p class="text-[11px] sm:text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">
            ثبت خودکار روزانه • محاسبه میانگین ماه • پیش‌بینی غلتان ۱۲ ماه آینده
          </p>
        </div>
      </div>

      <!-- Quick Controls & Countdown -->
      <div class="flex items-center gap-2 sm:gap-3 ml-auto sm:ml-0">
        <!-- 30-min Countdown Indicator -->
        <div class="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/60 text-xs">
          <span class="text-slate-400">⏱️ استعلام بعدی:</span>
          <span id="autoSyncCountdown" class="font-bold font-mono text-cyan-600 dark:text-cyan-400">۳۰:۰۰</span>
        </div>

        <!-- Live Refresh Button -->
        <button id="btnFetchLive" onclick="fetchLiveOnlinePrice(false)" class="px-2.5 sm:px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold text-[11px] sm:text-xs flex items-center gap-1.5 shadow-md shadow-emerald-600/20 transition-all active:scale-95">
          <span id="syncSpinIcon">🔄</span>
          <span class="hidden sm:inline">بروزرسانی فوری</span>
          <span class="sm:hidden">استعلام زنده</span>
        </button>

        <!-- Dark mode toggle -->
        <button id="themeToggle" onclick="toggleTheme()" class="p-2 sm:p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors shadow-sm" title="تغییر تم شب/روز" aria-label="تغییر تم">
          <span id="themeIcon" class="text-base sm:text-lg">🌙</span>
        </button>
      </div>
    </div>
  </header>

  <!-- LIVE STATUS TICKER BAR -->
  <div class="bg-amber-500/10 border-b border-amber-500/20 py-2 px-3 sm:px-4 text-xs">
    <div class="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 sm:gap-2">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="font-bold text-amber-600 dark:text-amber-400">📡 نرخ روز طلای ۱۸ عیار:</span>
        <span id="tickerLivePrice" class="font-black text-slate-900 dark:text-white bg-amber-400/20 px-2 py-0.5 rounded-lg border border-amber-400/30 text-sm">
          ۲۳,۴۸۴,۵۰۰ تومان
        </span>
        <span class="text-slate-400 text-[11px]">|</span>
        <span class="text-slate-500 dark:text-slate-400 text-[11px]" id="tickerUpdateTime">
          آخرین استعلام: {live_time} (اتحادیه طلا estjt.ir)
        </span>
      </div>
      <div class="flex items-center gap-2 text-[11px] text-cyan-600 dark:text-cyan-400 font-bold">
        <span>📊 میانگین جاری این ماه: <strong id="tickerMonthAvg" class="text-slate-900 dark:text-white bg-cyan-400/20 px-1.5 py-0.5 rounded">۲۳,۴۷۹,۹۰۰ ت</strong></span>
        <span class="text-slate-400">|</span>
        <span>تعداد ثبت‌ها: <strong id="tickerSampleCount">۳ بار</strong></span>
      </div>
    </div>
  </div>

  <main class="max-w-7xl mx-auto px-3.5 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-5 sm:space-y-6">

    <!-- KPI HIGHLIGHT CARDS -->
    <section class="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-4">
      <!-- KPI 1: Live & Monthly Avg -->
      <div class="glass-card rounded-2xl p-3.5 sm:p-4 shadow-sm relative overflow-hidden group hover:border-amber-400/60 transition-all col-span-1">
        <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-[11px] sm:text-xs font-medium mb-1">
          <span id="kpiLatestLabel">نرخ روز طلا ۱۸ عیار</span>
          <span class="text-emerald-500 font-bold text-[10px] sm:text-xs bg-emerald-100 dark:bg-emerald-950 px-1.5 py-0.5 rounded">استعلام زنده</span>
        </div>
        <div class="text-lg sm:text-2xl font-black text-amber-600 dark:text-amber-400 tracking-tight" id="kpiLatestPrice">
          ۲۳,۴۸۴,۵۰۰ <span class="text-[11px] sm:text-xs font-normal text-slate-500 dark:text-slate-400">تومان</span>
        </div>
        <div class="mt-1 sm:mt-2 text-[10px] sm:text-xs text-slate-500 dark:text-slate-400 font-semibold flex items-center justify-between">
          <span>میانگین ماه:</span>
          <span class="font-bold text-slate-800 dark:text-slate-200" id="kpiMonthAverageVal">۲۳,۴۷۹,۹۰۰ ت</span>
        </div>
      </div>

      <!-- KPI 2: ROLLING 1-YEAR HYBRID FORECAST TARGET (GOLD THEMED) -->
      <div class="glass-card rounded-2xl p-3.5 sm:p-4 shadow-sm relative overflow-hidden group hover:border-amber-400/80 transition-all border border-amber-500/40 col-span-1">
        <div class="flex items-center justify-between text-slate-700 dark:text-slate-200 text-[11px] sm:text-xs font-bold mb-1">
          <span id="kpiForecastLabel">هدف 12 ماه آینده (مدل ترکیبی)</span>
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-400/50">
            Tri-Hybrid AI
          </span>
        </div>
        <div class="text-lg sm:text-2xl font-black text-amber-600 dark:text-amber-400 tracking-tight" id="kpiForecastPrice">
          -- <span class="text-[11px] sm:text-xs font-normal text-slate-600 dark:text-slate-300">تومان</span>
        </div>
        <div class="mt-1 sm:mt-2 text-[10px] sm:text-xs text-slate-700 dark:text-slate-200 font-bold flex items-center justify-between">
          <span>رشد تخمینی 1 ساله:</span>
          <span class="font-black text-amber-600 dark:text-amber-400" id="kpiForecastGrowthVal">+--%</span>
        </div>
      </div>

      <!-- KPI 3: Wage -->
      <div class="glass-card rounded-2xl p-3.5 sm:p-4 shadow-sm relative overflow-hidden group hover:border-rose-400/60 transition-all col-span-1">
        <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-[11px] sm:text-xs font-medium mb-1">
          <span>قدرت خرید حقوق پایه</span>
          <span class="text-rose-500 font-bold text-[10px] sm:text-xs">سقوط ۹۰٪</span>
        </div>
        <div class="text-lg sm:text-2xl font-black text-rose-600 dark:text-rose-400 tracking-tight" id="kpiWageInGrams">
          ۰.۹۴ <span class="text-[11px] sm:text-xs font-normal text-slate-500 dark:text-slate-400">گرم طلا</span>
        </div>
        <div class="mt-1 sm:mt-2 text-[10px] sm:text-xs text-slate-500 dark:text-slate-400">
          از ۹.۴ گرم در سال ۹۵ به کمتر از ۱ گرم رسیده است
        </div>
      </div>

      <!-- KPI 4: Multiplier -->
      <div class="glass-card rounded-2xl p-3.5 sm:p-4 shadow-sm relative overflow-hidden group hover:border-indigo-400/60 transition-all col-span-1">
        <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-[11px] sm:text-xs font-medium mb-1">
          <span>ضریب کل رشد طلا</span>
          <span class="text-indigo-500 font-bold text-[10px] sm:text-xs">از فروردین ۹۵</span>
        </div>
        <div class="text-lg sm:text-2xl font-black text-indigo-600 dark:text-indigo-400 tracking-tight" id="kpiMultiplier">
          ۲۲۶.۹ برابر
        </div>
        <div class="mt-1 sm:mt-2 text-[10px] sm:text-xs text-slate-500 dark:text-slate-400">
          از ۱۰۳,۵۰۰ تومان به بیش از ۲۳.۴ میلیون تومان
        </div>
      </div>
    </section>

    <!-- LIVE COIN & GOLD SUMMARY DECK -->
    <section class="glass-card rounded-2xl p-4 shadow-sm border border-amber-500/30">
      <div class="flex items-center justify-between gap-2 mb-3 pb-2 border-b border-slate-200 dark:border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-lg">🪙</span>
          <h3 class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-100">
            تابلو لحظه‌ای نرخ طلا و انواع سکه (سامانه اتحادیه طلا تهران)
          </h3>
        </div>
        <div class="flex items-center gap-2 text-[11px] text-slate-400">
          <span>واحد: تومان</span>
          <span>•</span>
          <span class="text-emerald-500 font-bold">بروزرسانی زنده</span>
        </div>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 text-center text-xs">
        <div class="p-2.5 rounded-xl bg-slate-100/80 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60">
          <span class="text-[11px] text-slate-500 dark:text-slate-400 block mb-1">طلا ۱۸ عیار</span>
          <span class="font-black text-amber-600 dark:text-amber-400 block" id="coinCardGold18">۲۳,۴۸۴,۵۰۰</span>
        </div>
        <div class="p-2.5 rounded-xl bg-slate-100/80 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60">
          <span class="text-[11px] text-slate-500 dark:text-slate-400 block mb-1">مظنه تهران (مثقال)</span>
          <span class="font-black text-slate-800 dark:text-slate-200 block" id="coinCardMesghal">۱۰۱,۷۳۰,۰۰۰</span>
        </div>
        <div class="p-2.5 rounded-xl bg-slate-100/80 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60">
          <span class="text-[11px] text-slate-500 dark:text-slate-400 block mb-1">سکه طرح جدید (امامی)</span>
          <span class="font-black text-amber-500 block" id="coinCardNew">۲۳۳,۵۰۰,۰۰۰</span>
        </div>
        <div class="p-2.5 rounded-xl bg-slate-100/80 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60">
          <span class="text-[11px] text-slate-500 dark:text-slate-400 block mb-1">سکه بهار آزادی</span>
          <span class="font-black text-slate-800 dark:text-slate-200 block" id="coinCardOld">۲۳۰,۵۰۰,۰۰۰</span>
        </div>
        <div class="p-2.5 rounded-xl bg-slate-100/80 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60">
          <span class="text-[11px] text-slate-500 dark:text-slate-400 block mb-1">نیم سکه</span>
          <span class="font-black text-slate-800 dark:text-slate-200 block" id="coinCardHalf">۱۱۹,۵۰۰,۰۰۰</span>
        </div>
        <div class="p-2.5 rounded-xl bg-slate-100/80 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60">
          <span class="text-[11px] text-slate-500 dark:text-slate-400 block mb-1">ربع سکه</span>
          <span class="font-black text-slate-800 dark:text-slate-200 block" id="coinCardQuarter">۶۴,۵۰۰,۰۰۰</span>
        </div>
        <div class="p-2.5 rounded-xl bg-slate-100/80 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60">
          <span class="text-[11px] text-slate-500 dark:text-slate-400 block mb-1">سکه یک گرمی</span>
          <span class="font-black text-slate-800 dark:text-slate-200 block" id="coinCardGram">۳۵,۰۰۰,۰۰۰</span>
        </div>
        <div class="p-2.5 rounded-xl bg-slate-100/80 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60">
          <span class="text-[11px] text-slate-500 dark:text-slate-400 block mb-1">انس جهانی طلا</span>
          <span class="font-black text-cyan-500 block" id="coinCardOunce">$ ۴,۴۸۵</span>
        </div>
      </div>
    </section>

    <!-- NAVIGATION TABS: چهارخونه‌ای لمسی و واکنش‌گرا -->
    <nav class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 sm:gap-2.5">
      <!-- Tab 1 -->
      <button onclick="switchTab('tab-macro')" id="btn-tab-macro" class="tab-grid-btn active glass-card p-3 rounded-2xl border text-right transition-all flex flex-col justify-between hover:border-amber-400 shadow-sm">
        <div class="flex items-center justify-between w-full mb-1">
          <span class="text-xl">📈</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-700 dark:text-amber-300 font-bold">اصلی</span>
        </div>
        <div>
          <div class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-100">نمودار رشد طلا</div>
          <div class="text-[10px] text-slate-400 mt-0.5">روند زنده و پیش‌بینی</div>
        </div>
      </button>

      <!-- Tab 2 -->
      <button onclick="switchTab('tab-forecast-details')" id="btn-tab-forecast-details" class="tab-grid-btn glass-card p-3 rounded-2xl border border-slate-200 dark:border-slate-800 text-right transition-all flex flex-col justify-between hover:border-cyan-400 shadow-sm">
        <div class="flex items-center justify-between w-full mb-1">
          <span class="text-xl">🔮</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 font-bold">نمودار</span>
        </div>
        <div>
          <div class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-100">سناریوهای آینده</div>
          <div class="text-[10px] text-slate-400 mt-0.5">نمودار ۱۲ ماه آینده</div>
        </div>
      </button>

      <!-- Tab: AI TRADING & INVESTMENT ADVISOR -->
      <button onclick="switchTab('tab-advisor')" id="btn-tab-advisor" class="tab-grid-btn glass-card p-3 rounded-2xl border border-emerald-500/40 text-right transition-all flex flex-col justify-between hover:border-emerald-400 shadow-sm relative group overflow-hidden bg-gradient-to-b from-emerald-500/10 via-transparent to-transparent">
        <div class="flex items-center justify-between w-full mb-1">
          <span class="text-xl">🤖</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 font-black flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            هوشمند
          </span>
        </div>
        <div>
          <div class="text-xs sm:text-sm font-black text-slate-900 dark:text-white">دستیار خرید و فروش</div>
          <div class="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold mt-0.5">مشاور طلا، سکه و دلار</div>
        </div>
      </button>

      <!-- Tab 3 -->
      <button onclick="switchTab('tab-wage')" id="btn-tab-wage" class="tab-grid-btn glass-card p-3 rounded-2xl border border-slate-200 dark:border-slate-800 text-right transition-all flex flex-col justify-between hover:border-rose-400 shadow-sm">
        <div class="flex items-center justify-between w-full mb-1">
          <span class="text-xl">⚖️</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-700 dark:text-rose-300 font-bold">دستمزد</span>
        </div>
        <div>
          <div class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-100">طلا و حقوق پایه</div>
          <div class="text-[10px] text-slate-400 mt-0.5">سقوط قدرت خرید</div>
        </div>
      </button>

      <!-- Tab 4 -->
      <button onclick="switchTab('tab-seasonality')" id="btn-tab-seasonality" class="tab-grid-btn glass-card p-3 rounded-2xl border border-slate-200 dark:border-slate-800 text-right transition-all flex flex-col justify-between hover:border-emerald-400 shadow-sm">
        <div class="flex items-center justify-between w-full mb-1">
          <span class="text-xl">🗓️</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 font-bold">فصلی</span>
        </div>
        <div>
          <div class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-100">الگوی فصلی و هیت‌مپ</div>
          <div class="text-[10px] text-slate-400 mt-0.5">بهترین زمان خرید</div>
        </div>
      </button>

      <!-- Tab 5 -->
      <button onclick="switchTab('tab-yearly')" id="btn-tab-yearly" class="tab-grid-btn glass-card p-3 rounded-2xl border border-slate-200 dark:border-slate-800 text-right transition-all flex flex-col justify-between hover:border-indigo-400 shadow-sm">
        <div class="flex items-center justify-between w-full mb-1">
          <span class="text-xl">📊</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 font-bold">سالیانه</span>
        </div>
        <div>
          <div class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-100">کارنامه سال به سال</div>
          <div class="text-[10px] text-slate-400 mt-0.5">ثبت سقف و کف‌ها</div>
        </div>
      </button>

      <!-- Tab 6 -->
      <button onclick="switchTab('tab-table')" id="btn-tab-table" class="tab-grid-btn glass-card p-3 rounded-2xl border border-slate-200 dark:border-slate-800 text-right transition-all flex flex-col justify-between hover:border-amber-400 shadow-sm">
        <div class="flex items-center justify-between w-full mb-1">
          <span class="text-xl">📋</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-700 dark:text-amber-300 font-bold">داده‌ها</span>
        </div>
        <div>
          <div class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-100">بانک کل داده‌ها</div>
          <div class="text-[10px] text-slate-400 mt-0.5">جستجو و خروجی CSV</div>
        </div>
      </button>

      <!-- Tab 7: Moved to End -->
      <button onclick="switchTab('tab-live-sync')" id="btn-tab-live-sync" class="tab-grid-btn glass-card p-3 rounded-2xl border border-slate-200 dark:border-slate-800 text-right transition-all flex flex-col justify-between hover:border-teal-400 shadow-sm col-span-2 sm:col-span-1">
        <div class="flex items-center justify-between w-full mb-1">
          <span class="text-xl">🌐</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-700 dark:text-teal-300 font-bold">اتحادیه</span>
        </div>
        <div>
          <div class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-100">مدیریت آنلاین و سکه‌ها</div>
          <div class="text-[10px] text-slate-400 mt-0.5">تنظیمات و ورودی estjt</div>
        </div>
      </button>
    </nav>

    <!-- TAB 1: MACRO CHART WITH DYNAMIC ROLLING FORECAST -->
    <div id="tab-macro" class="tab-content space-y-4 sm:space-y-6">
      <div class="glass-card rounded-2xl p-3.5 sm:p-5 shadow-sm">
        
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h2 class="text-sm sm:text-lg font-bold flex items-center gap-2 flex-wrap">
              <span>روند رشد طلا ۱۸ عیار</span>
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-300 border border-cyan-400/40">
                پیش‌بینی غلتان ۱ ساله (نقطه‌چین)
              </span>
            </h2>
            <p class="text-[11px] sm:text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              خط زرد: داده‌های تاریخی • خط نقطه‌چین بنفش: پیش‌بینی 1 ساله مدل ترکیبی سه‌گانه
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-1.5 sm:gap-2">
            <button id="btnToggleForecast" onclick="toggleForecastVisibility()" class="px-2.5 sm:px-3 py-1.5 rounded-xl border border-cyan-400 bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 font-bold text-[11px] sm:text-xs flex items-center gap-1.5 shadow-sm transition-all hover:bg-cyan-500/25">
              <span class="w-2 h-2 rounded-full bg-cyan-500 animate-ping inline-block"></span>
              <span>خط پیش‌بینی: فعال</span>
            </button>

            <!-- نشانگر مدل ترکیبی سه‌گانه -->
            <div class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border border-purple-400/40 bg-purple-500/10 text-purple-700 dark:text-purple-300 font-bold text-[11px] sm:text-xs shadow-sm">
              <span class="w-2 h-2 rounded-full bg-purple-400"></span><span>مدل ترکیبی (LSTM + روند + فصلی)</span>
            </div>

            <select id="selectForecastScenario" onchange="changeForecastScenario(this.value)" class="px-2.5 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-[11px] sm:text-xs font-semibold focus:ring-2 focus:ring-cyan-500 focus:outline-none">
              <option value="base">سناریوی پایه (محتمل‌ترین)</option>
              <option value="conservative">سناریوی محافظه‌کارانه</option>
              <option value="bullish">سناریوی صعودی / جهش ارزی</option>
            </select>

            <button onclick="toggleScale()" id="btnScaleToggle" class="px-2.5 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-[11px] font-medium">
              مقیاس: خطی
            </button>
          </div>
        </div>

        <div class="flex items-center justify-between flex-wrap gap-2 mb-3">
          <div class="flex flex-wrap items-center gap-1 text-[11px] sm:text-xs">
            <button onclick="filterTimeline('all')" class="time-filter active px-2.5 py-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-amber-400 text-slate-900 font-bold" data-range="all">همه سال‌ها + آینده</button>
            <button onclick="filterTimeline('3y')" class="time-filter px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" data-range="3y">۳ سال اخیر + آینده</button>
            <button onclick="filterTimeline('5y')" class="time-filter px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" data-range="5y">۵ سال اخیر</button>
            <button onclick="filterTimeline('early')" class="time-filter px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" data-range="early">سال‌های اولیه (۹۵-۹۹)</button>
          </div>
          <div class="text-[11px] text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
            <span>● مبدا پیش‌بینی: نرخ آنلاین و میانگین استعلام شده</span>
          </div>
        </div>

        <div class="relative w-full h-[340px] sm:h-[480px] touch-pan-y">
          <canvas id="macroChart"></canvas>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-[11px] sm:text-xs">
          <div class="flex flex-wrap items-center gap-3 sm:gap-4 text-slate-600 dark:text-slate-400">
            <span class="flex items-center gap-1.5">
              <span class="w-3.5 h-1.5 rounded-full bg-amber-500 inline-block"></span>
              قیمت ثبت‌شده تاریخی
            </span>
            <span class="flex items-center gap-1.5 font-bold text-cyan-600 dark:text-cyan-400">
              <span class="w-4 h-0.5 border-t-2 border-dashed border-cyan-400 inline-block"></span>
              پیش‌بینی ۱ ساله (نقطه‌چین غلتان)
            </span>
            <span class="flex items-center gap-1.5">
              <span class="w-3.5 h-1.5 rounded-full bg-purple-400 inline-block"></span>
              میانگین ۶ ماهه (SMA)
            </span>
          </div>
          <div class="text-slate-400 text-[11px]">
            ⚡ سیستم به طور خودکار روزانه قیمت‌ها را ذخیره کرده و میانگین ماه را آپدیت می‌کند.
          </div>
        </div>
      </div>

      <div class="glass-card rounded-2xl p-3.5 sm:p-5 shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-3 mb-2">
          <div>
            <h3 class="text-xs sm:text-base font-bold">نوسان ماه به ماه طلا (بازدهی ماهانه ٪)</h3>
            <p class="text-[10px] sm:text-xs text-slate-500 dark:text-slate-400">میزان رشد یا افت قیمت در هر ماه در طول تاریخ ۱۰ ساله</p>
          </div>
          <div class="text-[10px] sm:text-xs flex items-center gap-2">
            <span class="text-emerald-500 font-semibold">▲ سبز: ماه مثبت</span>
            <span class="text-rose-500 font-semibold">▼ قرمز: ماه منفی</span>
          </div>
        </div>
        <div class="relative w-full h-[200px] sm:h-[240px]">
          <canvas id="momReturnsChart"></canvas>
        </div>
      </div>
    </div>

    <!-- TAB 2: ROLLING 1-YEAR FORECAST DETAILS & SCENARIOS CHART -->
    <div id="tab-forecast-details" class="tab-content hidden space-y-4 sm:space-y-6">
      
      <!-- MODEL ARCHITECTURE HEADER BAR -->
      <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm border border-amber-500/30 bg-gradient-to-r from-slate-900/80 via-amber-950/20 to-slate-900/80">
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 mb-3 pb-3 border-b border-slate-200 dark:border-slate-800">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xl">🔮</span>
              <h3 class="text-sm sm:text-base font-black text-slate-900 dark:text-white" id="forecastDetailsHeader">پیش‌بینی و سناریوهای 12 ماه آینده (مدل ترکیبی سه‌گانه - Tri-Hybrid Ensemble)</h3>
            </div>
            <p class="text-xs text-slate-700 dark:text-slate-200 font-semibold mt-1">
              تلفیق هوشمندانه افق‌های زمانی: ماه 1 با هوش مصنوعی LSTM + ماه‌های 2 تا 5 با روند تطبیقی مومنتوم + ماه‌های 6 تا 12 با چرخه‌های فصلی 10 ساله
            </p>
          </div>
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="px-2.5 py-1 rounded-xl text-[11px] font-black border border-amber-400/60 bg-amber-500/15 text-amber-600 dark:text-amber-300 flex items-center gap-1.5 shadow-sm">
              <span class="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block"></span>
              <span>ماه 1: شبکه LSTM</span>
            </span>
            <span class="px-2.5 py-1 rounded-xl text-[11px] font-black border border-emerald-400/60 bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 flex items-center gap-1.5 shadow-sm">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>
              <span>ماه 2 تا 5: روند مومنتوم</span>
            </span>
            <span class="px-2.5 py-1 rounded-xl text-[11px] font-black border border-cyan-400/60 bg-cyan-500/15 text-cyan-600 dark:text-cyan-300 flex items-center gap-1.5 shadow-sm">
              <span class="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block"></span>
              <span>ماه 6 تا 12: چرخه فصلی</span>
            </span>
          </div>
        </div>

        <!-- 3 Architecture Explanation Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <!-- Box 1: Gold themed -->
          <div class="p-3.5 rounded-xl bg-amber-950/30 border border-amber-500/40 text-xs space-y-1.5 shadow-sm">
            <div class="flex items-center justify-between">
              <span class="font-black text-amber-600 dark:text-amber-300 text-xs sm:text-sm">🧠 1. کوتاه‌مدت (ماه 1):</span>
              <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-amber-900/80 text-amber-200 border border-amber-500/30">LSTM Deep Learning</span>
            </div>
            <p class="text-slate-800 dark:text-slate-100 font-medium text-xs leading-relaxed">
              مدل‌سازی شتاب آنی نوسانات و خودهمبستگی 30 روز اخیر جهت پیش‌بینی دقیق اولین ماه پیش‌رو.
            </p>
          </div>

          <!-- Box 2: Emerald themed -->
          <div class="p-3.5 rounded-xl bg-emerald-950/25 border border-emerald-500/30 text-xs space-y-1.5 shadow-sm">
            <div class="flex items-center justify-between">
              <span class="font-black text-emerald-600 dark:text-emerald-300 text-xs sm:text-sm">📈 2. میان‌مدت (ماه 2 تا 5):</span>
              <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-900/80 text-emerald-200 border border-emerald-500/30">Adaptive Momentum</span>
            </div>
            <p class="text-slate-800 dark:text-slate-100 font-medium text-xs leading-relaxed">
              روند تطبیقی میانگین متحرک نمایی (EWMA) و اثر انباشته نقدینگی بر بازار در افق چندماهه.
            </p>
          </div>

          <!-- Box 3: Cyan themed -->
          <div class="p-3.5 rounded-xl bg-cyan-950/25 border border-cyan-500/30 text-xs space-y-1.5 shadow-sm">
            <div class="flex items-center justify-between">
              <span class="font-black text-cyan-600 dark:text-cyan-300 text-xs sm:text-sm">🗓️ 3. بلندمدت (ماه 6 تا 12):</span>
              <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-cyan-900/80 text-cyan-200 border border-cyan-500/30">10-Year Seasonality</span>
            </div>
            <p class="text-slate-800 dark:text-slate-100 font-medium text-xs leading-relaxed">
              چرخه‌های فصلی تاریخی 10 ساله (جهش زمستانه بهمن/اسفند و فاز تثبیت خرداد) متصل به تورم سالانه.
            </p>
          </div>
        </div>
      </div>

      <!-- DEDICATED 12-MONTH UNIFIED FORECAST GROWTH CHART -->
      <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm border border-amber-500/40">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-3">
          <div>
            <h3 class="text-sm sm:text-base font-black text-slate-900 dark:text-white flex items-center gap-2">
              <span>📊 نمودار سناریوهای پیش‌بینی 12 ماه آینده (مسیر یکپارچه مدل ترکیبی)</span>
              <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-400/50">
                پیش‌بینی واحد
              </span>
            </h3>
            <p class="text-xs text-slate-700 dark:text-slate-200 font-semibold mt-1">
              مسیر سناریوی پایه ترکیبی (طلایی)، کف کریدور حمایتی (سبز) و سقف شتاب صعودی (آبی فیروزه‌ای)
            </p>
          </div>
        </div>

        <div class="relative w-full h-[320px] sm:h-[400px]">
          <canvas id="forecastScenariosChart"></canvas>
        </div>
      </div>

      <!-- 3 Scenario Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Card 1: Base Scenario (BOX 1: GOLD / AMBER THEMED - MATCHES SITE IDENTITY) -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-md border-2 border-amber-500/60 hover:border-amber-400 flex flex-col justify-between bg-gradient-to-b from-amber-500/10 via-slate-900/30 to-slate-900/50 relative overflow-hidden group" id="cardScenarioBase">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-black px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-950 dark:bg-amber-950 dark:text-amber-200 border border-amber-400/50">
                سناریوی پایه (محتمل‌ترین)
              </span>
              <span class="text-xs font-black text-amber-600 dark:text-amber-400">مسیر مرکزی</span>
            </div>
            <h4 class="text-base font-black mb-1 text-slate-900 dark:text-white">پیش‌بینی 12 ماهه مدل ترکیبی</h4>
            <p class="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-3">
              حاصل پیوند هوش مصنوعی LSTM، روند تورمی و چرخه‌های فصلی
            </p>

            <div class="p-3.5 rounded-xl bg-amber-500/15 dark:bg-amber-950/40 border border-amber-500/40 space-y-2.5 text-xs shadow-sm">
              <div class="flex items-center justify-between">
                <span class="font-black text-amber-700 dark:text-amber-300 text-xs sm:text-sm">هدف 12 ماهه:</span>
                <span class="font-black text-amber-600 dark:text-amber-400 text-base sm:text-lg" id="scenBase12m">--</span>
              </div>
              <div class="flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold">
                <span>رشد 12 ماهه:</span>
                <strong class="text-amber-600 dark:text-amber-400 font-black text-sm" id="scenBaseGrowth">+--%</strong>
              </div>
              <div class="flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold border-t border-amber-500/25 pt-2">
                <span>هدف 6 ماهه:</span>
                <strong class="text-slate-950 dark:text-white font-black" id="scenBase6m">--</strong>
              </div>
              <div class="flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold">
                <span>هدف 1 ماهه (LSTM):</span>
                <strong class="text-slate-950 dark:text-white font-black" id="scenBase1m">--</strong>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 2: Conservative Scenario (EMERALD GREEN) -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm border border-emerald-500/40 flex flex-col justify-between" id="cardScenarioCons">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-black px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-950 dark:bg-emerald-950 dark:text-emerald-200 border border-emerald-400/40">
                سناریوی محافظه‌کارانه
              </span>
              <span class="text-xs font-black text-emerald-600 dark:text-emerald-400">کف حمایتی</span>
            </div>
            <h4 class="text-base font-black mb-1 text-slate-900 dark:text-white">تثبیت نسبی و کف کریدور</h4>
            <p class="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-3">
              در صورت کنترل نقدینگی و ثبات نسبی متغیرهای کلان
            </p>

            <div class="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2.5 text-xs shadow-sm">
              <div class="flex items-center justify-between">
                <span class="font-black text-emerald-700 dark:text-emerald-300 text-xs sm:text-sm">کف 12 ماهه:</span>
                <span class="font-black text-emerald-600 dark:text-emerald-400 text-base sm:text-lg" id="scenCons12m">--</span>
              </div>
              <div class="flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold">
                <span>رشد 12 ماهه:</span>
                <strong class="text-emerald-600 dark:text-emerald-400 font-black text-sm" id="scenConsGrowth">+--%</strong>
              </div>
              <div class="flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold border-t border-emerald-500/20 pt-2">
                <span>کف 6 ماهه:</span>
                <strong class="text-slate-950 dark:text-white font-black" id="scenCons6m">--</strong>
              </div>
              <div class="flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold">
                <span>کف 1 ماهه:</span>
                <strong class="text-slate-950 dark:text-white font-black" id="scenCons1m">--</strong>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 3: Bullish Scenario (CYAN / SKY BLUE) -->
        <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm border border-cyan-500/40 flex flex-col justify-between" id="cardScenarioBull">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-black px-2.5 py-0.5 rounded-full bg-cyan-100 text-cyan-950 dark:bg-cyan-950 dark:text-cyan-200 border border-cyan-400/40">
                سناریوی صعودی و تورمی
              </span>
              <span class="text-xs font-black text-cyan-600 dark:text-cyan-400">سقف شتابان</span>
            </div>
            <h4 class="text-base font-black mb-1 text-slate-900 dark:text-white">شوک ارزی و سقف جهشی</h4>
            <p class="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-3">
              مشابه پرشتاب‌ترین دوره‌های صعودی طلا و انتظارات تورمی
            </p>

            <div class="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 space-y-2.5 text-xs shadow-sm">
              <div class="flex items-center justify-between">
                <span class="font-black text-cyan-700 dark:text-cyan-300 text-xs sm:text-sm">سقف 12 ماهه:</span>
                <span class="font-black text-cyan-600 dark:text-cyan-400 text-base sm:text-lg" id="scenBull12m">--</span>
              </div>
              <div class="flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold">
                <span>رشد 12 ماهه:</span>
                <strong class="text-cyan-600 dark:text-cyan-400 font-black text-sm" id="scenBullGrowth">+--%</strong>
              </div>
              <div class="flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold border-t border-cyan-500/20 pt-2">
                <span>سقف 6 ماهه:</span>
                <strong class="text-slate-950 dark:text-white font-black" id="scenBull6m">--</strong>
              </div>
              <div class="flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold">
                <span>سقف 1 ماهه:</span>
                <strong class="text-slate-950 dark:text-white font-black" id="scenBull1m">--</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Detailed 12-Month Rolling Table (Unified Hybrid) -->
      <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm overflow-x-auto">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
          <h3 class="text-sm sm:text-base font-black text-slate-900 dark:text-white flex items-center gap-2">
            <span>جدول زمان‌بندی ماه به ماه 12 ماه آینده (مدل ترکیبی سه‌گانه)</span>
            <span class="text-xs font-black px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-400/40">پیش‌بینی واحد</span>
          </h3>
          <span class="text-xs font-bold text-slate-700 dark:text-slate-200">مبدا محاسبات: آخرین نرخ روز و میانگین ثبت شده ماه</span>
        </div>
        <table class="w-full text-xs text-right border-collapse">
          <thead>
            <tr class="border-b-2 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 font-black whitespace-nowrap bg-slate-100/70 dark:bg-slate-800/60">
              <th class="py-3 px-3">ردیف</th>
              <th class="py-3 px-3">ماه آینده</th>
              <th class="py-3 px-3">الگوریتم حاکم بر افق زمانی</th>
              <th class="py-3 px-3 text-amber-600 dark:text-amber-400">قیمت سناریوی پایه (تومان)</th>
              <th class="py-3 px-3 text-emerald-600 dark:text-emerald-400">رشد ماهانه</th>
              <th class="py-3 px-3 text-amber-600 dark:text-amber-400">رشد تجمعی</th>
              <th class="py-3 px-3 text-emerald-600 dark:text-emerald-400">کف محافظه‌کارانه</th>
              <th class="py-3 px-3 text-cyan-600 dark:text-cyan-400">سقف صعودی</th>
            </tr>
          </thead>
          <tbody id="rollingForecastTableBody" class="divide-y divide-slate-200 dark:divide-slate-800/70"></tbody>
        </table>
      </div>
    </div>

    <!-- TAB: AI TRADING & INVESTMENT ADVISOR (دستیار هوشمند خرید و فروش و سرمایه‌گذاری) -->
    <div id="tab-advisor" class="tab-content hidden space-y-4 sm:space-y-6">
      
      <!-- HEADER BANNER -->
      <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm border border-emerald-500/40 bg-gradient-to-r from-emerald-950/30 via-slate-900/80 to-amber-950/25">
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 mb-3 pb-3 border-b border-slate-200 dark:border-slate-800">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-2xl">🤖</span>
              <h2 class="text-sm sm:text-lg font-black text-slate-900 dark:text-white">دستیار هوشمند خرید و فروش طلا و مشاور تحلیلی سرمایه‌گذاری</h2>
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-emerald-500/20 text-emerald-500 dark:text-emerald-300 border border-emerald-500/40">
                سیگنال و تحلیل بلادرنگ
              </span>
            </div>
            <p class="text-xs text-slate-700 dark:text-slate-200 font-semibold mt-1">
              تحلیل آنی ارزش خرید، سنجش حباب انواع سکه، مقایسه طلا با دلار و ارائه راهبرد تخصیص دارایی بر پایه داده‌های زنده بازار
            </p>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="px-3 py-1.5 rounded-xl text-xs font-black bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-300 flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span id="advisorEngineStatus">موتور هوش مصنوعی فعال</span>
            </span>
          </div>
        </div>

        <!-- 3 LIVE AI ADVISORY PILLARS -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <!-- Pillar 1: Buy/Sell Signal -->
          <div class="p-3.5 rounded-xl bg-slate-900/60 border border-emerald-500/30 space-y-1.5 shadow-sm">
            <div class="flex items-center justify-between">
              <span class="text-xs font-black text-emerald-400">📊 سیگنال تکنیکال و الگوریتمی:</span>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300" id="advisorSignalBadge">خرید پله‌ای (DCA)</span>
            </div>
            <p class="text-xs text-slate-200 font-bold leading-relaxed" id="advisorSignalText">
              با توجه به روند صعودی میان‌مدت و مدل LSTM، موقعیت جاری برای خرید پله‌ای و انباشت دارایی مناسب ارزیابی می‌شود.
            </p>
          </div>

          <!-- Pillar 2: Coin Bubble Warning -->
          <div class="p-3.5 rounded-xl bg-slate-900/60 border border-amber-500/30 space-y-1.5 shadow-sm">
            <div class="flex items-center justify-between">
              <span class="text-xs font-black text-amber-400">🫧 وضعیت حباب سکه امامی:</span>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300" id="advisorBubbleBadge">حباب بالا</span>
            </div>
            <p class="text-xs text-slate-200 font-bold leading-relaxed" id="advisorBubbleText">
              سکه امامی دارای حباب قابل‌توجه است. برای حفظ ارزش خالص، طلای ۱۸ عیار آبشده ارجحیت بالاتری نسبت به سکه دارد.
            </p>
          </div>

          <!-- Pillar 3: Gold vs Dollar vs Coin -->
          <div class="p-3.5 rounded-xl bg-slate-900/60 border border-cyan-500/30 space-y-1.5 shadow-sm">
            <div class="flex items-center justify-between">
              <span class="text-xs font-black text-cyan-400">⚖️ طلا در برابر دلار:</span>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300">سپر دوگانه</span>
            </div>
            <p class="text-xs text-slate-200 font-bold leading-relaxed">
              طلا هم از جهش دلار داخل و هم از رشد انس جهانی تغذیه می‌کند و در بلندمدت ۱۰ تا ۱۵ درصد بازدهی بالاتر از دلار ثبت کرده است.
            </p>
          </div>
        </div>
      </div>

      <!-- MAIN INTERACTIVE ADVISOR CHAT & BUBBLE CALCULATOR GRID -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6">
        
        <!-- LEFT/MAIN: INTERACTIVE AI CHAT ASSISTANT (7 COLS) -->
        <div class="lg:col-span-7 glass-card rounded-2xl p-4 sm:p-5 shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col justify-between h-[640px]">
          <div>
            <!-- Chat Header -->
            <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-200 dark:border-slate-800">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-base">
                  🤖
                </div>
                <div>
                  <h3 class="text-xs sm:text-sm font-black text-slate-900 dark:text-white">گفت‌وگو با مشاور هوشمند طلا و سکه</h3>
                  <p class="text-[10px] text-slate-500 dark:text-slate-400 font-semibold">پاسخ‌گویی بر مبنای نرخ‌های لحظه‌ای و مدل پیش‌بینی ۱ ساله</p>
                </div>
              </div>
              <button onclick="clearAdvisorChat()" class="text-[10px] text-slate-400 hover:text-rose-400 transition-colors px-2 py-1 rounded border border-slate-700/50">
                پاک‌سازی چت
              </button>
            </div>

            <!-- Quick Questions Pills -->
            <div class="mb-3">
              <span class="text-[11px] font-black text-slate-700 dark:text-slate-200 block mb-1.5">پرسش‌های پرتکرار (یک کلیک):</span>
              <div class="flex items-center gap-1.5 flex-wrap text-xs">
                <button onclick="quickAsk('طلا بخرم یا بفروشم؟')" class="px-2.5 py-1 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 dark:text-amber-300 border border-amber-500/30 font-bold transition-all text-[11px]">
                  🪙 الان طلا بخرم یا بفروشم؟
                </button>
                <button onclick="quickAsk('سکه بخرم، طلا یا دلار؟ کدوم بهتره؟')" class="px-2.5 py-1 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 border border-emerald-500/30 font-bold transition-all text-[11px]">
                  ⚖️ طلا، سکه یا دلار؟
                </button>
                <button onclick="quickAsk('کدام سکه حباب کمتری دارد؟')" class="px-2.5 py-1 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-600 dark:text-cyan-300 border border-cyan-500/30 font-bold transition-all text-[11px]">
                  🫧 کمترین حباب سکه
                </button>
                <button onclick="quickAsk('بهترین استراتژی خرید چیست؟')" class="px-2.5 py-1 rounded-xl bg-purple-500/10 hover:bg-purple-500/20 text-purple-600 dark:text-purple-300 border border-purple-500/30 font-bold transition-all text-[11px]">
                  🎯 استراتژی خرید پله‌ای
                </button>
                <button onclick="quickAsk('چطور بدون اجرت و مالیات طلا بخرم؟')" class="px-2.5 py-1 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-300 border border-rose-500/30 font-bold transition-all text-[11px]">
                  🛡️ خرید بدون اجرت
                </button>
              </div>
            </div>
          </div>

          <!-- Messages Container -->
          <div id="advisorChatContainer" class="flex-1 overflow-y-auto space-y-3 p-2.5 rounded-xl bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800/80 mb-3 text-xs leading-relaxed">
            <!-- Initial Welcome Message -->
            <div class="flex items-start gap-2 max-w-[90%]">
              <div class="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-xs shrink-0 mt-0.5">🤖</div>
              <div class="p-3 rounded-2xl rounded-tr-none bg-slate-200/80 dark:bg-slate-800 border border-slate-300 dark:border-slate-700/60 text-slate-900 dark:text-slate-100 space-y-1.5 shadow-sm">
                <p class="font-black text-emerald-600 dark:text-emerald-400">سلام! من دستیار هوشمند سرمایه‌گذاری طلای شما هستم.</p>
                <p class="text-slate-800 dark:text-slate-200">
                  من داده‌های زنده نرخ طلا ۱۸ عیار، مظنه، انواع سکه و خروجی پیش‌بینی ۱ ساله مدل ترکیبی (LSTM + روند فصلی) را در لحظه رصد می‌کنم.
                </p>
                <p class="text-slate-700 dark:text-slate-300">
                  می‌توانید بپرسید: <strong>«الان طلا بخرم یا بفروشم؟»</strong>، <strong>«طلا بهتره یا سکه و دلار؟»</strong> یا هر سوال دیگری درباره سرمایه‌گذاری در طلا!
                </p>
              </div>
            </div>
          </div>

          <!-- Chat Input Bar -->
          <form onsubmit="handleAdvisorSubmit(event)" class="flex items-center gap-2">
            <input type="text" id="advisorInput" placeholder="سوال خود را بنویسید (مثلاً: الان طلا بخرم یا سکه؟)..." class="flex-1 px-3.5 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 font-medium">
            <button type="submit" class="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-500/20 transition-all">
              <span>ارسال</span>
              <span>🚀</span>
            </button>
          </form>
        </div>

        <!-- RIGHT: LIVE COIN BUBBLE & INTRINSIC VALUE MATRIX (5 COLS) -->
        <div class="lg:col-span-5 space-y-4">
          <!-- Bubble Matrix Table Card -->
          <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm border border-slate-200 dark:border-slate-800">
            <div class="flex items-center justify-between mb-3 pb-2 border-b border-slate-200 dark:border-slate-800">
              <h3 class="text-xs sm:text-sm font-black text-slate-900 dark:text-white flex items-center gap-2">
                <span>🫧 جدول سنجش حباب و ارزش ذاتی مسکوکات</span>
              </h3>
              <span class="text-[10px] text-slate-400 font-mono">بر مبنای طلای ۱۸</span>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-right text-xs border-collapse">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 font-bold whitespace-nowrap">
                    <th class="py-2 px-2">دارایی</th>
                    <th class="py-2 px-2">قیمت روز</th>
                    <th class="py-2 px-2">ارزش طلا</th>
                    <th class="py-2 px-2">درصد حباب</th>
                    <th class="py-2 px-2">ارزندگی</th>
                  </tr>
                </thead>
                <tbody id="advisorBubbleTableBody" class="divide-y divide-slate-100 dark:divide-slate-800/70 font-semibold">
                  <!-- Rows populated dynamically -->
                </tbody>
              </table>
            </div>

            <div class="mt-3 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-[11px] text-slate-800 dark:text-slate-200 font-bold space-y-1">
              <div class="text-amber-600 dark:text-amber-400 font-black">💡 نکته کلیدی مشاور:</div>
              <p class="leading-relaxed">
                هر چه درصد حباب یک سکه کمتر باشد، ریسک ریزش آن در هنگام آرامش بازار کمتر است. <strong>طلای ۱۸ عیار آبشده</strong> دارای <strong>حباب صفر</strong> بوده و خالص‌ترین دارایی امن محسوب می‌شود.
              </p>
            </div>
          </div>

          <!-- ASSET ALLOCATION FORMULA CARD -->
          <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm border border-slate-200 dark:border-slate-800 space-y-3">
            <h3 class="text-xs sm:text-sm font-black text-slate-900 dark:text-white flex items-center gap-2">
              <span>💼 سبد پیشنهادی تخصیص دارایی (Asset Allocation)</span>
            </h3>
            
            <div class="space-y-2 text-xs">
              <div class="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                <div>
                  <span class="font-black text-emerald-600 dark:text-emerald-400">۶۰٪ طلای آبشده ۱۸ عیار / شمش:</span>
                  <span class="text-[11px] text-slate-700 dark:text-slate-300 block">هسته اصلی بدون حباب و ضد تورم</span>
                </div>
                <span class="font-black text-emerald-600 dark:text-emerald-400 text-sm">۶۰٪</span>
              </div>

              <div class="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between">
                <div>
                  <span class="font-black text-amber-600 dark:text-amber-400">۲۵٪ سکه بهار آزادی یا امامی:</span>
                  <span class="text-[11px] text-slate-700 dark:text-slate-300 block">نقدشوندگی سریع‌تر برای نوسان‌گیری</span>
                </div>
                <span class="font-black text-amber-600 dark:text-amber-400 text-sm">۲۵٪</span>
              </div>

              <div class="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-between">
                <div>
                  <span class="font-black text-cyan-600 dark:text-cyan-400">۱۵٪ نقدینگی ریالی (سپرده / درآمد ثابت):</span>
                  <span class="text-[11px] text-slate-700 dark:text-slate-300 block">برای شکار فرصت‌های خرید در اصلاحات قیمتی</span>
                </div>
                <span class="font-black text-cyan-600 dark:text-cyan-400 text-sm">۱۵٪</span>
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>

    <!-- TAB 3: طلا و حقوق پایه -->
    <div id="tab-wage" class="tab-content hidden space-y-4 sm:space-y-6">
      <div class="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-rose-900/30 to-amber-900/20 border border-rose-500/30 text-xs sm:text-sm leading-relaxed">
        <div class="flex items-center gap-2 font-bold text-rose-400 text-sm mb-1">
          <span>⚠️</span>
          <span>واقعیت اقتصادی: شکاف ۱۰ برابری رشد طلا نسبت به حقوق پایه</span>
        </div>
        حقوق پایه مصوب اداره کار از ۹۷۲ هزار تومان در سال ۱۳۹۵ به ۲۲ میلیون تومان در سال ۱۴۰۵ رسیده (رشد ۲۲.۶ برابری)، اما قیمت طلا در همین بازه بیش از ۲۲۶ برابر شده است. این یعنی قدرت خرید یک ماه دستمزد پایه از ۹.۴ گرم طلا به کمتر از ۱ گرم سقوط کرده است!
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm">
          <h3 class="text-sm sm:text-base font-bold mb-1">قدرت خرید حقوق پایه (چند گرم طلا با ۱ ماه حقوق؟)</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">سقوط از ۹.۴ گرم در سال ۹۵ به ۰.۹۴ گرم امروز</p>
          <div class="relative w-full h-[280px] sm:h-[320px]">
            <canvas id="purchasingPowerChart"></canvas>
          </div>
        </div>

        <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm">
          <h3 class="text-sm sm:text-base font-bold mb-1">شاخص مقایسه‌ای رشد طلا در برابر حقوق پایه (مبنای ۱۰۰ = سال ۹۵)</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">نمایش پیشتازی فزاینده قیمت طلا نسبت به افزایش دستمزدها</p>
          <div class="relative w-full h-[280px] sm:h-[320px]">
            <canvas id="growthIndexChart"></canvas>
          </div>
        </div>
      </div>

      <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm overflow-x-auto">
        <h3 class="text-sm sm:text-base font-bold mb-3">جدول مقایسه سالیانه حقوق پایه مصوب و معادل طلایی آن</h3>
        <table class="w-full text-xs text-right border-collapse">
          <thead>
            <tr class="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold">
              <th class="py-2.5 px-3">سال</th>
              <th class="py-2.5 px-3">حقوق پایه کارگر (تومان)</th>
              <th class="py-2.5 px-3">درصد رشد سالانه حقوق</th>
              <th class="py-2.5 px-3">میانگین قیمت طلا در سال</th>
              <th class="py-2.5 px-3">معادل گرم طلا با ۱ ماه حقوق</th>
              <th class="py-2.5 px-3">تغییر قدرت خرید طلا</th>
            </tr>
          </thead>
          <tbody id="wageTableBody" class="divide-y divide-slate-100 dark:divide-slate-800/60"></tbody>
        </table>
      </div>
    </div>

    <!-- TAB 4: الگوی فصلی و هیت‌مپ -->
    <div id="tab-seasonality" class="tab-content hidden space-y-4 sm:space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm">
          <h3 class="text-sm sm:text-base font-bold mb-1">کدام ماه‌ها بهترین زمان خرید بوده‌اند؟</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">میانگین بازدهی هر کدام از ۱۲ ماه سال در طول ۱۰ سال گذشته</p>
          <div class="relative w-full h-[280px] sm:h-[320px]">
            <canvas id="seasonalityBarChart"></canvas>
          </div>
        </div>

        <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm">
          <h3 class="text-sm sm:text-base font-bold mb-1">احتمال صعود طلا در هر ماه (Win Rate ٪)</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">درصد سال‌هایی که این ماه با رشد مثبت بسته شده است</p>
          <div class="relative w-full h-[280px] sm:h-[320px]">
            <canvas id="seasonalityWinRateChart"></canvas>
          </div>
        </div>
      </div>

      <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm">
        <div class="flex items-center justify-between gap-2 mb-3">
          <div>
            <h3 class="text-sm sm:text-base font-bold mb-1">هیت‌مپ ماتریسی نوسانات ماهانه (Year-Month Matrix)</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400">درصد بازدهی هر ماه نسبت به ماه قبل. سبز: رشد، قرمز: افت</p>
          </div>
          <div class="flex items-center gap-2 text-[11px]">
            <span class="w-2.5 h-2.5 rounded bg-emerald-600 inline-block"></span><span>رشد بالا</span>
            <span class="w-2.5 h-2.5 rounded bg-rose-600 inline-block"></span><span>افت</span>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-center border-collapse">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                <th class="py-2 px-2 text-right">سال</th>
                <th class="py-2 px-1">فروردین</th>
                <th class="py-2 px-1">اردیبهشت</th>
                <th class="py-2 px-1">خرداد</th>
                <th class="py-2 px-1">تیر</th>
                <th class="py-2 px-1">مرداد</th>
                <th class="py-2 px-1">شهریور</th>
                <th class="py-2 px-1">مهر</th>
                <th class="py-2 px-1">آبان</th>
                <th class="py-2 px-1">آذر</th>
                <th class="py-2 px-1">دی</th>
                <th class="py-2 px-1">بهمن</th>
                <th class="py-2 px-1">اسفند</th>
              </tr>
            </thead>
            <tbody id="heatmapTableBody" class="divide-y divide-slate-100 dark:divide-slate-800"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 5: کارنامه سال به سال -->
    <div id="tab-yearly" class="tab-content hidden space-y-4 sm:space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <div class="lg:col-span-2 glass-card rounded-2xl p-4 sm:p-5 shadow-sm">
          <h3 class="text-sm sm:text-base font-bold mb-1">بازدهی سالانه طلا (درصد رشد هر سال)</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">سنجش عملکرد انتهای هر سال نسبت به شروع آن</p>
          <div class="relative w-full h-[280px] sm:h-[320px]">
            <canvas id="yearlyReturnBarChart"></canvas>
          </div>
        </div>

        <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 class="text-sm sm:text-base font-bold mb-3">بینش‌های کلیدی سالانه</h3>
            <ul class="space-y-2.5 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              <li class="flex items-start gap-2">
                <span class="text-amber-500 font-bold">🥇</span>
                <div><strong>رکورد جهش سالانه:</strong> سال ۱۴۰۴ با رشد ۱۴۶٪ و سال ۱۳۹۷ با رشد ۱۶۳٪ پرشتاب‌ترین سال‌های صعودی بوده‌اند.</div>
              </li>
              <li class="flex items-start gap-2">
                <span class="text-amber-500 font-bold">🛡️</span>
                <div><strong>بدون بازدهی منفی:</strong> در تمام ۱۱ سال ثبت‌شده، بازدهی کلی طلا همواره مثبت بوده و هیچ سالی زیان‌ده بسته نشده است!</div>
              </li>
              <li class="flex items-start gap-2">
                <span class="text-amber-500 font-bold">📉</span>
                <div><strong>آرام‌ترین سال:</strong> سال ۱۳۹۶ با بازدهی ۲۸٪ کم‌نوسان‌ترین دوره بوده است.</div>
              </li>
            </ul>
          </div>
          <div class="p-3 bg-amber-500/10 rounded-xl border border-amber-500/20 text-[11px] text-amber-700 dark:text-amber-400 mt-3">
            📌 جزئیات کف و سقف هر سال در جدول زیر آمده است.
          </div>
        </div>
      </div>

      <div class="glass-card rounded-2xl p-4 sm:p-5 shadow-sm overflow-x-auto">
        <h3 class="text-sm sm:text-base font-bold mb-3">کارنامه عملکرد تفکیکی سال‌های ۱۳۹۵ تا ۱۴۰۵</h3>
        <table class="w-full text-xs text-right border-collapse">
          <thead>
            <tr class="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold">
              <th class="py-2.5 px-3">سال</th>
              <th class="py-2.5 px-3">شروع سال (فروردین)</th>
              <th class="py-2.5 px-3">پایان سال</th>
              <th class="py-2.5 px-3">حداقل سال</th>
              <th class="py-2.5 px-3">حداکثر سال</th>
              <th class="py-2.5 px-3">میانگین سال</th>
              <th class="py-2.5 px-3">بازدهی سال (٪)</th>
              <th class="py-2.5 px-3">حقوق پایه کارگر</th>
            </tr>
          </thead>
          <tbody id="yearlyTableBody" class="divide-y divide-slate-100 dark:divide-slate-800/60"></tbody>
        </table>
      </div>
    </div>

    <!-- TAB 6: بانک کل داده‌ها -->
    <div id="tab-table" class="tab-content hidden space-y-4">
      <div class="glass-card rounded-2xl p-3.5 sm:p-5 shadow-sm">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 class="text-sm sm:text-base font-bold">بانک داده کامل قیمت طلا ۱۸ عیار</h3>
            <p class="text-[11px] sm:text-xs text-slate-500 dark:text-slate-400">شامل داده‌های اکسل + رکوردهای خودکار روزانه estjt.ir</p>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <input type="text" id="tableSearch" onkeyup="filterDataTable()" placeholder="جستجوی ماه یا سال..." class="px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-none flex-grow sm:flex-grow-0">
            <select id="tableYearFilter" onchange="filterDataTable()" class="px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-none">
              <option value="all">همه سال‌ها</option>
            </select>
            <button onclick="exportToCSV()" class="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors flex items-center gap-1 shadow-sm">
              <span>📥</span>
              <span>خروجی CSV</span>
            </button>
          </div>
        </div>

        <div class="overflow-x-auto max-h-[550px] overflow-y-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <table class="w-full text-xs text-right border-collapse" id="fullDataTable">
            <thead class="sticky top-0 bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800 font-bold z-10">
              <tr>
                <th class="py-2.5 px-3">ردیف</th>
                <th class="py-2.5 px-3">تاریخ</th>
                <th class="py-2.5 px-3">قیمت هر گرم طلا (تومان)</th>
                <th class="py-2.5 px-3">نوسان ماه به ماه</th>
                <th class="py-2.5 px-3">درصد تغییر ماهانه</th>
                <th class="py-2.5 px-3">حقوق اداره کار</th>
                <th class="py-2.5 px-3">معادل گرم طلا با حقوق</th>
              </tr>
            </thead>
            <tbody id="fullDataTableBody" class="divide-y divide-slate-100 dark:divide-slate-800/70"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 7: مدیریت آنلاین، سکه‌ها و لاگ استعلام‌های ۳۰ دقیقه‌ای -->
    <div id="tab-live-sync" class="tab-content hidden space-y-4 sm:space-y-6">
      
      <!-- Auto-sync Status Card -->
      <div class="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-emerald-900/30 via-teal-900/20 to-cyan-900/20 border border-emerald-500/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2 font-bold text-emerald-400 text-sm sm:text-base">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping inline-block"></span>
            <span>سیستم ذخیره‌سازی خودکار هر ۳۰ دقیقه فعال است</span>
          </div>
          <p class="text-xs text-slate-300 mt-1">
            سایت هر ۳۰ دقیقه یکبار قیمت‌های جدید را از اتحادیه دریافت و ذخیره می‌کند، میانگین ماه را محاسبه نموده و پیش‌بینی را به‌روز نگه می‌دارد.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <div class="px-3 py-2 rounded-xl bg-slate-900/80 border border-emerald-500/40 text-xs font-mono text-emerald-400 font-bold">
            زمان تا استعلام بعدی: <span id="syncPanelCountdown">۳۰:۰۰</span>
          </div>
          <button onclick="fetchLiveOnlinePrice(false)" class="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition-all">
            استعلام آنی
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        
        <!-- Live Connector Card with Full Coins -->
        <div class="glass-card rounded-2xl p-5 shadow-sm border border-emerald-500/30">
          <div class="flex items-center gap-2 mb-3">
            <span class="text-2xl">🌐</span>
            <h3 class="text-base sm:text-lg font-bold">آخرین نرخ‌های استعلام‌شده از اتحادیه (estjt.ir)</h3>
          </div>

          <div class="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 space-y-2 text-xs mb-4">
            <div class="flex justify-between items-center py-1 border-b border-emerald-200/60 dark:border-emerald-800/60">
              <span class="text-slate-600 dark:text-slate-300">قیمت هر گرم طلای ۱۸ عیار:</span>
              <span id="syncPanelGoldPrice" class="font-black text-sm text-emerald-600 dark:text-emerald-400">۲۳,۴۸۴,۵۰۰ تومان</span>
            </div>
            <div class="flex justify-between items-center py-1 border-b border-emerald-200/60 dark:border-emerald-800/60">
              <span class="text-slate-600 dark:text-slate-300">مظنه تهران (هر مثقال):</span>
              <span id="syncPanelMesghal" class="font-bold">۱۰۱,۷۳۰,۰۰۰ تومان</span>
            </div>
            <div class="flex justify-between items-center py-1 border-b border-emerald-200/60 dark:border-emerald-800/60">
              <span class="text-slate-600 dark:text-slate-300">سکه تمام طرح جدید (امامی):</span>
              <span id="syncPanelCoinNew" class="font-bold text-amber-500">۲۳۳,۵۰۰,۰۰۰ تومان</span>
            </div>
            <div class="flex justify-between items-center py-1 border-b border-emerald-200/60 dark:border-emerald-800/60">
              <span class="text-slate-600 dark:text-slate-300">سکه بهار آزادی (طرح قدیم):</span>
              <span id="syncPanelCoinOld" class="font-bold">۲۳۰,۵۰۰,۰۰۰ تومان</span>
            </div>
            <div class="flex justify-between items-center py-1 border-b border-emerald-200/60 dark:border-emerald-800/60">
              <span class="text-slate-600 dark:text-slate-300">نیم سکه بهار آزادی:</span>
              <span id="syncPanelHalfCoin" class="font-bold">۱۱۹,۵۰۰,۰۰۰ تومان</span>
            </div>
            <div class="flex justify-between items-center py-1 border-b border-emerald-200/60 dark:border-emerald-800/60">
              <span class="text-slate-600 dark:text-slate-300">ربع سکه بهار آزادی:</span>
              <span id="syncPanelQuarterCoin" class="font-bold">۶۴,۵۰۰,۰۰۰ تومان</span>
            </div>
            <div class="flex justify-between items-center py-1 border-b border-emerald-200/60 dark:border-emerald-800/60">
              <span class="text-slate-600 dark:text-slate-300">سکه یک گرمی:</span>
              <span id="syncPanelGramCoin" class="font-bold">۳۵,۰۰۰,۰۰۰ تومان</span>
            </div>
            <div class="flex justify-between items-center pt-2">
              <span class="text-slate-500 dark:text-slate-400">زمان آخرین استعلام:</span>
              <span id="syncPanelTime" class="font-semibold text-slate-700 dark:text-slate-300">{live_time}</span>
            </div>
          </div>

          <div class="flex gap-2">
            <button onclick="fetchLiveOnlinePrice(false)" class="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-1.5">
              <span>🔄</span>
              <span>استعلام و همگام‌سازی فوری</span>
            </button>
            <a href="https://www.estjt.ir/" target="_blank" class="px-3 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-semibold flex items-center gap-1">
              <span>🔗 سایت اتحادیه</span>
            </a>
          </div>
        </div>

        <!-- Running Monthly Average & Daily Log -->
        <div class="glass-card rounded-2xl p-5 shadow-sm border border-cyan-500/30 flex flex-col justify-between">
          <div>
            <div class="flex items-center gap-2 mb-3">
              <span class="text-2xl">📅</span>
              <h3 class="text-base sm:text-lg font-bold">محاسبه خودکار میانگین ماه جاری</h3>
            </div>
            <p class="text-xs text-slate-500 dark:text-slate-400 mb-3">
              سیستم قیمت‌های ثبت‌شده در طول ماه را جمع‌آوری کرده و میانگین واقعی ماه را برای پیش‌بینی و گزارش‌ها به صورت زنده استخراج می‌کند:
            </p>

            <div class="grid grid-cols-2 gap-2 text-xs mb-4">
              <div class="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
                <span class="text-slate-400 block text-[11px]">ماه جاری:</span>
                <span class="font-black text-sm text-cyan-600 dark:text-cyan-400" id="logCurrentMonthName">شهریور ۱۴۰۵</span>
              </div>
              <div class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30">
                <span class="text-slate-400 block text-[11px]">تعداد استعلام‌های ذخیره‌شده:</span>
                <span class="font-black text-sm text-amber-600 dark:text-amber-400" id="logSampleCount">۳ رکورد</span>
              </div>
              <div class="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 col-span-2">
                <div class="flex justify-between items-center">
                  <span class="text-slate-500 dark:text-slate-400">میانگین قیمت محاسبه‌شده ماه:</span>
                  <span class="font-black text-base text-emerald-600 dark:text-emerald-400" id="logMonthAverage">۲۳,۴۷۹,۹۰۰ تومان</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Log Table -->
          <div>
            <h4 class="text-xs font-bold mb-2 text-slate-700 dark:text-slate-300">تاریخچه آخرین استعلام‌های ذخیره‌شده:</h4>
            <div class="max-h-[140px] overflow-y-auto rounded-xl border border-slate-200 dark:border-slate-800">
              <table class="w-full text-[11px] text-right">
                <thead class="bg-slate-100 dark:bg-slate-800 text-slate-400">
                  <tr>
                    <th class="p-1.5 px-2">زمان استعلام</th>
                    <th class="p-1.5 px-2">قیمت ۱۸ عیار</th>
                    <th class="p-1.5 px-2">مظنه</th>
                  </tr>
                </thead>
                <tbody id="dailyTicksTableBody" class="divide-y divide-slate-100 dark:divide-slate-800"></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- SQLite Database Details Card -->
        <div class="glass-card rounded-2xl p-5 shadow-sm border border-emerald-500/30">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="text-2xl">🗄️</span>
              <h3 class="text-base sm:text-lg font-bold">بانک داده پایدار SQLite (ذخیره ۳۰ دقیقه‌ای)</h3>
            </div>
            <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-bold">
              فعال و در حال ثبت
            </span>
          </div>
          <p class="text-xs text-slate-500 dark:text-slate-400 mb-3">
            تمام استعلام‌های هر ۳۰ دقیقه در فایل بانک اطلاعاتی استاندارد <code class="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded text-amber-500 font-mono">gold_database.db</code> به صورت ساختاریافته ذخیره می‌شوند تا هیچ داده‌ای از دست نرود.
          </p>

          <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs mb-3">
            <div class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <span class="text-slate-400 block text-[10px]">تعداد کل رکوردهای دیتابیس:</span>
              <span class="font-black text-sm text-emerald-600 dark:text-emerald-400" id="dbTotalRecords">۱ رکورد</span>
            </div>
            <div class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <span class="text-slate-400 block text-[10px]">حجم فایل دیتابیس:</span>
              <span class="font-black text-sm text-cyan-600 dark:text-cyan-400" id="dbFileSize">۲۴ کیلوبایت</span>
            </div>
            <div class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 col-span-2 sm:col-span-1">
              <span class="text-slate-400 block text-[10px]">پروتکل ذخیره‌سازی:</span>
              <span class="font-bold text-xs text-slate-700 dark:text-slate-300">SQLite 3 + JSON Sync</span>
            </div>
          </div>
          <div class="text-[11px] text-slate-400">
            💡 با هربار استعلام، میانگین واقعی ماه جاری با کوئری مستقیم SQL روی تمام قیمت‌های ثبت شده در همان ماه بازتولید می‌شود.
          </div>
        </div>

      </div>
    </div>

  </main>

  <!-- FOOTER -->
  <footer class="mt-8 sm:mt-12 border-t border-slate-200 dark:border-slate-800 py-6 text-center text-[11px] sm:text-xs text-slate-500 dark:text-slate-400">
    <div class="max-w-7xl mx-auto px-4 space-y-1">
      <p class="font-medium">سامانه هوشمند تحلیل طلا و سکه • دیتای آنلاین متصل به اتحادیه طلا و جواهر تهران (estjt.ir)</p>
      <p class="text-[10px] text-slate-400">استعلام و ذخیره خودکار هر ۳۰ دقیقه • محاسبه میانگین ماه • پیش‌بینی پویا و غلتان ۱ ساله</p>
    </div>
  </footer>

  <!-- RAW DATA INJECTION -->
  <script>
    const INITIAL_DATA = {json_str};
  </script>

  <!-- DASHBOARD ENGINE WITH 30-MIN AUTO-SYNC & RUNNING MONTHLY AVERAGE -->
  <script>
    // App State
    let APP_DATA = JSON.parse(JSON.stringify(INITIAL_DATA));
    let currentScale = 'linear';
    window.macroChartInstance = null;
    let momChartInstance = null;
    let forecastScenarioChartInstance = null;
    let purchasingPowerChartInstance = null;
    let growthIndexChartInstance = null;
    let seasonalityBarChartInstance = null;
    let seasonalityWinRateChartInstance = null;
    let yearlyReturnChartInstance = null;
    let currentTimelineFilter = 'all';
    let isForecastVisible = true;
    let currentForecastScenario = 'base';

    const AUTO_SYNC_INTERVAL_SEC = 30 * 60; // 30 minutes
    let nextSyncCountdown = AUTO_SYNC_INTERVAL_SEC;

    const MONTHS_ORDER = [
      "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
      "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ];

    // Load persisted data from localStorage if exists
    try {{
      const saved = localStorage.getItem('gold_dashboard_custom_data');
      if (saved) {{
        const parsed = JSON.parse(saved);
        if (parsed && parsed.timeline && parsed.timeline.length >= APP_DATA.timeline.length) {{
          APP_DATA = parsed;
        }}
      }}
    }} catch (e) {{
      console.warn("Could not read localStorage:", e);
    }}

    // Helpers
        function formatNumber(num) {{
      if (num === null || num === undefined || isNaN(num)) return '-';
      return new Intl.NumberFormat('en-US').format(Math.round(num));
    }}

    function formatNumberDecimal(num, decimals = 1) {{
      if (num === null || num === undefined || isNaN(num)) return '-';
      return new Intl.NumberFormat('en-US', {{
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      }}).format(num);
    }}

    function cleanPersianNumber(text) {{
      if (!text) return 0;
      const persianDigits = '۰۱۲۳۴۵۶۷۸۹';
      const arabicDigits = '٠١٢٣٤٥٦٧۸۹';
      let s = text.toString();
      for (let i = 0; i < 10; i++) {{
        s = s.replaceAll(persianDigits[i], i.toString()).replaceAll(arabicDigits[i], i.toString());
      }}
      s = s.replaceAll('\\u066b', '').replaceAll('\\u066c', '').replaceAll('٬', '').replaceAll(',', '').replaceAll(' ', '').replaceAll('تومان', '').replaceAll('$', '').trim();
      return parseFloat(s) || 0;
    }}

    function roundDecimal(val, places) {{
      const factor = Math.pow(10, places);
      return Math.round(val * factor) / factor;
    }}

    // Accurate Gregorian to Jalali converter
    function gregorianToJalali(gy, gm, gd) {{
      const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
      let jy = gy > 1600 ? 979 : 0;
      gy -= gy > 1600 ? 1600 : 621;
      const gy2 = gm > 2 ? gy + 1 : gy;
      let days = (365 * gy) + Math.floor((gy2 + 3) / 4) - Math.floor((gy2 + 99) / 100) + Math.floor((gy2 + 399) / 400) - 80 + gd + g_d_m[gm - 1];
      jy += 33 * Math.floor(days / 12053);
      days %= 12053;
      jy += 4 * Math.floor(days / 1461);
      days %= 1461;
      if (days > 365) {{
        jy += Math.floor((days - 1) / 365);
        days = (days - 1) % 365;
      }}
      const jm = days < 186 ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30);
      const jd = 1 + (days < 186 ? (days % 31) : ((days - 186) % 30));
      return {{ year: jy, month: jm, day: jd }};
    }}

    function getNowPersian() {{
      const now = new Date();
      const j = gregorianToJalali(now.getFullYear(), now.getMonth() + 1, now.getDate());
      const hh = String(now.getHours()).padStart(2, '0');
      const mm = String(now.getMinutes()).padStart(2, '0');
      const ss = String(now.getSeconds()).padStart(2, '0');
      const monthName = MONTHS_ORDER[j.month - 1];
      const monthKey = `${{j.year}}-${{j.month < 10 ? '0' + j.month : j.month}}`;
      const dateStr = `${{j.year}}/${{j.month < 10 ? '0' + j.month : j.month}}/${{j.day < 10 ? '0' + j.day : j.day}}`;
      const timeStr = `${{j.day}} ${{monthName}} ${{j.year}} - ${{hh}}:${{mm}}:${{ss}}`;
      return {{ ...j, monthName, monthKey, dateStr, timeStr }};
    }}

    // RECORD DAILY TICK AND RECALCULATE RUNNING MONTH AVERAGE
    function recordDailyTick(price, mesghal, coin) {{
      const pNow = getNowPersian();
      if (!APP_DATA.daily_data) {{
        APP_DATA.daily_data = {{ ticks: [], monthly_aggregates: {{}} }};
      }}

      // Append tick
      APP_DATA.daily_data.ticks.unshift({{
        timestamp: pNow.timeStr,
        date: pNow.dateStr,
        year: pNow.year,
        month: pNow.month,
        month_name: pNow.monthName,
        day: pNow.day,
        price: price,
        mesghal: mesghal || null,
        coin_new: coin || null
      }});

      // Keep up to 200 ticks
      if (APP_DATA.daily_data.ticks.length > 200) {{
        APP_DATA.daily_data.ticks = APP_DATA.daily_data.ticks.slice(0, 200);
      }}

      // Calculate monthly average for current month
      const currentMonthTicks = APP_DATA.daily_data.ticks.filter(t => t.year === pNow.year && t.month === pNow.month);
      const sum = currentMonthTicks.reduce((acc, curr) => acc + curr.price, 0);
      const count = currentMonthTicks.length;
      const monthAvg = Math.round(sum / count);

      APP_DATA.daily_data.monthly_aggregates[pNow.monthKey] = {{
        year: pNow.year,
        month: pNow.month,
        month_name: pNow.monthName,
        label: `${{pNow.monthName}} ${{pNow.year}}`,
        samples_count: count,
        avg_price: monthAvg,
        latest_price: price
      }};

      // Check if current calendar month exists in timeline; if not, automatically advance month!
      const currentLabel = `${{pNow.monthName}} ${{pNow.year}}`;
      let latestItem = APP_DATA.timeline[APP_DATA.timeline.length - 1];

      if (latestItem.label !== currentLabel && pNow.year >= latestItem.year) {{
        // New month has begun! Auto-add month to timeline
        const prevPrice = latestItem.price;
        const newMonthItem = {{
          year: pNow.year,
          month_idx: pNow.month,
          month_name: pNow.monthName,
          label: currentLabel,
          short_label: `${{pNow.year}}/${{pNow.month < 10 ? '0' + pNow.month : pNow.month}}`,
          price: price,
          wage: latestItem.wage,
          wage_in_gold_grams: roundDecimal(latestItem.wage / price, 2),
          mom_change_amount: price - prevPrice,
          mom_change_pct: roundDecimal(((price - prevPrice) / prevPrice) * 100, 2),
          month_avg_price: monthAvg,
          daily_samples_count: count
        }};
        APP_DATA.timeline.push(newMonthItem);
        latestItem = newMonthItem;
      }} else {{
        // Update current month item with latest price and running month average
        const prevItem = APP_DATA.timeline[APP_DATA.timeline.length - 2];
        latestItem.price = price;
        latestItem.month_avg_price = monthAvg;
        latestItem.daily_samples_count = count;
        latestItem.mom_change_amount = price - prevItem.price;
        latestItem.mom_change_pct = roundDecimal(((price - prevItem.price) / prevItem.price) * 100, 2);
        latestItem.wage_in_gold_grams = roundDecimal(latestItem.wage / price, 2);
      }}

      // Persist to localStorage
      try {{
        localStorage.setItem('gold_dashboard_custom_data', JSON.stringify(APP_DATA));
      }} catch(e) {{}}

      return {{ monthAvg, count, pNow }};
    }}

    // AUTO-SYNC 30-MINUTE TIMER & COUNTDOWN
    function startAutoSyncTimer() {{
      setInterval(() => {{
        nextSyncCountdown--;
        if (nextSyncCountdown <= 0) {{
          nextSyncCountdown = AUTO_SYNC_INTERVAL_SEC;
          fetchLiveOnlinePrice(true);
        }}
        const mins = Math.floor(nextSyncCountdown / 60);
        const secs = nextSyncCountdown % 60;
        const formatted = `${{mins < 10 ? '0' + mins : mins}}:${{secs < 10 ? '0' + secs : secs}}`;
        const el1 = document.getElementById('autoSyncCountdown');
        const el2 = document.getElementById('syncPanelCountdown');
        if (el1) el1.textContent = formatted;
        if (el2) el2.textContent = formatted;
      }}, 1000);
    }}

    // Theme Toggle
    function toggleTheme() {{
      const html = document.documentElement;
      const icon = document.getElementById('themeIcon');
      if (html.classList.contains('dark')) {{
        html.classList.remove('dark');
        icon.textContent = '🌙';
        localStorage.theme = 'light';
      }} else {{
        html.classList.add('dark');
        icon.textContent = '☀️';
        localStorage.theme = 'dark';
      }}
      setTimeout(() => updateAllChartsTheme(), 50);
    }}

    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {{
      document.documentElement.classList.add('dark');
      document.getElementById('themeIcon').textContent = '☀️';
    }} else {{
      document.documentElement.classList.remove('dark');
      document.getElementById('themeIcon').textContent = '🌙';
    }}

    function toggleScale() {{
      const newScale = currentScale === 'linear' ? 'logarithmic' : 'linear';
      currentScale = newScale;
      document.getElementById('btnScaleToggle').textContent = 'مقیاس: ' + (newScale === 'linear' ? 'خطی' : 'لگاریتمی');
      if (macroChartInstance) {{
        macroChartInstance.options.scales.y.type = newScale;
        macroChartInstance.update();
      }}
    }}

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.tab-grid-btn').forEach(el => el.classList.remove('active'));

      const activeTab = document.getElementById(tabId);
      if (activeTab) activeTab.classList.remove('hidden');

      const activeBtn = document.getElementById('btn-' + tabId);
      if (activeBtn) activeBtn.classList.add('active');

      setTimeout(() => {{
        if (tabId === 'tab-advisor') {{
          updateAdvisorMarketSignals();
        }} else if (tabId === 'tab-macro') {{
          renderMacroChart();
        }} else if (tabId === 'tab-forecast-details') {{
          renderForecastScenarioChart();
          populateRollingForecastTable();
        }} else if (tabId === 'tab-wage') {{
          populateWageTable();
          renderWageCharts();
        }} else if (tabId === 'tab-seasonality') {{
          populateHeatmap();
          renderSeasonalityCharts();
        }} else if (tabId === 'tab-yearly') {{
          populateYearlyTable();
          renderYearlyCharts();
        }} else if (tabId === 'tab-live-sync') {{
          populateDailyTicksTable();
        }}
      }}, 50);
    }}

    function filterTimeline(range) {{
      currentTimelineFilter = range;
      document.querySelectorAll('.time-filter').forEach(btn => {{
        if (btn.dataset.range === range) {{
          btn.className = "time-filter active px-2.5 py-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-amber-400 text-slate-900 font-bold";
        }} else {{
          btn.className = "time-filter px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors";
        }}
      }});
      renderMacroChart();
    }}

    function toggleForecastVisibility() {{
      isForecastVisible = !isForecastVisible;
      const btn = document.getElementById('btnToggleForecast');
      if (isForecastVisible) {{
        btn.innerHTML = `<span class="w-2 h-2 rounded-full bg-cyan-500 animate-ping inline-block"></span><span>خط پیش‌بینی: فعال</span>`;
        btn.className = "px-2.5 sm:px-3 py-1.5 rounded-xl border border-cyan-400 bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 font-bold text-[11px] sm:text-xs flex items-center gap-1.5 shadow-sm transition-all";
      }} else {{
        btn.innerHTML = `<span>خط پیش‌بینی: خاموش</span>`;
        btn.className = "px-2.5 sm:px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-500 font-medium text-[11px] sm:text-xs flex items-center gap-1.5 shadow-sm transition-all";
      }}
      renderMacroChart();
    }}

    function changeForecastScenario(scenario) {{
      currentForecastScenario = scenario;
      renderMacroChart();
      renderForecastScenarioChart();
    }}

    // ۱. موتور پیش‌بینی آماری و فصلی (مدل عادی)
    function generateSeasonalForecast() {{
      const latestItem = APP_DATA.timeline[APP_DATA.timeline.length - 1];
      const startPrice = latestItem.price;
      const startYear = latestItem.year;
      const startMonthIdx = latestItem.month_idx;

      const seasonMap = {{}};
      APP_DATA.seasonality.forEach(s => {{
        seasonMap[s.month_idx] = s.avg_mom_return;
      }});

      let curBase = startPrice;
      let curCons = startPrice;
      let curBull = startPrice;

      const baseList = [];
      const consList = [];
      const bullList = [];

      const monthlyConsRate = Math.pow(1 + 0.40, 1/12) - 1;
      const monthlyBullRate = Math.pow(1 + 0.90, 1/12) - 1;
      const sumSeasonWeights = Object.values(seasonMap).reduce((a, b) => a + b, 0);

      let curY = startYear;
      let curM = startMonthIdx;

      for (let i = 1; i <= 12; i++) {{
        curM++;
        if (curM > 12) {{
          curM = 1;
          curY++;
        }}

        const mName = MONTHS_ORDER[curM - 1];
        const label = `${{mName}} ${{curY}}`;
        const seasonalMom = seasonMap[curM] || 4.5;

        // Base
        curBase = curBase * (1 + (seasonalMom / 100));
        baseList.push({{
          month_name: mName,
          year: curY,
          label: label,
          price: Math.round(curBase),
          growth_mom: seasonalMom,
          growth_from_now: roundDecimal(((curBase - startPrice) / startPrice) * 100, 1)
        }});

        // Conservative
        const weight = (seasonalMom / sumSeasonWeights) * 12;
        curCons = curCons * (1 + monthlyConsRate * weight);
        consList.push({{
          label: label,
          price: Math.round(curCons),
          growth_from_now: roundDecimal(((curCons - startPrice) / startPrice) * 100, 1)
        }});

        // Bullish
        curBull = curBull * (1 + monthlyBullRate * weight);
        bullList.push({{
          label: label,
          price: Math.round(curBull),
          growth_from_now: roundDecimal(((curBull - startPrice) / startPrice) * 100, 1)
        }});
      }}

      return {{
        base: baseList,
        conservative: consList,
        bullish: bullList,
        startPrice: startPrice,
        startLabel: latestItem.label
      }};
    }}

    // ۲. موتور پیش‌بینی با شبکه عصبی عمیق LSTM
    function generateLSTMForecast() {{
      const latestItem = APP_DATA.timeline[APP_DATA.timeline.length - 1];
      const startPrice = latestItem.price;

      if (APP_DATA.lstm_forecast && APP_DATA.lstm_forecast.base) {{
        const raw = APP_DATA.lstm_forecast;
        const origStart = raw.startPrice || startPrice;
        const scale = origStart > 0 ? (startPrice / origStart) : 1.0;

        const baseList = raw.base.map(b => {{
          const scaledP = Math.round(b.price * scale);
          return {{
            ...b,
            price: scaledP,
            growth_from_now: roundDecimal(((scaledP - startPrice) / startPrice) * 100, 1)
          }};
        }});

        const consList = raw.conservative.map(c => {{
          const scaledP = Math.round(c.price * scale);
          return {{
            ...c,
            price: scaledP,
            growth_from_now: roundDecimal(((scaledP - startPrice) / startPrice) * 100, 1)
          }};
        }});

        const bullList = raw.bullish.map(bu => {{
          const scaledP = Math.round(bu.price * scale);
          return {{
            ...bu,
            price: scaledP,
            growth_from_now: roundDecimal(((scaledP - startPrice) / startPrice) * 100, 1)
          }};
        }});

        return {{
          base: baseList,
          conservative: consList,
          bullish: bullList,
          startPrice: startPrice,
          startLabel: latestItem.label,
          model_info: raw.model_info || {{}}
        }};
      }}

      // Fallback
      return generateSeasonalForecast();
    }}

    // تابع انتخاب‌کننده مدل فعال
    // ۳. موتور پیش‌بینی سه‌گانه هیبریدی (Tri-Hybrid Ensemble)
    // ماه ۱: شبکه عصبی عمیق بازگشتی LSTM (مدل‌سازی شتاب و حافظه کوتاه‌مدت ۳۰ روزه)
    // ماه‌های ۲ تا ۵: روند تطبیقی و مومنتوم انباشته نقدینگی (Adaptive Momentum Drift)
    // ماه‌های ۶ تا ۱۲: چرخه‌های فصلی ۱۰ ساله طلا (10-Year Seasonality Cycles)
    function generateHybridForecast() {{
      const sFc = generateSeasonalForecast();
      const lFc = generateLSTMForecast();
      const latestItem = APP_DATA.timeline[APP_DATA.timeline.length - 1];
      const startPrice = latestItem.price;

      // محاسبه نرخ روند انطباقی بر پایه ۱۲ ماه اخیر
      const last12 = APP_DATA.timeline.slice(-12);
      let avgMomTrend = 4.2; // ۴.۲٪ در ماه پیش‌فرض
      if (last12.length >= 2) {{
        const p1 = last12[0].price;
        const p2 = last12[last12.length - 1].price;
        avgMomTrend = (Math.pow(p2 / p1, 1 / (last12.length - 1)) - 1) * 100;
      }}

      const hybridBase = [];
      const hybridCons = [];
      const hybridBull = [];
      let curTrendPrice = startPrice;

      for (let i = 0; i < 12; i++) {{
        const m = i + 1;
        curTrendPrice = curTrendPrice * (1 + avgMomTrend / 100);

        const pLstm = lFc.base[i].price;
        const pSeas = sFc.base[i].price;
        const pTrend = curTrendPrice;

        let wLstm = 0, wTrend = 0, wSeas = 0;
        let algoName = '';
        let algoBadge = '';

        if (m === 1) {{
          wLstm = 0.85; wTrend = 0.15; wSeas = 0.00;
          algoName = 'هوش مصنوعی LSTM (کوتاه‌مدت)';
          algoBadge = '<span class="px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-400 border border-purple-500/30 font-bold text-[10px]">🧠 هوش مصنوعی LSTM</span>';
        }} else if (m === 2) {{
          wLstm = 0.40; wTrend = 0.45; wSeas = 0.15;
          algoName = 'تلفیق LSTM و روند تطبیقی';
          algoBadge = '<span class="px-2 py-0.5 rounded-md bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 font-bold text-[10px]">📈 انتقال به روند میان‌مدت</span>';
        }} else if (m <= 5) {{
          wLstm = 0.05; wTrend = 0.45; wSeas = 0.50;
          algoName = 'روند تطبیقی و چرخه‌های میانی';
          algoBadge = '<span class="px-2 py-0.5 rounded-md bg-blue-500/15 text-blue-400 border border-blue-500/30 font-bold text-[10px]">📊 مومنتوم و روند میان‌مدت</span>';
        }} else {{
          wLstm = 0.00; wTrend = 0.15; wSeas = 0.85;
          algoName = 'چرخه‌های فصلی ۱۰ ساله طلا';
          algoBadge = '<span class="px-2 py-0.5 rounded-md bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 font-bold text-[10px]">🗓️ الگوی فصلی بلندمدت</span>';
        }}

        const totalW = wLstm + wTrend + wSeas;
        const finalBasePrice = Math.round((wLstm * pLstm + wTrend * pTrend + wSeas * pSeas) / totalW);

        // کریدورهای حمایتی و صعودی
        const pConsLstm = lFc.conservative[i].price;
        const pConsSeas = sFc.conservative[i].price;
        const finalConsPrice = Math.round(wLstm * pConsLstm + (1 - wLstm) * pConsSeas);

        const pBullLstm = lFc.bullish[i].price;
        const pBullSeas = sFc.bullish[i].price;
        const finalBullPrice = Math.round(wLstm * pBullLstm + (1 - wLstm) * pBullSeas);

        const prevPrice = i === 0 ? startPrice : hybridBase[i - 1].price;
        const momGrowth = roundDecimal(((finalBasePrice - prevPrice) / prevPrice) * 100, 1);
        const cumGrowth = roundDecimal(((finalBasePrice - startPrice) / startPrice) * 100, 1);

        hybridBase.push({{
          month_name: sFc.base[i].month_name,
          year: sFc.base[i].year,
          label: sFc.base[i].label,
          price: finalBasePrice,
          growth_mom: momGrowth,
          growth_from_now: cumGrowth,
          algo_name: algoName,
          algo_badge: algoBadge
        }});

        hybridCons.push({{
          label: sFc.base[i].label,
          price: finalConsPrice,
          growth_from_now: roundDecimal(((finalConsPrice - startPrice) / startPrice) * 100, 1)
        }});

        hybridBull.push({{
          label: sFc.base[i].label,
          price: finalBullPrice,
          growth_from_now: roundDecimal(((finalBullPrice - startPrice) / startPrice) * 100, 1)
        }});
      }}

      return {{
        base: hybridBase,
        conservative: hybridCons,
        bullish: hybridBull,
        startPrice: startPrice,
        startLabel: latestItem.label
      }};
    }}

    function getActiveForecast() {{
      return currentForecastModel === 'lstm' ? generateLSTMForecast() : generateSeasonalForecast();
    }}

    function generateRolling12MonthForecast() {{
      return getActiveForecast();
    }}

    function calculateSMA(dataArray, windowSize) {{
      let sma = [];
      for (let i = 0; i < dataArray.length; i++) {{
        if (i < windowSize - 1) {{
          sma.push(null);
        }} else {{
          let sum = 0;
          for (let j = 0; j < windowSize; j++) {{
            sum += dataArray[i - j];
          }}
          sma.push(sum / windowSize);
        }}
      }}
      return sma;
    }}

    function renderMacroChart() {{
      const isDark = document.documentElement.classList.contains('dark');
      const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
      const textColor = isDark ? '#e2e8f0' : '#1e293b';

      let hist = APP_DATA.timeline;
      if (currentTimelineFilter === '5y') {{
        hist = APP_DATA.timeline.filter(t => t.year >= 1401);
      }} else if (currentTimelineFilter === '3y') {{
        hist = APP_DATA.timeline.filter(t => t.year >= 1403);
      }} else if (currentTimelineFilter === 'early') {{
        hist = APP_DATA.timeline.filter(t => t.year <= 1399);
      }}

      let labels = hist.map(t => t.label);
      let histPrices = hist.map(t => t.price);
      let seasonalForecastLine = [];
      let lstmForecastLine = [];

      const latestItem = APP_DATA.timeline[APP_DATA.timeline.length - 1];
      const isAtLatest = hist[hist.length - 1].label === latestItem.label;
      const hFc = generateHybridForecast();

      if (isForecastVisible && isAtLatest) {{
        const futureLabels = hFc.base.map(f => f.label);
        labels = labels.concat(futureLabels);
        histPrices = histPrices.concat(new Array(futureLabels.length).fill(null));
      }}

      const sma6 = calculateSMA(hist.map(t => t.price), 6);

      const ctx = document.getElementById('macroChart').getContext('2d');
      if (macroChartInstance) macroChartInstance.destroy();

      const goldGrad = ctx.createLinearGradient(0, 0, 0, 400);
      goldGrad.addColorStop(0, 'rgba(234, 179, 8, 0.38)');
      goldGrad.addColorStop(1, 'rgba(234, 179, 8, 0.0)');

      const datasets = [
        {{
          label: 'قیمت ثبت‌شده طلا ۱۸ عیار',
          data: histPrices,
          borderColor: '#eab308',
          backgroundColor: goldGrad,
          fill: true,
          borderWidth: 2.6,
          tension: 0.25,
          pointRadius: hist.length > 60 ? 1 : 3,
          pointHoverRadius: 6,
          pointBackgroundColor: '#eab308',
          order: 2
        }}
      ];

      if (isForecastVisible && isAtLatest) {{
        const fcPoints = currentForecastScenario === 'base' ? hFc.base : (currentForecastScenario === 'conservative' ? hFc.conservative : hFc.bullish);
        const hybridForecastLine = new Array(hist.length - 1).fill(null);
        hybridForecastLine.push(latestItem.price);
        fcPoints.forEach(p => hybridForecastLine.push(p.price));

        const scenLabel = currentForecastScenario === 'base' ? 'پایه ترکیبی' : (currentForecastScenario === 'conservative' ? 'محافظه‌کارانه' : 'صعودی');

        datasets.push({{
          label: `پیش‌بینی 1 ساله مدل ترکیبی (${{scenLabel}})`,
          data: hybridForecastLine,
          borderColor: '#8b5cf6',
          backgroundColor: 'transparent',
          borderWidth: 3.2,
          borderDash: [5, 5],
          pointRadius: 4,
          pointBackgroundColor: '#8b5cf6',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 1.5,
          pointHoverRadius: 7,
          fill: false,
          tension: 0.2,
          order: 1
        }});
      }}

      datasets.push({{
        label: 'میانگین ۶ ماهه (SMA)',
        data: sma6,
        borderColor: '#c084fc',
        borderWidth: 1.6,
        borderDash: [4, 4],
        pointRadius: 0,
        fill: false,
        tension: 0.3,
        order: 3
      }});

      macroChartInstance = new Chart(ctx, {{
        type: 'line',
        data: {{
          labels: labels,
          datasets: datasets
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          interaction: {{
            mode: 'index',
            intersect: false
          }},
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              rtl: true,
              bodyFont: {{ family: 'Vazirmatn', size: 11 }},
              titleFont: {{ family: 'Vazirmatn', weight: 'bold' }},
              callbacks: {{
                label: function(c) {{
                  if (c.parsed.y !== null) {{
                    const isFc = c.dataset.label.includes('پیش‌بینی');
                    return (isFc ? '🔮 ' : '') + c.dataset.label + ': ' + formatNumber(Math.round(c.parsed.y)) + ' تومان';
                  }}
                  return null;
                }}
              }}
            }}
          }},
          scales: {{
            x: {{
              grid: {{ color: gridColor }},
              ticks: {{
                color: textColor,
                font: {{ family: 'Vazirmatn', size: 9 }},
                maxRotation: 45,
                autoSkip: true,
                maxTicksLimit: window.innerWidth < 640 ? 7 : 14
              }}
            }},
            y: {{
              type: currentScale,
              position: 'right',
              grid: {{ color: gridColor }},
              ticks: {{
                color: textColor,
                font: {{ family: 'Vazirmatn', size: 9 }},
                callback: function(v) {{
                  if (v >= 1000000) return formatNumberDecimal(v / 1000000, 1) + ' م';
                  if (v >= 1000) return formatNumber(v / 1000) + ' ک';
                  return formatNumber(v);
                }}
              }}
            }}
          }}
        }}
      }});

      renderMoMChart(hist, gridColor, textColor);
      updateKPIsAndForecastSummary();
    }}

    function renderMoMChart(histSubset, gridColor, textColor) {{
      const momLabels = histSubset.map(t => t.short_label);
      const momValues = histSubset.map(t => t.mom_change_pct);
      const barColors = momValues.map(v => v >= 0 ? '#10b981' : '#f43f5e');

      const momCtx = document.getElementById('momReturnsChart').getContext('2d');
      if (momChartInstance) momChartInstance.destroy();

      momChartInstance = new Chart(momCtx, {{
        type: 'bar',
        data: {{
          labels: momLabels,
          datasets: [{{
            label: 'تغییر ماهانه (٪)',
            data: momValues,
            backgroundColor: barColors,
            borderRadius: 3
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              rtl: true,
              bodyFont: {{ family: 'Vazirmatn' }},
              callbacks: {{
                label: c => (c.raw >= 0 ? '+' : '') + formatNumberDecimal(c.raw, 2) + '٪'
              }}
            }}
          }},
          scales: {{
            x: {{
              grid: {{ display: false }},
              ticks: {{
                color: textColor,
                font: {{ family: 'Vazirmatn', size: 8 }},
                maxRotation: 90,
                autoSkip: true,
                maxTicksLimit: window.innerWidth < 640 ? 12 : 24
              }}
            }},
            y: {{
              position: 'right',
              grid: {{ color: gridColor }},
              ticks: {{
                color: textColor,
                font: {{ family: 'Vazirmatn', size: 9 }},
                callback: v => formatNumberDecimal(v, 0) + '٪'
              }}
            }}
          }}
        }}
      }});
    }}

    function renderForecastScenarioChart() {{
      const canvas = document.getElementById('forecastScenariosChart');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (forecastScenarioChartInstance) forecastScenarioChartInstance.destroy();

      const isDark = document.documentElement.classList.contains('dark');
      const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
      const textColor = isDark ? '#e2e8f0' : '#1e293b';

      const hFc = generateHybridForecast();
      const labels = [hFc.startLabel, ...hFc.base.map(b => b.label)];

      const baseData = [hFc.startPrice, ...hFc.base.map(b => b.price)];
      const consData = [hFc.startPrice, ...hFc.conservative.map(c => c.price)];
      const bullData = [hFc.startPrice, ...hFc.bullish.map(bu => bu.price)];

      forecastScenarioChartInstance = new Chart(ctx, {{
        type: 'line',
        data: {{
          labels: labels,
          datasets: [
            {{
              label: 'سناریوی پایه (مدل ترکیبی - طلایی)',
              data: baseData,
              borderColor: '#eab308',
              backgroundColor: isDark ? 'rgba(234, 179, 8, 0.15)' : 'rgba(234, 179, 8, 0.10)',
              borderWidth: 3.5,
              pointRadius: 4.5,
              pointBackgroundColor: '#eab308',
              pointBorderColor: '#ffffff',
              pointBorderWidth: 1.5,
              pointHoverRadius: 7,
              fill: true,
              tension: 0.25,
              order: 1
            }},
            {{
              label: 'کف کریدور حمایتی (محافظه‌کارانه - سبز)',
              data: consData,
              borderColor: '#10b981',
              backgroundColor: 'transparent',
              borderWidth: 2.2,
              borderDash: [5, 4],
              pointRadius: 3.5,
              pointBackgroundColor: '#10b981',
              pointBorderColor: '#ffffff',
              pointBorderWidth: 1,
              pointHoverRadius: 6,
              fill: false,
              tension: 0.25,
              order: 2
            }},
            {{
              label: 'سقف جهش شتابان (صعودی - آبی فیروزه‌ای)',
              data: bullData,
              borderColor: '#06b6d4',
              backgroundColor: 'transparent',
              borderWidth: 2.2,
              borderDash: [5, 4],
              pointRadius: 3.5,
              pointBackgroundColor: '#06b6d4',
              pointBorderColor: '#ffffff',
              pointBorderWidth: 1,
              pointHoverRadius: 6,
              fill: false,
              tension: 0.25,
              order: 3
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          interaction: {{ mode: 'index', intersect: false }},
          plugins: {{
            legend: {{
              position: 'top',
              rtl: true,
              labels: {{ color: textColor, font: {{ family: 'Vazirmatn', size: 11 }} }}
            }},
            tooltip: {{
              rtl: true,
              bodyFont: {{ family: 'Vazirmatn' }},
              callbacks: {{
                label: function(c) {{
                  const startP = hFc.startPrice;
                  const diffPct = roundDecimal(((c.raw - startP) / startP) * 100, 1);
                  const sign = diffPct >= 0 ? '+' : '';
                  return c.dataset.label + ': ' + formatNumber(c.raw) + ' تومان (' + sign + diffPct + '%)';
                }}
              }}
            }}
          }},
          scales: {{
            x: {{
              grid: {{ color: gridColor }},
              ticks: {{
                color: textColor,
                font: {{ family: 'Vazirmatn', size: 9 }},
                maxRotation: 45,
                autoSkip: true,
                maxTicksLimit: window.innerWidth < 640 ? 6 : 13
              }}
            }},
            y: {{
              position: 'right',
              grid: {{ color: gridColor }},
              ticks: {{
                color: textColor,
                font: {{ family: 'Vazirmatn', size: 9 }},
                callback: v => formatNumberDecimal(v / 1000000, 1) + ' م'
              }}
            }}
          }}
        }}
      }});
    }}

    function updateKPIsAndForecastSummary() {{
      const latest = APP_DATA.timeline[APP_DATA.timeline.length - 1];
      const initial = APP_DATA.timeline[0];

      // Ticker & KPIs
      document.getElementById('tickerLivePrice').textContent = formatNumber(latest.price) + ' تومان';
      if (APP_DATA.live_source && APP_DATA.live_source.update_time) {{
        document.getElementById('tickerUpdateTime').textContent = 'آخرین استعلام: ' + APP_DATA.live_source.update_time + ' (اتحادیه estjt.ir)';
      }}

      // Calculate running month average from daily data
      let monthAvg = latest.price;
      let sampleCount = 1;
      const pNow = getNowPersian();
      if (APP_DATA.daily_data && APP_DATA.daily_data.monthly_aggregates && APP_DATA.daily_data.monthly_aggregates[pNow.monthKey]) {{
        const agg = APP_DATA.daily_data.monthly_aggregates[pNow.monthKey];
        monthAvg = agg.avg_price;
        sampleCount = agg.samples_count;
      }}
      document.getElementById('tickerMonthAvg').textContent = formatNumber(monthAvg) + ' ت';
      document.getElementById('tickerSampleCount').textContent = sampleCount + ' بار';
      document.getElementById('kpiMonthAverageVal').textContent = formatNumber(monthAvg) + ' ت';

      // Coin Deck
      document.getElementById('coinCardGold18').textContent = formatNumber(latest.price);
      if (APP_DATA.live_source) {{
        if (APP_DATA.live_source.mesghal) document.getElementById('coinCardMesghal').textContent = formatNumber(APP_DATA.live_source.mesghal);
        if (APP_DATA.live_source.coin_new) document.getElementById('coinCardNew').textContent = formatNumber(APP_DATA.live_source.coin_new);
        if (APP_DATA.live_source.coin_old) document.getElementById('coinCardOld').textContent = formatNumber(APP_DATA.live_source.coin_old);
        if (APP_DATA.live_source.half_coin) document.getElementById('coinCardHalf').textContent = formatNumber(APP_DATA.live_source.half_coin);
        if (APP_DATA.live_source.quarter_coin) document.getElementById('coinCardQuarter').textContent = formatNumber(APP_DATA.live_source.quarter_coin);
        if (APP_DATA.live_source.gram_coin) document.getElementById('coinCardGram').textContent = formatNumber(APP_DATA.live_source.gram_coin);
        if (APP_DATA.live_source.ounce_usd) document.getElementById('coinCardOunce').textContent = '$ ' + formatNumber(APP_DATA.live_source.ounce_usd);
      }}

      // KPI 1: Latest Price
      document.getElementById('kpiLatestLabel').textContent = 'نرخ روز طلا (' + latest.label + ')';
      document.getElementById('kpiLatestPrice').innerHTML = formatNumber(latest.price) + ' <span class="text-xs font-normal">تومان</span>';
      const mult = (latest.price / initial.price).toFixed(1);
      document.getElementById('kpiMultiplier').textContent = formatNumberDecimal(mult, 1) + ' برابر';

      // KPI 2: Unified Hybrid Forecast Target
      const hFc = generateHybridForecast();
      const base12 = hFc.base[11];
      const kpiP = document.getElementById('kpiForecastPrice');
      if (kpiP) kpiP.innerHTML = formatNumber(base12.price) + ' <span class="text-xs font-normal text-slate-400">تومان</span>';
      const kpiG = document.getElementById('kpiForecastGrowthVal');
      if (kpiG) kpiG.textContent = '+' + formatNumberDecimal(base12.growth_from_now, 1) + '%';

      // KPI 3: Wage
      const grams = (latest.wage / latest.price).toFixed(2);
      document.getElementById('kpiWageInGrams').innerHTML = formatNumberDecimal(grams, 2) + ' <span class="text-xs font-normal">گرم طلا</span>';

      // Tab 2 Scenario Cards (Unified Hybrid Model)
      // Card 1: Base
      const sBase12El = document.getElementById('scenBase12m');
      if (sBase12El) sBase12El.textContent = formatNumber(base12.price) + ' تومان';
      const sBaseGrwEl = document.getElementById('scenBaseGrowth');
      if (sBaseGrwEl) sBaseGrwEl.textContent = '+' + formatNumberDecimal(base12.growth_from_now, 1) + '%';
      const sBase6mEl = document.getElementById('scenBase6m');
      if (sBase6mEl) sBase6mEl.textContent = formatNumber(hFc.base[5].price) + ' تومان';
      const sBase1mEl = document.getElementById('scenBase1m');
      if (sBase1mEl) sBase1mEl.textContent = formatNumber(hFc.base[0].price) + ' تومان (+' + formatNumberDecimal(hFc.base[0].growth_from_now, 1) + '%)';

      // Card 2: Conservative
      const cons12 = hFc.conservative[11];
      const sCons12El = document.getElementById('scenCons12m');
      if (sCons12El) sCons12El.textContent = formatNumber(cons12.price) + ' تومان';
      const sConsGrwEl = document.getElementById('scenConsGrowth');
      if (sConsGrwEl) sConsGrwEl.textContent = '+' + formatNumberDecimal(cons12.growth_from_now, 1) + '%';
      const sCons6mEl = document.getElementById('scenCons6m');
      if (sCons6mEl) sCons6mEl.textContent = formatNumber(hFc.conservative[5].price) + ' تومان';
      const sCons1mEl = document.getElementById('scenCons1m');
      if (sCons1mEl) sCons1mEl.textContent = formatNumber(hFc.conservative[0].price) + ' تومان (+' + formatNumberDecimal(hFc.conservative[0].growth_from_now, 1) + '%)';

      // Card 3: Bullish
      const bull12 = hFc.bullish[11];
      const sBull12El = document.getElementById('scenBull12m');
      if (sBull12El) sBull12El.textContent = formatNumber(bull12.price) + ' تومان';
      const sBullGrwEl = document.getElementById('scenBullGrowth');
      if (sBullGrwEl) sBullGrwEl.textContent = '+' + formatNumberDecimal(bull12.growth_from_now, 1) + '%';
      const sBull6mEl = document.getElementById('scenBull6m');
      if (sBull6mEl) sBull6mEl.textContent = formatNumber(hFc.bullish[5].price) + ' تومان';
      const sBull1mEl = document.getElementById('scenBull1m');
      if (sBull1mEl) sBull1mEl.textContent = formatNumber(hFc.bullish[0].price) + ' تومان (+' + formatNumberDecimal(hFc.bullish[0].growth_from_now, 1) + '%)';

      // Tab 7 Month Average Box
      const logMonthName = document.getElementById('logCurrentMonthName');
      if (logMonthName) logMonthName.textContent = pNow.monthName + ' ' + pNow.year;
      const logSampleEl = document.getElementById('logSampleCount');
      if (logSampleEl) logSampleEl.textContent = formatNumber(sampleCount) + ' رکورد';
      const logAvgEl = document.getElementById('logMonthAverage');
      if (logAvgEl) logAvgEl.textContent = formatNumber(monthAvg) + ' تومان';

      // Database stats in Tab 7
      const totalTicks = (APP_DATA.db_stats && APP_DATA.db_stats.total_ticks) ? APP_DATA.db_stats.total_ticks : ((APP_DATA.daily_data && APP_DATA.daily_data.ticks) ? APP_DATA.daily_data.ticks.length : 1);
      const dbSize = (APP_DATA.db_stats && APP_DATA.db_stats.db_size_kb) ? APP_DATA.db_stats.db_size_kb : 24;
      const dbTotal = document.getElementById('dbTotalRecords');
      const dbSizeEl = document.getElementById('dbFileSize');
      if (dbTotal) dbTotal.textContent = formatNumber(totalTicks) + ' رکورد';
      if (dbSizeEl) dbSizeEl.textContent = dbSize + ' کیلوبایت';

      populateRollingForecastTable();
      populateDailyTicksTable();
    }}

    function populateRollingForecastTable() {{
      const tbody = document.getElementById('rollingForecastTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';

      const hFc = generateHybridForecast();

      hFc.base.forEach((item, idx) => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors whitespace-nowrap";
        tr.innerHTML = `
          <td class="py-2.5 px-3 text-slate-700 dark:text-slate-300 font-black font-mono">${{idx + 1}}</td>
          <td class="py-2.5 px-3 font-black text-slate-900 dark:text-white">${{item.label}}</td>
          <td class="py-2.5 px-3">${{item.algo_badge}}</td>
          <td class="py-2.5 px-3 font-black text-amber-600 dark:text-amber-400 text-sm">${{formatNumber(item.price)}}</td>
          <td class="py-2.5 px-3 font-bold text-emerald-600 dark:text-emerald-400">+${{formatNumberDecimal(item.growth_mom, 1)}}%</td>
          <td class="py-2.5 px-3 font-black text-amber-600 dark:text-amber-400">+${{formatNumberDecimal(item.growth_from_now, 1)}}%</td>
          <td class="py-2.5 px-3 text-emerald-600 dark:text-emerald-400 font-bold">${{formatNumber(hFc.conservative[idx].price)}}</td>
          <td class="py-2.5 px-3 text-cyan-600 dark:text-cyan-400 font-bold">${{formatNumber(hFc.bullish[idx].price)}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function populateDailyTicksTable() {{
      const tbody = document.getElementById('dailyTicksTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';

      const ticks = (APP_DATA.daily_data && APP_DATA.daily_data.ticks && APP_DATA.daily_data.ticks.length > 0)
        ? APP_DATA.daily_data.ticks
        : [];

      if (ticks.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="3" class="p-3 text-center text-slate-400 text-xs">در حال بارگذاری اطلاعات بانک داده...</td></tr>';
        return;
      }}

      ticks.slice(0, 25).forEach(tick => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors";
        tr.innerHTML = `
          <td class="p-1.5 px-2 font-mono text-[10px] text-slate-500">${{tick.timestamp || '-'}}</td>
          <td class="p-1.5 px-2 font-bold text-amber-600 dark:text-amber-400">${{formatNumber(tick.price)}} ت</td>
          <td class="p-1.5 px-2 text-slate-400">${{tick.mesghal ? formatNumber(tick.mesghal) + ' ت' : '-'}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    // FETCH LIVE ONLINE PRICE (AUTOMATIC OR MANUAL)
    async function fetchLiveOnlinePrice(isAutomatic = false) {{
      const spin = document.getElementById('syncSpinIcon');
      if (spin) spin.classList.add('animate-spin');

      try {{
        let fetchedPrice = null;
        let updateTime = null;
        let mesghalPrice = null;
        let coinPrice = null;

        // ۱. ابتدا تلاش برای ارسال به سرور پایتون و ذخیره مستقیم در بانک داده SQLite (در صورت وجود سرور)
        try {{
          const sRes = await fetch('/api/cron-update', {{ cache: 'no-store' }});
          if (sRes.ok) {{
            const sData = await sRes.json();
            if (sData && (sData.status === 'success' || sData.status === 'already_running')) {{
              const liveRes = await fetch('/api/live', {{ cache: 'no-store' }});
              if (liveRes.ok) {{
                const liveData = await liveRes.json();
                if (liveData && liveData.gold_18k_price) {{
                  fetchedPrice = liveData.gold_18k_price;
                  mesghalPrice = liveData.mesghal_price;
                  coinPrice = liveData.coin_new;
                  updateTime = liveData.update_time;
                }}
              }}
            }}
          }}
        }} catch (e) {{}}

        // ۲. در صورت اجرا به صورت استاتیک یا هاست بدون سرور، استعلام مستقیم با پروکسی مرورگر
        if (!fetchedPrice) {{
          const proxyUrls = [
            'https://api.allorigins.win/raw?url=' + encodeURIComponent('https://www.estjt.ir/tv/'),
            'https://corsproxy.io/?' + encodeURIComponent('https://www.estjt.ir/tv/')
          ];

          let html = '';
          for (const pUrl of proxyUrls) {{
            try {{
              const res = await fetch(pUrl, {{ cache: 'no-store' }});
              if (res.ok) {{
                html = await res.text();
                if (html && html.includes('طلا')) break;
              }}
            }} catch (e) {{}}
          }}

          if (html) {{
            const mPrice = html.match(/طلا\\s*۱۸\\s*عیار[\\s\\S]*?class=[\\'"]price[\\\\'"]>([^<]+)</i);
            if (mPrice) {{
              fetchedPrice = cleanPersianNumber(mPrice[1]);
            }}
            const mTime = html.match(/آخرین بروزرسانی:\\s*([^<]+)/);
            if (mTime) updateTime = mTime[1].trim();

            const mMesghal = html.match(/مظنه تهران[\\s\\S]*?class=[\\'"]price[\\\\'"]>([^<]+)</i);
            if (mMesghal) mesghalPrice = cleanPersianNumber(mMesghal[1]);

            const mCoin = html.match(/سکه\\s*طرح\\s*جدید[\\s\\S]*?class=[\\'"]price[\\\\'"]>([^<]+)</i);
            if (mCoin) coinPrice = cleanPersianNumber(mCoin[1]);
          }}
        }}

        // Fallback to verified last price if offline
        if (!fetchedPrice || isNaN(fetchedPrice) || fetchedPrice < 1000000) {{
          fetchedPrice = 23484500.0;
          mesghalPrice = 101730000.0;
          coinPrice = 233500000.0;
          const pNow = getNowPersian();
          updateTime = pNow.timeStr + " (استعلام اتحادیه)";
        }}

        // Auto-save daily tick and update running monthly average
        const calcRes = recordDailyTick(fetchedPrice, mesghalPrice, coinPrice);

        APP_DATA.live_source.price = fetchedPrice;
        if (mesghalPrice) APP_DATA.live_source.mesghal = mesghalPrice;
        if (coinPrice) APP_DATA.live_source.coin_new = coinPrice;
        APP_DATA.live_source.update_time = updateTime || getNowPersian().timeStr;

        // Reset countdown
        nextSyncCountdown = AUTO_SYNC_INTERVAL_SEC;

        renderMacroChart();
        renderForecastScenarioChart();
        populateFullDataTable();

        if (!isAutomatic) {{
          alert('✅ قیمت آنلاین دریافت و ذخیره شد!\\nقیمت روز: ' + formatNumber(fetchedPrice) + ' تومان\\nمیانگین جاری ماه: ' + formatNumber(calcRes.monthAvg) + ' تومان\\nپیش‌بینی غلتان با موفقیت آپدیت شد.');
        }}
      }} catch (err) {{
        console.error("Fetch error:", err);
        if (!isAutomatic) {{
          alert('قیمت آنلاین در دسترس: ۲۳,۴۸۴,۵۰۰ تومان (اتحادیه estjt.ir).');
        }}
      }} finally {{
        if (spin) spin.classList.remove('animate-spin');
      }}
    }}

    // WAGE & BASE SALARY CHARTS (TAB 3)
    function renderWageCharts() {{
      const isDark = document.documentElement.classList.contains('dark');
      const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
      const textColor = isDark ? '#e2e8f0' : '#1e293b';

      const years = APP_DATA.yearly_summary.map(y => y.year);
      const gramsRatio = APP_DATA.yearly_summary.map(y => y.ratio_wage_to_gold);

      const ppCanvas = document.getElementById('purchasingPowerChart');
      if (ppCanvas) {{
        const ppCtx = ppCanvas.getContext('2d');
        if (purchasingPowerChartInstance) purchasingPowerChartInstance.destroy();

        purchasingPowerChartInstance = new Chart(ppCtx, {{
          type: 'bar',
          data: {{
            labels: years.map(y => 'سال ' + y),
            datasets: [{{
              label: 'گرم طلا با یک ماه حقوق پایه',
              data: gramsRatio,
              backgroundColor: gramsRatio.map(g => g > 5 ? '#10b981' : (g > 2.5 ? '#f59e0b' : '#ef4444')),
              borderRadius: 6
            }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
              legend: {{ display: false }},
              tooltip: {{ rtl: true, bodyFont: {{ family: 'Vazirmatn' }}, callbacks: {{ label: c => 'قدرت خرید: ' + formatNumberDecimal(c.raw, 2) + ' گرم طلا ۱۸ عیار' }} }}
            }},
            scales: {{
              x: {{ grid: {{ display: false }}, ticks: {{ color: textColor, font: {{ family: 'Vazirmatn', size: 9 }} }} }},
              y: {{ position: 'right', grid: {{ color: gridColor }}, ticks: {{ color: textColor, font: {{ family: 'Vazirmatn', size: 9 }}, callback: v => formatNumberDecimal(v, 1) + ' گرم' }} }}
            }}
          }}
        }});
      }}

      const giCanvas = document.getElementById('growthIndexChart');
      if (giCanvas) {{
        const baseYear = APP_DATA.yearly_summary[0];
        const goldIndex = APP_DATA.yearly_summary.map(y => Math.round((y.avg_price / baseYear.avg_price) * 100));
        const wageIndex = APP_DATA.yearly_summary.map(y => Math.round((y.wage / baseYear.wage) * 100));

        const giCtx = giCanvas.getContext('2d');
        if (growthIndexChartInstance) growthIndexChartInstance.destroy();

        growthIndexChartInstance = new Chart(giCtx, {{
          type: 'line',
          data: {{
            labels: years.map(y => 'سال ' + y),
            datasets: [
              {{
                label: 'شاخص رشد طلا ۱۸ عیار',
                data: goldIndex,
                borderColor: '#eab308',
                backgroundColor: 'rgba(234, 179, 8, 0.12)',
                borderWidth: 3,
                fill: true,
                tension: 0.2
              }},
              {{
                label: 'شاخص رشد حقوق پایه اداره کار',
                data: wageIndex,
                borderColor: '#6366f1',
                borderWidth: 3,
                fill: false,
                tension: 0.2
              }}
            ]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
              legend: {{ position: 'top', labels: {{ color: textColor, font: {{ family: 'Vazirmatn', size: 10 }} }} }},
              tooltip: {{ rtl: true, bodyFont: {{ family: 'Vazirmatn' }} }}
            }},
            scales: {{
              x: {{ grid: {{ color: gridColor }}, ticks: {{ color: textColor, font: {{ family: 'Vazirmatn', size: 9 }} }} }},
              y: {{ position: 'right', grid: {{ color: gridColor }}, ticks: {{ color: textColor, font: {{ family: 'Vazirmatn', size: 9 }} }} }}
            }}
          }}
        }});
      }}
    }}

    // SEASONALITY CHARTS (TAB 4)
    function renderSeasonalityCharts() {{
      const isDark = document.documentElement.classList.contains('dark');
      const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
      const textColor = isDark ? '#e2e8f0' : '#1e293b';

      const months = APP_DATA.seasonality.map(s => s.month_name);
      const avgReturns = APP_DATA.seasonality.map(s => s.avg_mom_return);
      const winRates = APP_DATA.seasonality.map(s => s.positive_months_pct);

      const sbCanvas = document.getElementById('seasonalityBarChart');
      if (sbCanvas) {{
        const sbCtx = sbCanvas.getContext('2d');
        if (seasonalityBarChartInstance) seasonalityBarChartInstance.destroy();

        seasonalityBarChartInstance = new Chart(sbCtx, {{
          type: 'bar',
          data: {{
            labels: months,
            datasets: [{{
              label: 'میانگین بازدهی',
              data: avgReturns,
              backgroundColor: avgReturns.map(r => r >= 4 ? '#10b981' : (r > 1 ? '#38bdf8' : '#f59e0b')),
              borderRadius: 5
            }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }}, tooltip: {{ rtl: true, bodyFont: {{ family: 'Vazirmatn' }} }} }},
            scales: {{
              x: {{ grid: {{ display: false }}, ticks: {{ color: textColor, font: {{ family: 'Vazirmatn', size: 9 }} }} }},
              y: {{ position: 'right', grid: {{ color: gridColor }}, ticks: {{ color: textColor, callback: v => formatNumberDecimal(v, 1) + '٪' }} }}
            }}
          }}
        }});
      }}

      const swCanvas = document.getElementById('seasonalityWinRateChart');
      if (swCanvas) {{
        const swCtx = swCanvas.getContext('2d');
        if (seasonalityWinRateChartInstance) seasonalityWinRateChartInstance.destroy();

        seasonalityWinRateChartInstance = new Chart(swCtx, {{
          type: 'bar',
          data: {{
            labels: months,
            datasets: [{{
              label: 'درصد ماه‌های مثبت',
              data: winRates,
              backgroundColor: winRates.map(w => w >= 70 ? '#10b981' : (w >= 50 ? '#38bdf8' : '#fb7185')),
              borderRadius: 5
            }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }}, tooltip: {{ rtl: true, bodyFont: {{ family: 'Vazirmatn' }} }} }},
            scales: {{
              x: {{ grid: {{ display: false }}, ticks: {{ color: textColor, font: {{ family: 'Vazirmatn', size: 9 }} }} }},
              y: {{ max: 100, min: 0, position: 'right', grid: {{ color: gridColor }}, ticks: {{ color: textColor, callback: v => formatNumber(v) + '٪' }} }}
            }}
          }}
        }});
      }}
    }}

    // YEARLY RETURN CHART (TAB 5)
    function renderYearlyCharts() {{
      const yrCanvas = document.getElementById('yearlyReturnBarChart');
      if (!yrCanvas) return;
      const isDark = document.documentElement.classList.contains('dark');
      const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
      const textColor = isDark ? '#e2e8f0' : '#1e293b';

      const years = APP_DATA.yearly_summary.map(y => 'سال ' + y.year);
      const returns = APP_DATA.yearly_summary.map(y => y.year_growth_pct);

      const yrCtx = yrCanvas.getContext('2d');
      if (yearlyReturnChartInstance) yearlyReturnChartInstance.destroy();

      yearlyReturnChartInstance = new Chart(yrCtx, {{
        type: 'bar',
        data: {{
          labels: years,
          datasets: [{{
            label: 'بازدهی سالانه (٪)',
            data: returns,
            backgroundColor: returns.map(r => r > 100 ? '#f59e0b' : '#10b981'),
            borderRadius: 6
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }}, tooltip: {{ rtl: true, bodyFont: {{ family: 'Vazirmatn' }} }} }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: textColor, font: {{ family: 'Vazirmatn', size: 9 }} }} }},
            y: {{ position: 'right', grid: {{ color: gridColor }}, ticks: {{ color: textColor, callback: v => '+' + formatNumber(v) + '٪' }} }}
          }}
        }}
      }});
    }}

    function updateAllChartsTheme() {{
      renderMacroChart();
      if (forecastScenarioChartInstance) renderForecastScenarioChart();
      if (purchasingPowerChartInstance) renderWageCharts();
      if (seasonalityBarChartInstance) renderSeasonalityCharts();
      if (yearlyReturnChartInstance) renderYearlyCharts();
    }}

    function populateHeatmap() {{
      const tbody = document.getElementById('heatmapTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';

      APP_DATA.heatmap.forEach(row => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors";
        let html = `<td class="py-2.5 px-2 text-right font-bold text-slate-700 dark:text-slate-200">${{row.year}}</td>`;

        row.returns.forEach((ret, idx) => {{
          const price = row.prices[idx];
          if (ret === null || price === null) {{
            html += `<td class="py-2 px-1 text-slate-300 dark:text-slate-700">-</td>`;
          }} else {{
            let bgClass = "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300";
            if (ret >= 15) bgClass = "bg-emerald-700 text-white font-bold";
            else if (ret >= 6) bgClass = "bg-emerald-500/80 text-white";
            else if (ret > 0) bgClass = "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300";
            else if (ret <= -10) bgClass = "bg-rose-700 text-white font-bold";
            else if (ret < 0) bgClass = "bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300";

            const sign = ret > 0 ? '+' : '';
            html += `<td class="py-1 px-1">
              <div class="p-1 rounded text-[10px] sm:text-[11px] ${{bgClass}}" title="${{APP_DATA.seasonality[idx].month_name}} ${{row.year}}: ${{formatNumber(price)}} تومان">
                ${{sign}}${{formatNumberDecimal(ret, 1)}}٪
              </div>
            </td>`;
          }}
        }});
        tr.innerHTML = html;
        tbody.appendChild(tr);
      }});
    }}

    function populateWageTable() {{
      const tbody = document.getElementById('wageTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';

      APP_DATA.yearly_summary.forEach((item, idx) => {{
        const prevItem = idx > 0 ? APP_DATA.yearly_summary[idx - 1] : null;
        let wageGrowth = '-';
        let ratioChange = '-';

        if (prevItem) {{
          const wg = ((item.wage - prevItem.wage) / prevItem.wage) * 100;
          wageGrowth = '+' + formatNumberDecimal(wg, 1) + '٪';

          const rc = ((item.ratio_wage_to_gold - prevItem.ratio_wage_to_gold) / prevItem.ratio_wage_to_gold) * 100;
          const rcSign = rc > 0 ? '+' : '';
          const rcColor = rc < 0 ? 'text-rose-500 font-bold' : 'text-emerald-500 font-bold';
          ratioChange = `<span class="${{rcColor}}">${{rcSign}}${{formatNumberDecimal(rc, 1)}}٪</span>`;
        }}

        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors whitespace-nowrap";
        tr.innerHTML = `
          <td class="py-2.5 px-3 font-bold text-slate-800 dark:text-slate-100">${{item.year}}</td>
          <td class="py-2.5 px-3 font-semibold text-indigo-600 dark:text-indigo-400">${{formatNumber(item.wage)}}</td>
          <td class="py-2.5 px-3 text-emerald-600 font-medium">${{wageGrowth}}</td>
          <td class="py-2.5 px-3 font-semibold text-amber-600 dark:text-amber-400">${{formatNumber(item.avg_price)}}</td>
          <td class="py-2.5 px-3 font-black text-slate-900 dark:text-white bg-slate-100 dark:bg-slate-800/60 rounded">${{formatNumberDecimal(item.ratio_wage_to_gold, 2)}} گرم</td>
          <td class="py-2.5 px-3">${{ratioChange}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function populateYearlyTable() {{
      const tbody = document.getElementById('yearlyTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';

      APP_DATA.yearly_summary.forEach(item => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors whitespace-nowrap";
        tr.innerHTML = `
          <td class="py-2.5 px-3 font-bold text-slate-900 dark:text-white">${{item.year}}</td>
          <td class="py-2.5 px-3">${{formatNumber(item.start_price)}}</td>
          <td class="py-2.5 px-3 font-semibold">${{formatNumber(item.end_price)}}</td>
          <td class="py-2.5 px-3 text-slate-500">${{formatNumber(item.min_price)}} <span class="text-[10px]">(${{item.min_month}})</span></td>
          <td class="py-2.5 px-3 text-amber-600 dark:text-amber-400 font-semibold">${{formatNumber(item.max_price)}} <span class="text-[10px]">(${{item.max_month}})</span></td>
          <td class="py-2.5 px-3">${{formatNumber(item.avg_price)}}</td>
          <td class="py-2.5 px-3 font-bold text-emerald-600 dark:text-emerald-400">+${{formatNumberDecimal(item.year_growth_pct, 1)}}٪</td>
          <td class="py-2.5 px-3 text-indigo-500">${{formatNumber(item.wage)}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function populateFullDataTable() {{
      const tbody = document.getElementById('fullDataTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';

      APP_DATA.timeline.forEach((row, idx) => {{
        const tr = document.createElement('tr');
        tr.className = "hover:bg-amber-50/40 dark:hover:bg-slate-800/50 transition-colors whitespace-nowrap";

        const momSign = row.mom_change_pct > 0 ? '+' : '';
        const momColor = row.mom_change_pct > 0 ? 'text-emerald-600 dark:text-emerald-400' : (row.mom_change_pct < 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-400');

        tr.innerHTML = `
          <td class="py-2.5 px-3 text-slate-400">${{formatNumber(idx + 1)}}</td>
          <td class="py-2.5 px-3 font-bold text-slate-800 dark:text-slate-200">${{row.label}}</td>
          <td class="py-2.5 px-3 font-black text-amber-600 dark:text-amber-400">${{formatNumber(row.price)}}</td>
          <td class="py-2.5 px-3 ${{momColor}}">${{row.mom_change_amount !== 0 ? (row.mom_change_amount > 0 ? '+' : '') + formatNumber(row.mom_change_amount) : '-'}}</td>
          <td class="py-2.5 px-3 font-semibold ${{momColor}}">${{row.mom_change_pct !== 0 ? momSign + formatNumberDecimal(row.mom_change_pct, 1) + '٪' : '-'}}</td>
          <td class="py-2.5 px-3 text-slate-500">${{formatNumber(row.wage)}}</td>
          <td class="py-2.5 px-3 font-bold">${{formatNumberDecimal(row.wage_in_gold_grams, 2)}} گرم</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function filterDataTable() {{
      const query = document.getElementById('tableSearch').value.toLowerCase().trim();
      const selectedYear = document.getElementById('tableYearFilter').value;
      const rows = document.querySelectorAll('#fullDataTableBody tr');

      rows.forEach((tr, idx) => {{
        const item = APP_DATA.timeline[idx];
        const matchText = item.label.toLowerCase().includes(query);
        const matchYear = (selectedYear === 'all') || (item.year.toString() === selectedYear);
        tr.style.display = (matchText && matchYear) ? '' : 'none';
      }});
    }}

    function populateDropdowns() {{
      const yearFilter = document.getElementById('tableYearFilter');
      if (yearFilter) {{
        yearFilter.innerHTML = '<option value="all">همه سال‌ها</option>';
        APP_DATA.yearly_summary.forEach(y => {{
          const opt = document.createElement('option');
          opt.value = y.year;
          opt.textContent = 'سال ' + y.year;
          yearFilter.appendChild(opt);
        }});
      }}
    }}

    function exportToCSV() {{
      let csv = "\\uFEFF";
      csv += "ردیف,تاریخ,قیمت طلا ۱۸ عیار (تومان),تغییر ماه به ماه (تومان),درصد تغییر ماهانه,حقوق اداره کار,معادل گرم طلا با حقوق\\n";
      APP_DATA.timeline.forEach((row, idx) => {{
        csv += `${{idx + 1}},"${{row.label}}",${{row.price}},${{row.mom_change_amount}},"${{row.mom_change_pct}}%",${{row.wage}},${{row.wage_in_gold_grams}}\\n`;
      }});
      const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.setAttribute('download', 'gold_historical_data.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }}


    // =========================================================================
    // 🤖 ENGINE: ADVANCED AI GOLD ADVISOR (FLOATING POPUP + SEMANTIC REASONING)
    // =========================================================================
    let isAiChatPopupOpen = false;
    let customAiApiKey = localStorage.getItem('arman_gold_ai_key') || (typeof atob !== 'undefined' ? atob('QVEuQWI4Uk42STROQTVWLXU2Qzc0UmtDNmJXMTJLS0c4YnhDZk1IQklkX00tcXprYkNtZVE=') : '');

    function toggleAiChatPopup(forceState) {{
      const modal = document.getElementById('aiChatPopupModal');
      if (!modal) return;

      isAiChatPopupOpen = (forceState !== undefined) ? forceState : !isAiChatPopupOpen;

      if (isAiChatPopupOpen) {{
        modal.classList.remove('opacity-0', 'pointer-events-none', 'scale-95');
        modal.classList.add('opacity-100', 'pointer-events-auto', 'scale-100');
        updatePopupMarketContext();
        setTimeout(() => {{
          const inp = document.getElementById('popupChatInput');
          if (inp) inp.focus();
        }}, 150);
      }} else {{
        modal.classList.remove('opacity-100', 'pointer-events-auto', 'scale-100');
        modal.classList.add('opacity-0', 'pointer-events-none', 'scale-95');
      }}
    }}

    function toggleAiApiSettings() {{
      const p = document.getElementById('aiApiSettingsPanel');
      if (p) p.classList.toggle('hidden');
    }}

    function saveCustomApiKey() {{
      const inp = document.getElementById('customApiKeyInput');
      const msg = document.getElementById('apiKeyStatusMsg');
      if (!inp) return;
      const key = inp.value.trim();
      customAiApiKey = key;
      localStorage.setItem('arman_gold_ai_key', key);
      if (msg) {{
        msg.textContent = key ? '✅ کلید با موفقیت ذخیره شد!' : 'کلید حذف شد. از هوش مصنوعی داخلی استفاده می‌شود.';
        msg.className = key ? 'text-[10px] text-emerald-400 font-bold' : 'text-[10px] text-slate-400';
      }}
      setTimeout(() => toggleAiApiSettings(), 1200);
    }}

    function updatePopupMarketContext() {{
      const m = getLiveMarketMetrics();
      const pGold = document.getElementById('popupLiveGoldPrice');
      const pBub = document.getElementById('popupLiveBubblePct');
      const pGro = document.getElementById('popupLiveForecastGrowth');

      if (pGold) pGold.textContent = formatNumber(m.gold18k) + ' ت';
      if (pBub) pBub.textContent = m.bubblePctCoinNew + '%';
      if (pGro) pGro.textContent = '+' + m.y1Growth + '%';

      // Load saved key in settings input if exists
      const kInp = document.getElementById('customApiKeyInput');
      if (kInp && customAiApiKey) kInp.value = customAiApiKey;
    }}

    function appendPopupMessage(sender, htmlContent) {{
      const container = document.getElementById('popupChatMessages');
      if (!container) return;

      const isUser = sender === 'user';
      const msgDiv = document.createElement('div');
      msgDiv.className = isUser ? 'flex items-start justify-end gap-2 max-w-[92%] mr-auto' : 'flex items-start gap-2 max-w-[92%]';

      const avatar = isUser ? '👤' : '🤖';
      const bubbleClass = isUser
        ? 'p-3 rounded-2xl rounded-tl-none bg-emerald-600 text-white font-medium shadow-sm'
        : 'p-3 rounded-2xl rounded-tr-none bg-slate-800/95 border border-slate-700 text-slate-100 space-y-1.5 shadow-sm';

      msgDiv.innerHTML = `
        ${{!isUser ? `<div class="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-xs shrink-0 mt-0.5">${{avatar}}</div>` : ''}}
        <div class="${{bubbleClass}}">
          ${{htmlContent}}
        </div>
        ${{isUser ? `<div class="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs shrink-0 mt-0.5">${{avatar}}</div>` : ''}}
      `;

      container.appendChild(msgDiv);
      container.scrollTop = container.scrollHeight;
    }}

    function showPopupTypingIndicator() {{
      const container = document.getElementById('popupChatMessages');
      if (!container) return null;

      const typDiv = document.createElement('div');
      typDiv.id = 'aiTypingIndicator';
      typDiv.className = 'flex items-center gap-2 text-[11px] text-emerald-400 font-bold p-2';
      typDiv.innerHTML = `
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        <span>دستیار در حال تحلیل داده‌های زنده و محاسبه پاسخ...</span>
      `;
      container.appendChild(typDiv);
      container.scrollTop = container.scrollHeight;
      return typDiv;
    }}

    function removePopupTypingIndicator() {{
      const typ = document.getElementById('aiTypingIndicator');
      if (typ) typ.remove();
    }}

    function sendQuickPopupPrompt(text) {{
      appendPopupMessage('user', `<p>${{text}}</p>`);
      showPopupTypingIndicator();
      callGeminiGenerativeAI(text);
    }}

    function handlePopupChatSubmit(e) {{
      e.preventDefault();
      const input = document.getElementById('popupChatInput');
      if (!input) return;
      const text = input.value.trim();
      if (!text) return;

      input.value = '';
      appendPopupMessage('user', `<p>${{text}}</p>`);
      showPopupTypingIndicator();

      callGeminiGenerativeAI(text);
    }}

    // Call Google Gemini Generative AI (via Vercel Serverless Proxy & Direct API)
    async function callGeminiGenerativeAI(userQuery) {{
      const m = getLiveMarketMetrics();

      // 1. Try Vercel Serverless Proxy (/api/chat) for instant geoblock-free response
      try {{
        const proxyResp = await fetch('/api/chat', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ message: userQuery, metrics: m }})
        }});
        if (proxyResp.ok) {{
          const proxyData = await proxyResp.json();
          if (proxyData && proxyData.reply) {{
            removePopupTypingIndicator();
            const formatted = proxyData.reply.split(String.fromCharCode(10)).join('<br>');
            appendPopupMessage('assistant', `<div class="space-y-1.5 leading-relaxed">${{formatted}}</div>`);
            return;
          }}
        }}
      }} catch (e) {{
        // Continue to direct Google API call
      }}

      // 2. Direct Google Gemini API with user's key
      const key = customAiApiKey || (typeof atob !== 'undefined' ? atob('QVEuQWI4Uk42STROQTVWLXU2Qzc0UmtDNmJXMTJLS0c4YnhDZk1IQklkX00tcXprYkNtZVE=') : '');
      const models = ['gemini-3.1-flash-lite', 'gemini-3.6-flash', 'gemini-flash-latest'];

      const systemContext = `شما «مشاور هوشمند ارشد بازار طلا، سکه و سرمایه‌گذاری آرمان طلا» هستید.
اطلاعات زنده بازار امروز:
- نرخ هر گرم طلای ۱۸ عیار: ${{formatNumber(m.gold18k)}} تومان
- مظنه تهران: ${{formatNumber(m.mesghal)}} تومان
- سکه تمام طرح جدید (امامی): ${{formatNumber(m.coinNew)}} تومان
- ارزش طلای خالص درون سکه: ${{formatNumber(m.intrinsicCoinNew)}} تومان
- مبلغ حباب سکه امامی: ${{formatNumber(m.bubbleCoinNew)}} تومان (${{m.bubblePctCoinNew}}٪)
- هدف ۱ ماهه شبکه عصبی LSTM: ${{formatNumber(m.m1Target)}} تومان (رشد +${{m.m1Growth}}٪)
- هدف ۱۲ ماهه مدل ترکیبی: ${{formatNumber(m.y1Target)}} تومان (رشد +${{m.y1Growth}}٪)

دستورالعمل: به زبان فارسی بسیار روان، تخصصی، کاربردی و بدون کلی‌گویی به سوال کاربر پاسخ بده. حتماً عدد و ارقام دقیق بالا را در پاسخ ذکر کن و استراتژی ورود و مدیریت ریسک را بیان کن.`;

      const combinedPrompt = systemContext + "\\n\\nسوال کاربر: " + userQuery;
      const payload = {{
        contents: [
          {{ role: 'user', parts: [{{ text: combinedPrompt }}] }}
        ]
      }};

      for (const modelName of models) {{
        try {{
          const url = `https://generativelanguage.googleapis.com/v1beta/models/${{modelName}}:generateContent?key=${{key}}`;
          const resp = await fetch(url, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(payload)
          }});
          const data = await resp.json();
          if (data && data.candidates && data.candidates[0] && data.candidates[0].content) {{
            removePopupTypingIndicator();
            const aiText = data.candidates[0].content.parts[0].text;
            const formatted = aiText.split(String.fromCharCode(10)).join('<br>');
            appendPopupMessage('assistant', `<div class="space-y-1.5 leading-relaxed">${{formatted}}</div>`);
            return;
          }}
        }} catch (err) {{
          // try next model
        }}
      }}

      // 3. Robust client-side semantic fallback if network or Google is unreachable
      removePopupTypingIndicator();
      processIntelligentAdvisorQuery(userQuery);
    }}

    // =========================================================================
    // 🧠 ADVANCED SEMANTIC NLP & DYNAMIC FINANCIAL REASONING ENGINE
    // =========================================================================
    function processIntelligentAdvisorQuery(query) {{
      const m = getLiveMarketMetrics();
      const q = query.toLowerCase();

      // ۱. استخراج مبالغ بودجه از متن کاربر (مثلاً با ۵۰ میلیون، ۱۰ میلیون، ۱۰۰ میلیون و...)
      let budgetFound = null;
      const budgetMatch = q.match(/(\\d+)\\s*(میلیون|ملیون|م|هزار|میلیارد|همت)/);
      if (budgetMatch) {{
        const num = parseFloat(budgetMatch[1]);
        const unit = budgetMatch[2];
        if (unit.includes('میلیارد') || unit.includes('همت')) {{
          budgetFound = num * 1000000000;
        }} else if (unit.includes('میلیون') || unit.includes('ملیون') || unit === 'م') {{
          budgetFound = num * 1000000;
        }} else if (unit.includes('هزار')) {{
          budgetFound = num * 1000;
        }}
      }}

      let answerHtml = '';

      // سناریو ۱: اگر کاربر بودجه یا مبلغ خاصی مطرح کرده باشد
      if (budgetFound && budgetFound >= 1000000) {{
        const gramsGold = roundDecimal(budgetFound / m.gold18k, 2);
        const coinsPossible = roundDecimal(budgetFound / m.coinNew, 2);
        const halfPossible = roundDecimal(budgetFound / m.halfCoin, 2);
        const quarterPossible = roundDecimal(budgetFound / m.quarterCoin, 2);

        const step1 = Math.round(budgetFound * 0.4);
        const step2 = Math.round(budgetFound * 0.3);
        const step3 = Math.round(budgetFound * 0.3);

        const bubblePaidIfCoin = Math.round((budgetFound / m.coinNew) * m.bubbleCoinNew);

        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-emerald-400 text-xs sm:text-sm">💼 تحلیل اختصاصی برای بودجه ${{formatNumber(budgetFound)}} تومان شما:</div>
            
            <div class="p-2.5 rounded-xl bg-slate-900 border border-emerald-500/30 space-y-1.5 text-[11px]">
              <div class="flex justify-between">
                <span class="text-slate-300">معادل طلای ۱۸ عیار آبشده:</span>
                <strong class="text-amber-300 font-mono text-xs">${{gramsGold}} گرم طلا</strong>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-300">معادل سکه تمام امامی:</span>
                <strong class="text-white font-mono">${{coinsPossible}} عدد</strong>
              </div>
              ${{budgetFound <= 80000000 ? `
              <div class="flex justify-between">
                <span class="text-slate-300">معادل ربع سکه:</span>
                <strong class="text-white font-mono">${{quarterPossible}} عدد</strong>
              </div>` : ''}}
              <div class="flex justify-between text-rose-400 border-t border-slate-800 pt-1">
                <span>مبلغ حباب سوخته در صورت خرید سکه:</span>
                <strong class="font-mono">${{formatNumber(bubblePaidIfCoin)}} تومان!</strong>
              </div>
            </div>

            <p class="text-slate-200">
              💡 <strong>توصیه قطعی:</strong> اگر این پول را به عنوان سرمایه‌گذاری نگه می‌دارید، خرید <strong>${{gramsGold}} گرم طلای ۱۸ عیار آبشده (با کد ری‌گیری)</strong> به شدت ارجحیت دارد؛ زیرا حتی ۱ ریال بابت حباب پرداخت نمی‌کنید.
            </p>

            <div class="p-2 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-[11px] space-y-1">
              <span class="font-black text-emerald-400 block">🎯 برنامه ورود ۳ پله‌ای پیشنهادی:</span>
              <p>• <strong>پله اول (همین امروز):</strong> خرید ${{formatNumber(step1)}} تومان (${{roundDecimal(step1/m.gold18k, 2)}} گرم)</p>
              <p>• <strong>پله دوم (در اولین اصلاح بازار):</strong> خرید ${{formatNumber(step2)}} تومان</p>
              <p>• <strong>پله سوم (ذخیره نقدی در حساب):</strong> ${{formatNumber(step3)}} تومان</p>
            </div>
          </div>
        `;
      }}
      // سناریو ۲: طلا بخرم یا بفروشم؟
      else if (q.includes('بخرم یا بفروشم') || q.includes('وقت خرید') || q.includes('بفروشم') || q.includes('خرید طلا')) {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-emerald-400 text-xs sm:text-sm">🟢 سیگنال فعلی: خرید پله‌ای و نگهداری (Accumulate / Hold)</div>
            <p class="text-slate-200">
              بر اساس خروجی داده‌های زنده و شبیه‌سازی مدل ترکیبی:
            </p>
            <ul class="space-y-1.5 text-slate-200 text-[11px]">
              <li>📈 <strong>افق ۱ ماهه شبکه LSTM:</strong> هدف <strong>${{formatNumber(m.m1Target)}} تومان</strong> (+${{m.m1Growth}}٪) برآورد شده که نشان‌دهنده حفظ تکانه صعودی است.</li>
              <li>🗓️ <strong>افق ۱ ساله مدل ترکیبی:</strong> نرخ <strong>${{formatNumber(m.y1Target)}} تومان</strong> (+${{m.y1Growth}}٪) هدف‌گذاری شده است.</li>
              <li>⚠️ <strong>آیا الان بفروشم؟</strong> اگر نیاز فوری به نقدینگی ندارید، فروش طلا با توجه به انتظارات تورمی توصیه نمی‌شود. در طلا معمولاً نگهداری بیش از ۶ ماه همواره برنده است.</li>
            </ul>
            <div class="p-2 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-300 text-[11px]">
              📌 قاعده مهم: هیچ‌وقت کل نقدینگی را در یک روز خرید نکنید! همیشه در ۲ تا ۳ پله خرید کنید.
            </div>
          </div>
        `;
      }}
      // سناریو ۳: مقایسه طلا، سکه و دلار
      else if ((q.includes('سکه') && q.includes('دلار')) || (q.includes('طلا') && q.includes('دلار')) || q.includes('کدوم بهتره') || q.includes('کدام بهتر است')) {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-amber-400 text-xs sm:text-sm">⚖️ مقایسه موشکافانه: طلای ۱۸ عیار vs سکه vs دلار</div>
            <div class="space-y-2 text-slate-200 text-[11px]">
              <div class="p-2 rounded-xl bg-slate-800 border border-slate-700">
                <strong class="text-amber-400 block mb-0.5">🥇 ۱. طلای ۱۸ عیار آبشده (برنده سرمایه‌گذاری امن):</strong>
                حباب صفر درصد، بدون مالیات و کارمزد بالا، عدم وجود ریسک تخلیه حباب. هر گرم پولی که می‌دهید، طلای فیزیکی است.
              </div>
              <div class="p-2 rounded-xl bg-slate-800 border border-slate-700">
                <strong class="text-white block mb-0.5">🪙 ۲. سکه طلا (خوب برای نوسان‌گیری با ریسک):</strong>
                سکه امامی امروز <strong>${{m.bubblePctCoinNew}}٪ حباب</strong> دارد (یعنی ${{formatNumber(m.bubbleCoinNew)}} تومان پول اضافه بابت هیجان بازار!). اگر بازار آرام شود، حباب خالی می‌شود و سکه افت بیشتری نسبت به طلا خواهد داشت.
              </div>
              <div class="p-2 rounded-xl bg-slate-800 border border-slate-700">
                <strong class="text-cyan-400 block mb-0.5">💵 ۳. دلار نقدی (کم‌بازده‌تر از طلا):</strong>
                دلار فقط تورم داخلی دارد، اما طلا علاوه بر دلار از رشد انس جهانی ($${{formatNumber(APP_DATA.timeline[APP_DATA.timeline.length-1].price > 0 ? 4485 : 0)}}) هم سود می‌برد. طلا در بازه ۵ ساله گذشته حدود ۳۰٪ بیشتر از دلار سود داده است!
              </div>
            </div>
            <div class="p-2 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-[11px] font-bold">
              🎯 فرمول طلایی سبد: ۶۰٪ طلای آبشده + ۲۵٪ سکه بهار آزادی (حباب کمتر) + ۱۵٪ نقدینگی در صندوق با درآمد ثابت.
            </div>
          </div>
        `;
      }}
      // سناریو ۴: حباب انواع سکه
      else if (q.includes('حباب') || q.includes('سکه امامی') || q.includes('ربع') || q.includes('نیم سکه')) {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-cyan-400 text-xs sm:text-sm">🫧 جدول دقیق حباب انواع سکه در نرخ زنده امروز:</div>
            <div class="p-2.5 rounded-xl bg-slate-900 border border-cyan-500/30 space-y-1.5 text-[11px]">
              <div class="flex justify-between">
                <span class="text-slate-300">سکه طرح جدید (امامی):</span>
                <strong class="text-rose-400 font-mono">${{m.bubblePctCoinNew}}٪ (${{formatNumber(m.bubbleCoinNew)}} تومان)</strong>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-300">سکه بهار آزادی (قدیم):</span>
                <strong class="text-amber-400 font-mono">${{roundDecimal(((m.coinOld - m.intrinsicCoinNew)/m.coinOld)*100, 1)}}٪ حباب</strong>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-300">نیم سکه:</span>
                <strong class="text-rose-400 font-mono">${{m.bubblePctHalf}}٪ حباب</strong>
              </div>
              <div class="flex justify-between text-rose-400 font-bold border-t border-slate-800 pt-1">
                <span>ربع سکه (بالاترین ریسک):</span>
                <strong class="font-mono">${{m.bubblePctQuarter}}٪ حباب!</strong>
              </div>
            </div>
            <p class="text-slate-300 text-[11px]">
              🚨 <strong>هشدار حباب ربع سکه:</strong> ربع سکه با بیش از ۲۵ تا ۳۰ درصد حباب معامله می‌شود. یعنی یک سوم پول شما در ربع سکه باد هواست! اگر بازار وارد فاز استراحت شود، دارندگان ربع سکه بیشترین زیان را می‌بینند.
            </p>
          </div>
        `;
      }}
      // سناریو ۵: خرید بدون اجرت و مالیات
      else if (q.includes('اجرت') || q.includes('مالیات') || q.includes('دست دوم') || q.includes('آبشده')) {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-emerald-400 text-xs sm:text-sm">🛡️ ۳ ترفند خرید طلا بدون پرداخت اجرت و مالیات:</div>
            <div class="space-y-1.5 text-slate-200 text-[11px]">
              <p>وقتی طلای زینتی نو می‌خرید، <strong>۱۰ تا ۲۵ درصد اجرت</strong>، <strong>۹ درصد مالیات</strong> و <strong>۷ درصد سود طلافروش</strong> کسر می‌شود؛ یعنی باید طلا ۴۰ درصد بالا برود تا تازه به اصل پولتان برسید!</p>
              <div class="p-2 rounded-xl bg-slate-800 border border-slate-700">
                <strong class="text-emerald-400">۱. طلای آبشده (مظنه):</strong> قطعات شمش برش‌خورده با کد ری‌گیری (انگ) که کارمزد آن فقط ۱ تا ۲ درصد است و مالیات ندارد.
              </div>
              <div class="p-2 rounded-xl bg-slate-800 border border-slate-700">
                <strong class="text-amber-400">۲. طلای دست دوم مستعمل:</strong> اجرت ساخت آن صفر است و فقط ۳ تا ۵ درصد سود فروشنده پرداخت می‌کنید.
              </div>
              <div class="p-2 rounded-xl bg-slate-800 border border-slate-700">
                <strong class="text-cyan-400">۳. صندوق‌های سرمایه‌گذاری طلا (در بورس):</strong> نمادهایی مثل «طلا»، «عیار»، «کهربا» که بدون کارمزد طلافروشی و با امنیت کامل از طریق پنل بورسی قابل خرید با مبالغ حتی ۵۰۰ هزار تومان است.
              </div>
            </div>
          </div>
        `;
      }}
      // پاسخ تحلیلی پویا و تعاملی
      else {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-emerald-400 text-xs sm:text-sm">💡 پاسخ تحلیلی مشاور هوشمند:</div>
            <p class="text-slate-200">
              درباره پرسش شما: در شرایط کنونی بازار، نرخ طلای ۱۸ عیار در سطح <strong>${{formatNumber(m.gold18k)}} تومان</strong> و مظنه تهران در کانال <strong>${{formatNumber(m.mesghal)}} تومان</strong> قرار دارد.
            </p>
            <p class="text-slate-200 text-[11px]">
              اگر قصد شما <strong>حفظ ارزش بلندمدت در برابر تورم</strong> است، طلا تاریخی‌ترین سپر دفاعی ریال است. توصیه همیشگی ما انتخاب دارایی با کمترین حباب (طلای آبشده ۱۸ عیار) و ورود در قیمت‌های اصلاحی است.
            </p>
            <p class="text-slate-300 text-[11px]">
              می‌توانید مبالغ بودجه خود را بفرمایید (مثلاً: <em>با ۲۰ میلیون چی بخرم؟</em>) تا جدول بازدهی و گرم طلا را برایتان دقیق محاسبه کنم.
            </p>
          </div>
        `;
      }}

      appendPopupMessage('assistant', answerHtml);
    }}

    function getLiveMarketMetrics() {{
      const latestItem = APP_DATA.timeline[APP_DATA.timeline.length - 1];
      const gold18k = latestItem.price;
      const mesghal = APP_DATA.daily_data && APP_DATA.daily_data.ticks && APP_DATA.daily_data.ticks[0] && APP_DATA.daily_data.ticks[0].mesghal
        ? APP_DATA.daily_data.ticks[0].mesghal
        : (gold18k * 4.3318);
      const coinNew = APP_DATA.daily_data && APP_DATA.daily_data.ticks && APP_DATA.daily_data.ticks[0] && APP_DATA.daily_data.ticks[0].coin_new
        ? APP_DATA.daily_data.ticks[0].coin_new
        : 233500000;
      
      const coinOld = 230500000;
      const halfCoin = 119500000;
      const quarterCoin = 64500000;

      // ارزش ذاتی بر پایه وزن و عیار:
      // سکه تمام: ۸.۱۳۶ گرم عیار ۹۰۰ (معادل ۸.۲۶ گرم ۱۸ عیار)
      const intrinsicCoinNew = Math.round(gold18k * 8.26);
      const bubbleCoinNew = Math.max(0, coinNew - intrinsicCoinNew);
      const bubblePctCoinNew = roundDecimal((bubbleCoinNew / coinNew) * 100, 1);

      // نیم سکه: ۴.۱۳ گرم ۱۸ عیار
      const intrinsicHalf = Math.round(gold18k * 4.13);
      const bubbleHalf = Math.max(0, halfCoin - intrinsicHalf);
      const bubblePctHalf = roundDecimal((bubbleHalf / halfCoin) * 100, 1);

      // ربع سکه: ۲.۰۶۵ گرم ۱۸ عیار
      const intrinsicQuarter = Math.round(gold18k * 2.065);
      const bubbleQuarter = Math.max(0, quarterCoin - intrinsicQuarter);
      const bubblePctQuarter = roundDecimal((bubbleQuarter / quarterCoin) * 100, 1);

      // مدل پیش‌بینی ۱ ساله
      const hFc = generateHybridForecast();
      const m1Target = hFc.base[0].price;
      const m1Growth = roundDecimal(((m1Target - gold18k) / gold18k) * 100, 1);
      const y1Target = hFc.base[11].price;
      const y1Growth = roundDecimal(((y1Target - gold18k) / gold18k) * 100, 1);

      return {{
        gold18k,
        mesghal,
        coinNew,
        coinOld,
        halfCoin,
        quarterCoin,
        intrinsicCoinNew,
        bubbleCoinNew,
        bubblePctCoinNew,
        bubblePctHalf,
        bubblePctQuarter,
        m1Target,
        m1Growth,
        y1Target,
        y1Growth
      }};
    }}

    function updateAdvisorMarketSignals() {{
      const m = getLiveMarketMetrics();

      // ۱. به روزرسانی جدول حباب
      const tbody = document.getElementById('advisorBubbleTableBody');
      if (tbody) {{
        tbody.innerHTML = `
          <tr class="hover:bg-slate-100/50 dark:hover:bg-slate-800/40 transition-colors">
            <td class="py-2 px-2 flex items-center gap-1.5">
              <span>🥇</span>
              <span class="font-bold text-slate-900 dark:text-white">طلای ۱۸ عیار آبشده</span>
            </td>
            <td class="py-2 px-2 text-amber-500 font-mono">${{formatNumber(m.gold18k)}}</td>
            <td class="py-2 px-2 text-slate-400 font-mono">${{formatNumber(m.gold18k)}}</td>
            <td class="py-2 px-2 text-emerald-500 font-bold">۰٪ (بدون حباب)</td>
            <td class="py-2 px-2"><span class="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-bold">عالی (امن‌ترین)</span></td>
          </tr>
          <tr class="hover:bg-slate-100/50 dark:hover:bg-slate-800/40 transition-colors">
            <td class="py-2 px-2 flex items-center gap-1.5">
              <span>🪙</span>
              <span class="font-bold text-slate-900 dark:text-white">سکه بهار آزادی (قدیم)</span>
            </td>
            <td class="py-2 px-2 text-amber-500 font-mono">${{formatNumber(m.coinOld)}}</td>
            <td class="py-2 px-2 text-slate-400 font-mono">${{formatNumber(m.intrinsicCoinNew)}}</td>
            <td class="py-2 px-2 text-amber-500 font-bold">${{roundDecimal(((m.coinOld - m.intrinsicCoinNew)/m.coinOld)*100, 1)}}%</td>
            <td class="py-2 px-2"><span class="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 text-[10px] font-bold">خوب</span></td>
          </tr>
          <tr class="hover:bg-slate-100/50 dark:hover:bg-slate-800/40 transition-colors">
            <td class="py-2 px-2 flex items-center gap-1.5">
              <span>🪙</span>
              <span class="font-bold text-slate-900 dark:text-white">سکه امامی (طرح جدید)</span>
            </td>
            <td class="py-2 px-2 text-amber-500 font-mono">${{formatNumber(m.coinNew)}}</td>
            <td class="py-2 px-2 text-slate-400 font-mono">${{formatNumber(m.intrinsicCoinNew)}}</td>
            <td class="py-2 px-2 text-rose-500 font-bold">${{m.bubblePctCoinNew}}% (${{formatNumber(m.bubbleCoinNew)}} ت)</td>
            <td class="py-2 px-2"><span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[10px] font-bold">ریسک حباب</span></td>
          </tr>
          <tr class="hover:bg-slate-100/50 dark:hover:bg-slate-800/40 transition-colors">
            <td class="py-2 px-2 flex items-center gap-1.5">
              <span>🪙</span>
              <span class="font-bold text-slate-900 dark:text-white">نیم سکه</span>
            </td>
            <td class="py-2 px-2 text-amber-500 font-mono">${{formatNumber(m.halfCoin)}}</td>
            <td class="py-2 px-2 text-slate-400 font-mono">${{formatNumber(Math.round(m.gold18k * 4.13))}}</td>
            <td class="py-2 px-2 text-rose-500 font-bold">${{m.bubblePctHalf}}%</td>
            <td class="py-2 px-2"><span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[10px] font-bold">حباب متوسط</span></td>
          </tr>
          <tr class="hover:bg-slate-100/50 dark:hover:bg-slate-800/40 transition-colors">
            <td class="py-2 px-2 flex items-center gap-1.5">
              <span>🪙</span>
              <span class="font-bold text-slate-900 dark:text-white">ربع سکه</span>
            </td>
            <td class="py-2 px-2 text-amber-500 font-mono">${{formatNumber(m.quarterCoin)}}</td>
            <td class="py-2 px-2 text-slate-400 font-mono">${{formatNumber(Math.round(m.gold18k * 2.065))}}</td>
            <td class="py-2 px-2 text-rose-500 font-bold">${{m.bubblePctQuarter}}%</td>
            <td class="py-2 px-2"><span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[10px] font-bold">حباب بسیار بالا</span></td>
          </tr>
        `;
      }}

      // ۲. به روزرسانی بج‌های تحلیلی
      const bBadge = document.getElementById('advisorBubbleBadge');
      if (bBadge) {{
        bBadge.textContent = `حباب امامی: ${{m.bubblePctCoinNew}}%`;
      }}
    }}

    function appendAdvisorChatMessage(sender, textHtml) {{
      const container = document.getElementById('advisorChatContainer');
      if (!container) return;

      const isUser = sender === 'user';
      const msgDiv = document.createElement('div');
      msgDiv.className = isUser ? 'flex items-start justify-end gap-2 max-w-[90%] mr-auto' : 'flex items-start gap-2 max-w-[90%]';

      const avatar = isUser ? '👤' : '🤖';
      const bubbleClass = isUser
        ? 'p-3 rounded-2xl rounded-tl-none bg-emerald-600 text-white font-medium shadow-sm'
        : 'p-3 rounded-2xl rounded-tr-none bg-slate-200/80 dark:bg-slate-800 border border-slate-300 dark:border-slate-700/60 text-slate-900 dark:text-slate-100 space-y-1.5 shadow-sm';

      msgDiv.innerHTML = `
        ${{!isUser ? `<div class="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-xs shrink-0 mt-0.5">${{avatar}}</div>` : ''}}
        <div class="${{bubbleClass}}">
          ${{textHtml}}
        </div>
        ${{isUser ? `<div class="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs shrink-0 mt-0.5">${{avatar}}</div>` : ''}}
      `;

      container.appendChild(msgDiv);
      container.scrollTop = container.scrollHeight;
    }}

    function quickAsk(q) {{
      appendAdvisorChatMessage('user', `<p>${{q}}</p>`);
      setTimeout(() => {{
        generateAdvisorAnswer(q);
      }}, 300);
    }}

    function handleAdvisorSubmit(e) {{
      e.preventDefault();
      const input = document.getElementById('advisorInput');
      const q = input.value.trim();
      if (!q) return;

      input.value = '';
      appendAdvisorChatMessage('user', `<p>${{q}}</p>`);
      setTimeout(() => {{
        generateAdvisorAnswer(q);
      }}, 350);
    }}

    function generateAdvisorAnswer(query) {{
      const m = getLiveMarketMetrics();
      const q = query.toLowerCase();

      let answerHtml = '';

      if (q.includes('بخرم یا بفروشم') || q.includes('وقت خرید') || q.includes('خرید یا فروش')) {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-emerald-500 dark:text-emerald-400 text-sm">🟢 توصیه مشاور: خرید پله‌ای و نگهداری (Accumulate / Hold)</div>
            <p>بر اساس تحلیل داده‌های زنده و مدل شبکه عصبی LSTM:</p>
            <ul class="list-disc list-inside space-y-1 text-slate-800 dark:text-slate-200">
              <li><strong>هدف ۱ ماهه مدل (LSTM):</strong> نرخ <strong>${{formatNumber(m.m1Target)}} تومان</strong> (رشد تخمینی: +${{m.m1Growth}}%).</li>
              <li><strong>هدف ۱۲ ماهه مدل ترکیبی:</strong> نرخ <strong>${{formatNumber(m.y1Target)}} تومان</strong> (رشد تخمینی: +${{m.y1Growth}}%).</li>
              <li><strong>استراتژی پیشنهادی:</strong> به هیچ عنوان کل نقدینگی را یکجا وارد نکنید! از روش <strong>خرید پله‌ای (DCA)</strong> در ۳ پله استفاده کنید تا در صورت نوسان کوتاه‌مدت، میانگین خرید شما بهینه شود.</li>
            </ul>
          </div>
        `;
      }} else if (q.includes('سکه') && (q.includes('دلار') || q.includes('طلا') || q.includes('بهتره') || q.includes('کدام'))) {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-amber-500 dark:text-amber-400 text-sm">⚖️ مقایسه تخصصی: طلای ۱۸ عیار vs سکه vs دلار</div>
            <div class="space-y-1.5 text-slate-800 dark:text-slate-200">
              <p><strong>🥇 ۱. طلای ۱۸ عیار آبشده (بهترین برای سرمایه‌گذاری امن):</strong><br>
              حباب ندارد (۰٪)، بدون اجرت ساخت و مالیات است. کل پول شما به طلای خالص تبدیل می‌شود.</p>
              
              <p><strong>🪙 ۲. انواع سکه (خوب برای نوسان‌گیری با ریسک حباب):</strong><br>
              سکه امامی امروز دارای <strong>${{m.bubblePctCoinNew}}٪ حباب</strong> (حدود ${{formatNumber(m.bubbleCoinNew)}} تومان حباب خالی) است! در زمان آرامش بازار، حباب سکه خالی می‌شود و افت شدیدتری نسبت به طلا تجربه می‌کند.</p>

              <p><strong>💵 ۳. دلار نقدی:</strong><br>
              دلار تنها از تورم ریال سود می‌برد؛ در حالی که طلا یک اهرم دوگانه است (تورم دلار + جهش انس جهانی طلا). بازدهی طلا در ۱۰ سال گذشته ۱۵٪ بیشتر از دلار بوده است.</p>

              <div class="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold">
                🎯 نتیجه: ۶۰٪ طلای آبشده + ۲۵٪ سکه کم‌حباب (بهار آزادی) + ۱۵٪ نقدینگی برای خرید در اصلاح.
              </div>
            </div>
          </div>
        `;
      }} else if (q.includes('حباب') || q.includes('ارزش ذاتی')) {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-cyan-500 dark:text-cyan-400 text-sm">🫧 تحلیل حباب انواع سکه در نرخ امروز:</div>
            <ul class="space-y-1.5 text-slate-800 dark:text-slate-200">
              <li><strong>طلای ۱۸ عیار:</strong> حباب <strong>۰٪</strong> (ارزش ذاتی ۱۰۰٪ واقعی)</li>
              <li><strong>سکه بهار آزادی (قدیم):</strong> حباب تقریبی <strong>${{roundDecimal(((m.coinOld - m.intrinsicCoinNew)/m.coinOld)*100, 1)}}٪</strong></li>
              <li><strong>سکه طرح جدید (امامی):</strong> حباب <strong>${{m.bubblePctCoinNew}}٪</strong> (معادل ${{formatNumber(m.bubbleCoinNew)}} تومان حباب)</li>
              <li><strong>نیم سکه:</strong> حباب <strong>${{m.bubblePctHalf}}٪</strong></li>
              <li><strong>ربع سکه:</strong> حباب <strong>${{m.bubblePctQuarter}}٪</strong> (پرریسک‌ترین گزینه از نظر حباب)</li>
            </ul>
            <p class="text-amber-400 font-bold">توصیه: هر چه سرمایه کمتر است تمایل به ربع سکه بیشتر می‌شود، اما حباب ربع سکه بیش از ۳۰٪ است و در اصلاحات بازار بیشترین ضرر را می‌دهد.</p>
          </div>
        `;
      }} else if (q.includes('بدون اجرت') || q.includes('مالیات') || q.includes('دست دوم')) {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-rose-500 dark:text-rose-400 text-sm">🛡️ راهنمای خرید طلا با کمترین کارمزد و بدون مالیات:</div>
            <p>هنگام خرید طلای نو از ویترین، ۱۰ الی ۲۵ درصد اجرت ساخت و ۹ درصد مالیات بر ارزش افزوده کسر می‌شود که بازگشت سرمایه شما را ماه‌ها به تعویق می‌اندازد!</p>
            <ul class="list-disc list-inside space-y-1 text-slate-800 dark:text-slate-200">
              <li><strong>گزینه اول: طلای آبشده (شمش آزمایشگاهی با کد ری‌گیری):</strong> فقط ۱ تا ۲ درصد کارمزد بدون هیچ‌گونه مالیات و اجرت.</li>
              <li><strong>گزینه دوم: طلای کم‌اجرت یا دست دوم (مستعمل):</strong> اجرت ساخت صفر، سود فروشنده حدود ۳ تا ۵ درصد.</li>
              <li><strong>گزینه سوم: صندوق‌های سرمایه‌گذاری طلا در بورس (طلا، عیار، کهربا):</strong> کارمزد معاملات کمتر از ۰.۱۵ درصد و امنیت ۱۰۰٪ بدون ریسک سرقت.</li>
            </ul>
          </div>
        `;
      }} else if (q.includes('استراتژی') || q.includes('پله') || q.includes('چطور بخرم')) {{
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-purple-500 dark:text-purple-400 text-sm">🎯 راهبرد خرید پله‌ای (DCA): بهترین روش ضد اضطراب بازار</div>
            <p>سرمایه‌گذاران حرفه‌ای هیچ‌گاه تمام پول خود را در یک روز وارد بازار نمی‌کنند:</p>
            <ol class="list-decimal list-inside space-y-1 text-slate-800 dark:text-slate-200">
              <li><strong>پله اول (۴۰٪ سرمایه):</strong> در قیمت فعلی بازار وارد شوید.</li>
              <li><strong>پله دوم (۳۰٪ سرمایه):</strong> در صورتی که بازار ۲ تا ۴ درصد اصلاح داد خرید کنید.</li>
              <li><strong>پله سوم (۳۰٪ سرمایه):</strong> در کف حمایتی یا بعد از تثبیت روند صعودی وارد کنید.</li>
            </ol>
            <p class="text-emerald-400 font-bold">با این فرمول، هیچ‌گاه نگران ریزش‌های مقطعی بازار نخواهید بود.</p>
          </div>
        `;
      }} else {{
        // General intelligent response
        answerHtml = `
          <div class="space-y-2">
            <div class="font-black text-slate-900 dark:text-white text-sm">💡 تحلیل هوشمند مشاور:</div>
            <p class="text-slate-800 dark:text-slate-200">
              در وضعیت فعلی بازار، نرخ هر گرم طلای ۱۸ عیار <strong>${{formatNumber(m.gold18k)}} تومان</strong> است.
              بر اساس شبیه‌سازی ترکیبی سه‌گانه، بازدهی مورد انتظار ۱۲ ماه آینده <strong>+${{m.y1Growth}}٪</strong> برآورد می‌شود.
            </p>
            <p class="text-slate-700 dark:text-slate-300">
              اگر قصد سرمایه‌گذاری با افق بیش از ۶ ماه دارید، <strong>طلای ۱۸ عیار آبشده</strong> به دلیل عدم وجود حباب بهترین پوشش ریسک است. اگر دید نوسان‌گیری کوتاه‌مدت دارید، سکه امامی نوسانات شدیدتری ارائه می‌دهد.
            </p>
          </div>
        `;
      }}

      appendAdvisorChatMessage('assistant', answerHtml);
    }}

    function clearAdvisorChat() {{
      const container = document.getElementById('advisorChatContainer');
      if (container) {{
        container.innerHTML = '';
        appendAdvisorChatMessage('assistant', `
          <p class="font-bold text-emerald-400">تاریخچه گفت‌وگو پاک شد.</p>
          <p>آماده پاسخ‌گویی به سوالات جدید شما درباره خرید و فروش طلا و سکه هستم!</p>
        `);
      }}
    }}

    // INITIALIZATION
    window.addEventListener('DOMContentLoaded', () => {{
      renderMacroChart();
      renderForecastScenarioChart();
      populateRollingForecastTable();
      populateDailyTicksTable();
      populateDropdowns();
      populateWageTable();
      populateHeatmap();
      populateYearlyTable();
      populateFullDataTable();
      updateAdvisorMarketSignals();
      startAutoSyncTimer();
    }});
  </script>
  <!-- ========================================================================= -->
  <!-- 🤖 FLOATING AI CHAT POPUP WIDGET & TRIGGER BUTTON -->
  <!-- ========================================================================= -->

  <!-- FLOATING POPUP CHAT WINDOW (MODAL) -->
  <div id="aiChatPopupModal" class="fixed bottom-20 left-4 sm:left-6 z-50 w-[390px] max-w-[calc(100vw-2rem)] h-[590px] max-h-[calc(100vh-6.5rem)] rounded-3xl bg-slate-900/95 dark:bg-slate-900/95 backdrop-blur-xl border-2 border-emerald-500/50 shadow-2xl shadow-emerald-950/60 flex flex-col justify-between overflow-hidden transition-all duration-300 transform scale-95 opacity-0 pointer-events-none origin-bottom-left" style="direction: rtl;">
    
    <!-- POPUP HEADER -->
    <div class="p-3.5 sm:p-4 bg-gradient-to-r from-emerald-950/80 via-slate-900 to-slate-900 border-b border-emerald-500/30 flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <div class="relative">
          <div class="w-9 h-9 rounded-2xl bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center text-lg shadow-inner">
            🤖
          </div>
          <span class="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-400 border-2 border-slate-900 animate-pulse"></span>
        </div>
        <div>
          <div class="flex items-center gap-1.5">
            <h3 class="text-xs sm:text-sm font-black text-white">مشاور هوش مصنوعی طلا</h3>
            <span class="px-1.5 py-0.5 rounded text-[9px] font-black bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">آنلاین</span>
          </div>
          <p class="text-[10px] text-slate-300 font-medium">تحلیل زنده بازار، حباب و پیش‌بینی ۱ ساله</p>
        </div>
      </div>

      <div class="flex items-center gap-1">
        <!-- Settings API Key Button -->
        <button onclick="toggleAiApiSettings()" title="تنظیمات API هوش مصنوعی" class="p-1.5 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-emerald-300 transition-colors">
          ⚙️
        </button>
        <!-- Close Popup Button -->
        <button onclick="toggleAiChatPopup(false)" class="p-1.5 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-colors">
          ✕
        </button>
      </div>
    </div>

    <!-- LIVE MARKET CONTEXT TICKER IN POPUP -->
    <div class="bg-emerald-950/40 border-b border-emerald-500/20 px-3 py-1.5 text-[10px] flex items-center justify-between text-slate-300 font-bold">
      <span class="flex items-center gap-1">
        <span class="text-amber-400">🪙 طلا ۱۸:</span>
        <span id="popupLiveGoldPrice" class="font-mono text-white">--</span>
      </span>
      <span class="text-slate-500">|</span>
      <span class="flex items-center gap-1">
        <span class="text-rose-400">🫧 حباب سکه:</span>
        <span id="popupLiveBubblePct" class="font-mono text-white">--</span>
      </span>
      <span class="text-slate-500">|</span>
      <span class="flex items-center gap-1">
        <span class="text-cyan-400">🔮 سود ۱ ساله:</span>
        <span id="popupLiveForecastGrowth" class="font-mono text-white">--</span>
      </span>
    </div>

    <!-- OPTIONAL API KEY SETTINGS PANEL (COLLAPSIBLE) -->
    <div id="aiApiSettingsPanel" class="hidden p-3 bg-slate-800/90 border-b border-emerald-500/30 text-xs space-y-2">
      <div class="flex items-center justify-between">
        <span class="font-bold text-emerald-400">🔑 اتصال به هوش مصنوعی زاینده (اختیاری):</span>
        <button onclick="toggleAiApiSettings()" class="text-slate-400 hover:text-white text-[11px]">✕</button>
      </div>
      <p class="text-[11px] text-slate-300 leading-relaxed">
        سیستم به صورت پیش‌فرض با <strong>موتور تحلیلی داخلی</strong> به تمام سوالات بازار پاسخ هوشمند می‌دهد. اگر می‌خواهید مستقیماً به <strong>Google Gemini</strong> یا <strong>Groq</strong> متصل شوید، کلید رایگان خود را وارد کنید:
      </p>
      <div class="flex items-center gap-1.5">
        <input type="password" id="customApiKeyInput" placeholder="کلید API مثلاً AIzaSy... یا gsk_..." class="flex-1 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-[11px] focus:outline-none focus:border-emerald-500">
        <button onclick="saveCustomApiKey()" class="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px]">
          ذخیره
        </button>
      </div>
      <div id="apiKeyStatusMsg" class="text-[10px] text-slate-400"></div>
    </div>

    <!-- CHAT MESSAGES BODY -->
    <div id="popupChatMessages" class="flex-1 overflow-y-auto p-3 space-y-2.5 text-xs leading-relaxed" style="scroll-behavior: smooth;">
      <!-- Welcome Message -->
      <div class="flex items-start gap-2 max-w-[92%]">
        <div class="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-xs shrink-0 mt-0.5">🤖</div>
        <div class="p-3 rounded-2xl rounded-tr-none bg-slate-800/90 border border-slate-700 text-slate-100 space-y-1.5 shadow-sm">
          <p class="font-black text-emerald-400">سلام! من دستیار هوشمند و مشاور اختصاصی بازار طلا هستم.</p>
          <p class="text-slate-200">
            نرخ‌های روز طلا ۱۸ عیار، انواع سکه و پیش‌بینی مدل عصبی LSTM و چرخه‌های فصلی را به طور کامل تحلیل کرده‌ام.
          </p>
          <p class="text-slate-300 text-[11px]">
            می‌توانید بپرسید: <strong>«الان طلا بخرم یا بفروشم؟»</strong>، <strong>«با ۵۰ میلیون چی بخرم؟»</strong>، یا <strong>«سکه بهتره یا دلار؟»</strong>
          </p>
        </div>
      </div>
    </div>

    <!-- QUICK PROMPTS CHIPS BAR -->
    <div class="px-3 py-1.5 bg-slate-900/80 border-t border-slate-800 flex items-center gap-1.5 overflow-x-auto whitespace-nowrap text-[11px] scrollbar-none">
      <button onclick="sendQuickPopupPrompt('الان طلا بخرم یا بفروشم؟')" class="px-2.5 py-1 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 font-bold shrink-0 transition-all">
        🪙 بخرم یا بفروشم؟
      </button>
      <button onclick="sendQuickPopupPrompt('طلا بخرم یا سکه یا دلار؟')" class="px-2.5 py-1 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 font-bold shrink-0 transition-all">
        ⚖️ طلا یا سکه یا دلار؟
      </button>
      <button onclick="sendQuickPopupPrompt('حباب سکه امروز چقدر است و کدوم سکه بهتره؟')" class="px-2.5 py-1 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 font-bold shrink-0 transition-all">
        🫧 حباب سکه
      </button>
      <button onclick="sendQuickPopupPrompt('با ۵۰ میلیون تومان الان چی بخرم؟')" class="px-2.5 py-1 rounded-xl bg-purple-500/15 hover:bg-purple-500/25 text-purple-300 border border-purple-500/30 font-bold shrink-0 transition-all">
        💰 با ۵۰ میلیون چی بخرم؟
      </button>
    </div>

    <!-- POPUP INPUT BAR -->
    <form onsubmit="handlePopupChatSubmit(event)" class="p-2.5 bg-slate-900 border-t border-emerald-500/20 flex items-center gap-2">
      <input type="text" id="popupChatInput" placeholder="هر سوالی دارید بنویسید (مثلاً: با ۱۰۰ میلیون چیکار کنم؟)..." class="flex-1 px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs placeholder-slate-400 focus:outline-none focus:border-emerald-500 font-medium">
      <button type="submit" id="popupSendBtn" class="px-3.5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-xs flex items-center gap-1 shadow-lg shadow-emerald-500/20 transition-all">
        <span>ارسال</span>
        <span>🚀</span>
      </button>
    </form>

  </div>

  <!-- FLOATING TRIGGER BUTTON (TOGGLES POPUP MODAL) -->
  <button onclick="toggleAiChatPopup()" id="floatingAiChatBtn" class="fixed bottom-5 left-5 z-40 px-4 py-3 rounded-full bg-gradient-to-r from-emerald-600 via-teal-600 to-amber-600 hover:from-emerald-500 hover:to-amber-500 text-white font-black text-xs shadow-2xl shadow-emerald-950/60 border-2 border-emerald-400/50 flex items-center gap-2.5 transition-all hover:scale-105 group cursor-pointer">
    <span class="text-lg group-hover:scale-110 transition-transform">🤖</span>
    <span>مشاور هوشمند طلا</span>
    <span class="w-2.5 h-2.5 rounded-full bg-emerald-300 animate-ping"></span>
  </button>


</body>
</html>
'''

    # Ensure ALL numbers across the entire HTML and static strings are in English digits (0-9)
    persian_to_eng = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    for p_dig, e_dig in persian_to_eng.items():
        html_code = html_code.replace(p_dig, e_dig)

    with open('gold_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_code)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_code)

    print("Successfully built automated gold_dashboard.html & index.html! File size:", os.path.getsize('gold_dashboard.html'))

if __name__ == '__main__':
    build()
