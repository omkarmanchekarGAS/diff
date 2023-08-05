import lib_db as ldb
import time
import sqlite3

conn = sqlite3.connect("/root/data/data.db")

rate = 10
pos = 0
rates = ['Cost per kWh: ', 'Parking: ', 'Activation: ']
rate_vals = ['usd_per_kWh', 'usd_per_parked_mins', 'usd_activation_fee']

while(1):
    if(int(time.time()) % rate == 0):
        line4 = ldb.read_db('config', rate_vals[pos], conn)
        print(rates[pos] + str(line4))
        ldb.update('output', 'line4', rates[pos] + "$" + str(line4), conn)

        pos = pos+1
        if(pos > 2):
            pos = 0
        time.sleep(rate - .1)