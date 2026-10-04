import subprocess
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

# Run native git directly without requiring Docker
cmd = ['git'] + sys.argv[1:]
try:
    res = subprocess.run(cmd)
    sys.exit(res.returncode)
except Exception as e:
    print("خطا در اجرای گیت:", e)
    sys.exit(1)
