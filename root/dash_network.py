from wifi_config import change_option
import os
import time

def update_wifi(ssid, pwd, enc):
    change_option('wireless','client', 'ssid', ssid)
    if(enc == 'None'):
        enc = 'none'
    change_option('wireless','client', 'key', pwd)
    change_option('wireless','client', 'encryption', enc)

    os.system('wifi down; wifi up')
    #search logs for issues connecting to network, if issues disable network and return 0
    time.sleep(10)
    log = os.popen('logread | grep 2=PREV_AUTH_NOT_VALID').read()
    log2 = os.popen('logread | grep "daemon.notice hostapd: handle_probe_req: send failed"').read()
    if len(log) > 0 or len(log2) > 0:
        os.system('/etc/init.d/log restart')
        change_option('wireless','client', 'disabled', '1')
        os.system('wifi down; wifi up')
        return 0

    #if successfully connected, return 1
    return 1

def restart_wifi():
    print("RESTARTING WIFI_CONFIG")
    os.system("ps | grep wifi_config | grep -v grep | awk '{print $1}' | xargs kill")
    os.system("python /root/wifi_config.py &")
    print("WIFI_CONFIG RESTARTED")
