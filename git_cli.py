import subprocess
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

cwd = os.getcwd()
cmd = ['docker', 'run', '--rm', '-v', f'{cwd}:/repo', '-w', '/repo', 'local-git', 'git'] + sys.argv[1:]
res = subprocess.run(cmd)
sys.exit(res.returncode)
