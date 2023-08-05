import lib_db as ldb
import time
import sqlite3

c_status = sqlite3.connect("/root/data/data.db")

rate = 10
time_str = '00:00'
pos = 0
cycle = ['EVM-1', 'V1.0 ']

while(1):
    if(int(time.time()) % rate == 0):
        cell_strength = ldb.read_db('status', 'cell_sig_strength', c_status)
        wifi_strength = ldb.read_db('status', 'wifi_sig_strength', c_status)
        
        cell = ''
        wifi = ''
        if(cell_strength == 0):
            cell = 'y'
        else:
            cell = 'z'

        if(wifi_strength == 0):
            wifi = 'v'
        elif(wifi_strength == 1):
            wifi = 'w'
        else:
            wifi = 'x'

        q = time.asctime(time.localtime(time.time()))[11:16]
        t = str(int(q[:2])-4) + q[2:]
        if(len(t) == 4):
            t = '0' + t

        if(int(t[:2]) < 0):
            t = str(24 + int(t[:2])) + q[2:]

        if(int(t[:2]) == 0):
            time_str = '12' + t[2:]
        elif(int(t[:2]) > 12):
            time_str = str(int(t[:2])-12) + t[2:]
        else:
            time_str = t

        if(time_str[0] == '0'):
            time_str = ' ' + time_str[1:]
        else:
            time_str = time_str
        
        ldb.update('output', 'topline', f"{cycle[pos]}        {cell}{wifi}", c_status)

        pos = pos+1
        if(pos > len(cycle)-1):
            pos = 0
        time.sleep(rate - .1)