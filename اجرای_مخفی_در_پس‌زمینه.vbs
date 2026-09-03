Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python scheduler_daemon.py", 0, False
