import os
import time
while True:
    os.system("/etc/init.d/sysntpd restart")
    time.sleep(10)