from lib_i2c import I2C
import datetime
from time import sleep

class EEPROM():

    device = I2C("/dev/i2c-0")

    def __init__(self):
        self.device = I2C("/dev/i2c-0")

    def write_byte_data(self, address, byte, value):
        msgs = [I2C.Message([byte, value])]
        self.device.transfer(address, msgs)

    def write_bytes_data(self, address, byte, values):
        msgs = [I2C.Message([byte] + values)]
        self.device.transfer(address, msgs)
    
    def write_serial_num(self, serial_num):
        self.write_bytes_data(0x50, 0x0A, serial_num)

    def write_calib_consts(self, CHC, CHV):#, PHC, PHV):
        self.write_bytes_data(0x50, 0x00, CHC)
        self.write_bytes_data(0x50, 0x02, CHV)
        #add phase calibration?
        # phase_consts = (PHV << 12) + PHC
        # self.write_bytes_data(0x50, 0x04, phase_consts)

    def write_prod_date(self):
        self.write_bytes_data(0x50, 0x06, datetime.datetime.utcnow())

    def authorize_charge(self):
        self.write_byte_data(0x14, 0, 80)
        self.write_byte_data(0x14, 3, 256-80)

    def end_charge(self):
        self.write_byte_data(0x14, 0, 0)
        self.write_byte_data(0x14, 3, 0)

    def enable_stpm(self):
        msgs = [I2C.Message([0x03]), I2C.Message([0x00], read=True)]
        self.device.transfer(0x38, msgs)

        msgs = [I2C.Message([0x03, 0xF9])]
        self.device.transfer(0x38, msgs)

        for j in range(3):
            msgs = [I2C.Message([0x01, 0xFD])]
            self.device.transfer(0x38, msgs)
            sleep(0.001)
            msgs = [I2C.Message([0x01, 0xFF])]
            self.device.transfer(0x38, msgs)
            sleep(0.001)


        # write final low pulse to SCS pin (IO2)

        msgs = [I2C.Message([0x01, 0xFB])]
        self.device.transfer(0x38, msgs)
        sleep(0.001)
        msgs = [I2C.Message([0x01, 0xFF])]
        self.device.transfer(0x38, msgs)