# -*- coding: utf-8 -*-
"""
سرور مدرن، پایدار و آماده استقرار بر روی هاست‌های رایگان (Render, Railway, Koyeb, PythonAnywhere, Local)
پشتیبانی از پورت متغیر محیطی (PORT)، اندپوینت‌های API برای وب‌هوک و کرون‌جاب (Cron-Job)
زمان‌بندی خودکار هر ۳۰ دقیقه در پس‌زمینه بدون نیاز به باز بودن مرورگر توسط کاربران
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

import http.server
import socketserver
import socket
import threading
import subprocess
import time
import re
import os
import json
import datetime

# تنظیم پورت پویا متناسب با هاست‌های ابری (مانند Render و Railway)
PORT = int(os.environ.get("PORT", 8080))
AUTO_SYNC_INTERVAL_SEC = 30 * 60  # ۳۰ دقیقه
SERVER_START_TIME = time.time()
LAST_SYNC_TIME = None
IS_UPDATING = False

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def perform_price_update(trigger_source="زمان‌بند خودکار سرور"):
    """اجرای استعلام زنده و ذخیره در بانک داده SQLite"""
    global LAST_SYNC_TIME, IS_UPDATING
    if IS_UPDATING:
        return {"status": "already_running", "message": "عملیات استعلام در حال اجراست."}
    
    IS_UPDATING = True
    try:
        print(f"\n[🔄 شروع استعلام قیمت - منبع: {trigger_source}]...", flush=True)
        import update_live_price
        update_live_price.run_update()
        LAST_SYNC_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"✅ [موفقیت] نرخ‌ها در بانک داده SQLite ذخیره و داشبورد با هر دو مدل پیش‌بینی فصلی و LSTM بروزرسانی شد.\n", flush=True)
        return {
            "status": "success",
            "trigger_source": trigger_source,
            "last_sync": LAST_SYNC_TIME,
            "message": "استعلام با موفقیت در بانک داده ذخیره شد."
        }
    except Exception as e:
        print(f"❌ [خطا در استعلام قیمت]: {e}", flush=True)
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        IS_UPDATING = False

def auto_update_job():
    """ترد پس‌زمینه برای بروزرسانی خودکار هر ۳۰ دقیقه حتی وقتی هیچ کاربری سایت را باز نکرده است"""
    time.sleep(5)  # وقفه کوتاه پس از روشن شدن سرور
    # اجرای اولین استعلام هنگام شروع به کار سرور
    perform_price_update("استعلام اولیه هنگام راه‌اندازی سرور")
    
    while True:
        time.sleep(AUTO_SYNC_INTERVAL_SEC)
        perform_price_update("زمان‌بند دوره‌ای ۳۰ دقیقه‌ای سرور")

class ProductionHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        req_path = self.path.split('?')[0].rstrip('/')
        if not req_path:
            req_path = '/'

        # ۱. اندپوینت کرون و وب‌هوک برای هاست‌های ابری و سرویس‌های کرون‌جاب خارجی (مانند cron-job.org و UptimeRobot)
        if req_path in ['/api/cron-update', '/api/update', '/cron']:
            res = perform_price_update("کرون‌جاب وب‌هوک /api/cron-update")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            return

        # ۲. اندپوینت پایش سلامت سرور (Health check)
        elif req_path in ['/api/health', '/api/status', '/ping']:
            import database
            uptime_seconds = int(time.time() - SERVER_START_TIME)
            health_info = {
                "status": "healthy",
                "uptime_seconds": uptime_seconds,
                "uptime_human": f"{uptime_seconds // 3600} ساعت و {(uptime_seconds % 3600) // 60} دقیقه",
                "last_sync_time": LAST_SYNC_TIME,
                "auto_sync_interval_minutes": AUTO_SYNC_INTERVAL_SEC // 60,
                "database_stats": database.get_stats(),
                "cloud_environment": os.environ.get("RENDER", "no") == "true" or "PORT" in os.environ,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(health_info, ensure_ascii=False).encode('utf-8'))
            return

        # ۳. اندپوینت آمار بانک داده SQLite
        elif req_path == '/api/db-stats':
            import database
            stats = database.get_stats()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode('utf-8'))
            return

        # ۴. اندپوینت آخرین نرخ‌های زنده و سکه‌ها
        elif req_path == '/api/live':
            data = {}
            if os.path.exists('live_gold_result.json'):
                try:
                    with open('live_gold_result.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            return

        # ۵. ارسال فایل‌های استاتیک عادی وب‌سایت
        super().do_GET()

    def do_POST(self):
        # پشتیبانی از متد POST برای اندپوینت آپدیت
        if self.path.startswith('/api/update') or self.path.startswith('/api/cron-update'):
            res = perform_price_update("درخواست دستی POST")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            return
        super().do_GET()

def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    local_ip = get_local_ip()
    
    is_cloud = os.environ.get("RENDER") == "true" or "PORT" in os.environ
    
    print("\n" + "=" * 70, flush=True)
    print("سامانه آنلاین نرخ طلا و سکه + پیش‌بینی با شبکه عصبی LSTM و مدل فصلی", flush=True)
    print("بروزرسانی خودکار هر ۳۰ دقیقه و ذخیره دائم در بانک داده SQLite", flush=True)
    print("=" * 70, flush=True)
    
    if not is_cloud:
        print(f"\n۱. آدرس محلی (شبکه داخلی / وای‌فای):", flush=True)
        print(f"   👉 http://localhost:{PORT}/  یا  http://{local_ip}:{PORT}/", flush=True)
        print("\n۲. اندپوینت‌های کرون‌جاب و سلامت خودکار برای هاست‌های ابری:", flush=True)
        print(f"   👉 http://localhost:{PORT}/api/health (بررسی وضعیت سرور و دیتابیس)", flush=True)
        print(f"   👉 http://localhost:{PORT}/api/cron-update (استعلام فوری و ذخیره در بانک داده)", flush=True)

    # راه‌اندازی سرور وب
    handler = ProductionHTTPHandler
    # استفاده از Allow Reuse Address برای جلوگیری از خطای اشغال پورت
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("0.0.0.0", PORT), handler)

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    print(f"\n🌐 سرور وب با موفقیت روی پورت {PORT} شروع به کار کرد.", flush=True)

    # فعال‌سازی زمان‌بند ۳۰ دقیقه‌ای در پس‌زمینه
    auto_thread = threading.Thread(target=auto_update_job, daemon=True)
    auto_thread.start()
    print("⏱️ زمان‌بند خودکار ۳۰ دقیقه‌ای فعال شد (حتی بدون حضور کاربر استعلام و ذخیره انجام می‌شود).", flush=True)

    # راه‌اندازی تانل اینترنتی رایگان فقط در محیط محلی (در محیط‌های ابری مانند Render خود هاست دامنه عمومی می‌دهد)
    if not is_cloud and sys.platform == 'win32':
        def start_tunnel():
            try:
                cmd = [
                    'ssh',
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=nul',
                    '-o', 'ServerAliveInterval=30',
                    '-R', f'80:localhost:{PORT}',
                    'nokey@localhost.run'
                ]
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                for line in proc.stdout:
                    m = re.search(r'https://[a-zA-Z0-9\-]+\.lhr\.life', line)
                    if m:
                        public_url = m.group(0)
                        print(f"\n=======================================================", flush=True)
                        print(f"✅ لینک عمومی موقت (از سراسر دنیا روی گوشی باز می‌شود):", flush=True)
                        print(f"   👉 {public_url}", flush=True)
                        print(f"=======================================================\n", flush=True)
                        break
            except Exception as e:
                pass

        tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
        tunnel_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nسرور متوقف شد.", flush=True)
        httpd.shutdown()

if __name__ == '__main__':
    run_server()

# Fallback exports if scanned by cloud serverless builders
def handler(request=None, *args, **kwargs):
    return {"statusCode": 200, "body": "OK"}
app = handler
application = handler

