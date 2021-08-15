import subprocess
import sys
import time

for i in range(5):
     proc = subprocess.Popen(['ps', '-ef'], stdout=subprocess.PIPE)
     out, _ = proc.communicate()

     lines = out.split('\n')
     for line in lines:
         if '/usr/bin/supervisord' in line:
             sys.exit()

     print 'supervisor not running'
     proc = subprocess.Popen(['service', 'supervisor', 'start'])
     proc.communicate()

     time.sleep(i)

print 'ruh roh shaggy'
