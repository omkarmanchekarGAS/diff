from lib_i2c import I2C
import lib_db as ldb
import time
import sqlite3

conn = sqlite3.connect("/root/data/data.db")

device = I2C("/dev/i2c-0")

def read_byte_data(address, byte):
    msgs = [I2C.Message([byte]), I2C.Message([0x00], read=True)]
    device.transfer(address, msgs)
    return msgs[1].data[0]

def read_bytes_data(address, byte, numvals):
    read_data = []
    for i in range (0,numvals):
        read_data.append(0x00)
    msgs = [I2C.Message([byte]), I2C.Message(read_data, read=True)]
    device.transfer(address, msgs)
    return msgs[1].data

def write_byte_data(address, byte, value):
    msgs = [I2C.Message([byte, value])]
    device.transfer(address, msgs)

def write_bytes_data(address, byte, values):
    msgs = [I2C.Message([byte] + values)]
    device.transfer(address, msgs)

def combine_bytes(byte_array):
    bytes = byte_array[0]
    for i in range(1,len(byte_array)):
        bytes = bytes << 8
        bytes = bytes + byte_array[i]
    return bytes

def read_serial_num():
    nums = (combine_bytes(read_bytes_data(0x50, 0x0A, 3))) & 0x0FFFFF
    serial_num = f"EVM{nums:06d}"
    print(serial_num)
    return serial_num

def read_calib_consts():
    CHC = (combine_bytes(read_bytes_data(0x50, 0x00, 2))) & 0x0FFF
    CHV = (combine_bytes(read_bytes_data(0x50, 0x02, 2))) & 0x0FFF
    phase_consts = combine_bytes(read_bytes_data(0x50, 0x04, 2))
    PHC = phase_consts & 0x03FF
    PHV = phase_consts >> 12
    print("CHV: ", CHV)
    print("CHC: ", CHC)
    print("PHV: ", PHV)
    print("PHC: ", PHC)
    return [CHC, CHV, PHC, PHV]


def read_prod_date():
    prod_date = combine_bytes(read_bytes_data(0x50, 0x06, 4))
    print(time.asctime(time.localtime(prod_date)))
    return prod_date

def write_serial_num():
    ldb.update('system_status', 'serial_num', read_serial_num(), conn)
    if ldb.read_db("config", "charge_point_id", conn) == "-1":
        ldb.update('config', 'charge_point_id', read_serial_num(), conn)

def write_calib_consts():
    consts = read_calib_consts()
    ldb.update('calibration', 'CHC', consts[0], conn)
    ldb.update('calibration', 'CHV', consts[1], conn)
    ldb.update('calibration', 'PHC', consts[2], conn)
    ldb.update('calibration', 'PHV', consts[3], conn)

def write_prod_date():
    ldb.update('system_status', 'production_date', read_prod_date(), conn)

#read_serial_num()
#read_calib_consts()
#read_prod_date()
write_serial_num()
write_calib_consts()
write_prod_date()