import time
from os import system
from lib_i2c import I2C

def read_byte_data(device, address, byte):
    msgs = [I2C.Message([byte]), I2C.Message([0x00], read=True)]
    device.transfer(address, msgs)
    return msgs[1].data[0]

def write_byte_data(device, address, byte, value):
    msgs = [I2C.Message([byte, value])]
    device.transfer(address, msgs)

def secs_convert(s):
	r = s % 10
	l = (int((s-r)/10) << 4) & 0x7F
	return (l + r)

def mins_convert(m):
	r = m % 10
	l = (int((m-r)/10) << 4) & 0x7F
	return (l + r)

def hours_convert(h):
	r = h % 10
	l = (int((h-r)/10) << 4) & 0x3F
	return (l + r)

def date_convert(d):
	r = d % 10
	l = (int((d-r)/10) << 4) & 0x3F
	return (l + r)
		
def month_convert(m):
	r = m % 10
	l = (int((m-r)/10) << 4) & 0x1F
	return (l + r)

def year_convert(y):
	ny = y % 100
	r = ny % 10
	l = (int((ny-r)/10) << 4)
	return (l + r)
    
def Update_Time(device):
    now = time.gmtime(time.time())
    print("NOW: ", now)
    yr = year_convert(now[0])
    write_byte_data(device,0x68,0x06, yr)
    mon = month_convert(now[1])
    write_byte_data(device,0x68,0x05, mon)
    day = date_convert(now[2])
    write_byte_data(device,0x68,0x04, day)
    hr = hours_convert(now[3])
    write_byte_data(device,0x68,0x02, hr)
    min = mins_convert(now[4])
    write_byte_data(device,0x68,0x01, min)
    sec = secs_convert(now[5])
    write_byte_data(device,0x68,0x00, sec)

def set_from_ntpd_time(device):
    system("/etc/init.d/sysntpd restart &")
    time.sleep(1)
    system("/etc/init.d/sysntpd start &")
    
    if(time.gmtime(time.time())[0] > 2022):
        Update_Time(device)
