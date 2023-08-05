import lib_db as ldb
import socket
import os
from time import sleep
import sqlite3

conn = sqlite3.connect("/root/data/data.db")

def change_option(filename, iface_name, option, new_val):
    os.system(f"uci set {filename}.{iface_name}.{option}='{new_val}'; uci commit")

def main():
    conn = sqlite3.connect("/root/data/data.db")
    # set dev network name
    serial_num = ldb.read_db('system_status', 'serial_num', conn)
    
    change_option('wireless', 'dev', 'ssid', serial_num + " Dev")

    # set dashboard network name
    change_option('wireless','dashboard', 'ssid', serial_num + " Config")

    # regen real network ssid and key
    real_ssid = serial_num
    real_key = 'NH9q-fUo2-o3ZrA'
    change_option('wireless','real', 'ssid', real_ssid)
    change_option('wireless','real', 'key', real_key)

    setup_on = ldb.read_db('status', 'setup_mode', conn)

    wifi_mode = ldb.read_db('config', 'network_mode', conn)

    if (setup_on):
        print("DASHBOARD ENABLED")
        change_option('wireless','dashboard', 'disabled', '0')
        change_option('wireless',"provisioning", 'disabled', '1')
        change_option('wireless',"real", 'disabled', '1')
        change_option('wireless',"client", 'disabled', '1')
        change_option('wireless',"child_connect", 'disabled', '1')
        match(wifi_mode):
            case "Direct":
                change_option('network', 'lan', 'ipaddr', '192.168.5.7')
                change_option('network', 'vlan', 'ipaddr', '192.168.6.7')

                os.system("wifi down; wifi up")
                sleep(10)
                print("DIRECT MODE")
            case "Gateway":
                change_option('network', 'lan', 'ipaddr', '192.168.1.1')
                change_option('network', 'vlan', 'ipaddr', '192.168.2.1')

                os.system("wifi down; wifi up")
                sleep(10)
                print("GATEWAY MODE")
            case "Client":
                change_option('network', 'lan', 'ipaddr', '192.168.3.1')
                change_option('network', 'vlan', 'ipaddr', '192.168.4.1')

                os.system("wifi down; wifi up")
                sleep(10)
                print("CLIENT MODE")
    else:
        print("DASHBOARD DISABLED")
        change_option('wireless','dashboard', 'disabled', '1')

        match(wifi_mode):
            case "Direct":
                change_option('wireless',"provisioning", 'disabled', '1')
                change_option('wireless',"real", 'disabled', '1')
                curr_ssid = ldb.read_db('config', 'ssid', conn)
                if curr_ssid == '':
                    change_option('wireless',"client", 'disabled', '1')
                else:
                    change_option('wireless',"client", 'disabled', '0')
                change_option('wireless',"child_connect", 'disabled', '1')

                # ensure we dont conflict with gateway we want to direct connect to
                change_option('network', 'lan', 'ipaddr', '192.168.5.7')
                change_option('network', 'vlan', 'ipaddr', '192.168.6.7')

                os.system("wifi down; wifi up")
                sleep(10)

                print("DIRECT MODE")
            
            case "Gateway":
                change_option('wireless',"provisioning", 'disabled', '1')
                change_option('wireless',"real", 'disabled', '0')
                # Commented out for now for manual testing
                change_option('wireless', "client", 'disabled', '1')
                change_option('wireless',"child_connect", 'disabled', '1')

                change_option('network', 'lan', 'ipaddr', '192.168.1.1')
                change_option('network', 'vlan', 'ipaddr', '192.168.2.1')

                os.system("wifi down; wifi up")

                sleep(10)

                os.system(". /root/cell_check.sh &")

            case "Client":
                # kill any pre-existing ocpp and supervisor
                os.system("ps | grep central_system | grep -v grep | awk '{print $1}' | xargs kill")
                os.system("ps | grep n_super | grep -v grep | awk '{print $1}' | xargs kill")

                # start naive supervisor to make sure ocpp doesnt crash
                os.system(". /root/n_super.sh &")

                change_option('wireless',"provisioning", 'disabled', '1')
                change_option('wireless',"real", 'disabled', '1')
                parent_serial = 'EVM000110'
                change_option('wireless','child_connect', 'ssid', parent_serial)
                change_option('wireless','child_connect', 'key', real_key)
                change_option('wireless','child_connect', 'disabled', '0')
                
                # ensure theres no ip conflicts between parents and children
                change_option('network', 'lan', 'ipaddr', '192.168.3.1')
                change_option('network', 'vlan', 'ipaddr', '192.168.4.1')

                os.system("wifi down; wifi up")
                sleep(10)


if __name__ == "__main__":
    main()
