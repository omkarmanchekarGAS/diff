import time
from lib_i2c import I2C
import lib_db as ldb
from urllib import request
import sqlite3
import os

device = I2C("/dev/i2c-0")
conn = sqlite3.connect("/root/data/data.db")

def read_byte_data(address, byte):
    msgs = [I2C.Message([byte]), I2C.Message([0x00], read=True)]
    device.transfer(address, msgs)
    return msgs[1].data[0]

def write_byte_data(address, byte, value):
    msgs = [I2C.Message([byte, value])]
    device.transfer(address, msgs)

def RTC_Read_Converter(x):
    #Converts BCD to Decimal    
    a = x & 0x0F
    b = x & 0xF0
    b = b >> 4
    return 10*b + a

def Read_Time():
    #Reads registers from RTC and converts to a formatted string
    sec = (read_byte_data(0x68,0x00)) & 0x7F
    seconds = RTC_Read_Converter(sec)
    min = (read_byte_data(0x68,0x01)) & 0x7F
    minutes = RTC_Read_Converter(min)
    hr = (read_byte_data(0x68,0x02)) & 0x3F
    hours = RTC_Read_Converter(hr)
    d = (read_byte_data(0x68,0x04)) & 0x3F
    day = RTC_Read_Converter(d)#Day_Dict[str(RTC_Read_Converter(d))]
    mon = (read_byte_data(0x68,0x05)) & 0x1F
    months = RTC_Read_Converter(mon)#Month_Dict[str(RTC_Read_Converter(m2))]
    yr = read_byte_data(0x68,0x06)
    years = RTC_Read_Converter(yr) + 2000
    print(months, day, years, hours, minutes, seconds)
    return (months, day, years, hours, minutes, seconds)

# dont assume we're connected to internet on boot
ldb.update('status', "internet_connected", 0, conn)

# turn on trickle charging
write_byte_data(0x68,0x08,0xAA)

t = Read_Time()
if(t[2] > 2022):
    s = f"date -s '{t[2]:04d}-{t[0]:02d}-{t[1]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}'"
    print(s)
    os.system(s)

# connected = False
# while(not connected):
#     ID = ldb.read_db('system_status', 'serial_num')
#     try:
#         request.urlopen(f'wss://ocpp.staging.lynkwell.com/{ID}', timeout=1)
#         connected = True
#     except:
#         time.sleep(5)
