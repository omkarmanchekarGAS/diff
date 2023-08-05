import sqlite3
import lib_db as ldb
from os import popen
from dash_network import restart_wifi
from time import sleep

conn = sqlite3.connect("/root/data/data.db")
direct_connect = ldb.read_db("config", "ssid", conn)
mode_in = ldb.read_db("config", "network_mode", conn)
counter = 6
while True:
    match(mode_in):
        case "Direct":
            a = popen("iw wlan0 scan").read()
            l = a.split("\n")
            ssids = []

            for i in range(len(l)):
                if l[i] == f"\tSSID: {direct_connect}":
                    ssids.append(l[i-9])

            assoc_flag = False
            for s in ssids:
                if s[-10:] == 'associated':
                    ldb.update("status", "wifi_sig_strength", 2, conn)
                    assoc_flag = True
                    break

            if not assoc_flag:
                ldb.update("status", "wifi_sig_strength", 0, conn)

        case "Gateway":
            # end the loop since gateway should not be connected to wifi
            ldb.update("status", "wifi_sig_strength", 0, conn)
            break

        case "Client":
            a = popen("iw wlan0 scan").read()
            l = a.split("\n")
            ssids = []

            assoc_flag = False
            for i in range(len(l)):
                if l[i][-10:] == 'associated':
                    if len(l[i+9]) == 22:
                        ldb.update("status", "wifi_sig_strength", 2, conn)
                        print("Associated with Parent!")
                        assoc_flag = True
                        break

            if not assoc_flag:
                ldb.update("status", "wifi_sig_strength", 0, conn)
                print("Couldn't associate with Parent")
        
            if (counter <= 0 and not assoc_flag):
                print("End of timer and restarting wifi config")
                # restart wifi config
                restart_wifi()
                # end this thread
                break
            counter = counter - 1
    print("Running Status Updater")
    sleep(10)