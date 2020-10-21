from datetime import datetime, timedelta
import os
import subprocess
import time

LOG_FILE = '/var/log/mt500/data.log'
INTERVAL = 60 * 60 * 3

def touch():
    with open('restarted', 'w'):
        pass

def restart():
    print('restarting')
    proc = subprocess.Popen(['supervisorctl', 'restart', 'mt500'])
    proc.communicate()
    touch()

first_run = False
if not os.path.exists('restarted'):
    first_run = True
    touch()

last_restarted = round(os.path.getmtime('restarted'))

last_line = None
try:
    with open(LOG_FILE, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode().strip()
except OSError:
    with open(LOG_FILE, 'r') as f:
        for line in f:
            pass
        try:
            last_line = line.strip()
        except NameError:
            print('file is probably empty')

if last_line:
    print(last_line)
    now = datetime.now()
    toks = last_line.split(',')
    if len(toks) == 5:
        #10/19/2020 16:59:47
        dt = datetime.strptime(toks[0], '%m/%d/%Y %H:%M:%S')
        diff = now - dt

        if diff.seconds > INTERVAL and time.time() - last_restarted > INTERVAL:
            restart()
elif first_run or time.time() - last_restarted > INTERVAL:
    restart()
