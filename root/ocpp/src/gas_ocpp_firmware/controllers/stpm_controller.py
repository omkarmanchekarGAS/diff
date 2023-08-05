'''
This controller seeks to replace the endless iterations of stpm_driver.py, stpm.py, and
new_new_stpm_test.py

As opposed to an independent script, we now create an object to be held by the charge_point class
during ocpp operation. 
'''

import lib_db
import serial
import time
import sqlite3
import math
from threading import Thread
import os

# Decimation clock rate
DCLK = (7812.5)
# Voltage reference inside chip
VREF = (1.18)
# Gain (amplitude) on voltage
AV = (2)
# gain on current
AI = (2)
# voltage divider resitor ohms
R1 = (750000)
R2 = (470)
# Current sensor sensitivity coming from ratio of input input current to output volts on our CT
KS = (0.00238)

def calcCRC(bytes):
    CRC_8 = 0x07
    checksum = 0x00
    for i in range(len(bytes)):
        loc_idx = 0
        loc_temp = 0
        while (loc_idx < 8):
            loc_temp = bytes[i] ^ checksum
            checksum = (checksum << 1) & 0xFF
            if (loc_temp & 0x80 != 0):
                checksum = checksum ^ CRC_8
            bytes[i] = (bytes[i] << 1) & 0xFF
            loc_idx += 1
    return checksum

def byteReverse(b):
    b = ((b >> 1) & 0x55) | ((b << 1) & 0xaa)
    b = ((b >> 2) & 0x33) | ((b << 2) & 0xcc)
    b = ((b >> 4) & 0x0f) | ((b << 4) & 0xf0)
    return b

def uart_frame(byte_list):
    copy = [byteReverse(i) for i in byte_list]
    byte_list.append(byteReverse(calcCRC(copy)))
    return byte_list

def write_frame(ser, byte_list):
    b = bytearray(uart_frame(byte_list))
    # print("Wrote:", b.hex())
    ser.write(b)

class StpmController:

    def __init__(self):
        self.ser = serial.Serial(baudrate=9600,timeout=1,port='/dev/ttyS1')
        self.conn = sqlite3.connect('/root/data/stpm.db')
        self.cconn = sqlite3.connect('/root/data/data.db')
        self.watths = lib_db.read_db('meter_values', 'energy', self.conn)
        self.CALV = lib_db.read_db("calibration", "CHV", self.cconn)
        self.CALI = lib_db.read_db("calibration", "CHC", self.cconn)
        self.set_calibration_value_voltage([(int(self.CALV) & 0xFF), ((int(self.CALV) >> 8) + 0xF0)])
        self.set_calibration_value_current([(int(self.CALI) & 0xFF), ((int(self.CALI) >> 8) + 0xF0)])
        self.CALV = 0.875
        self.CALI = 0.875
        self.cconn.close()
        self.set_gain()
        self.energy_overflows = 0
        self.volts = 0
        self.amps = 0
        self.watts = 0
        self.watths = lib_db.read_db('meter_values', 'energy', self.conn)
        self.power_sign = 1
        self.conn.close()
        t = Thread(target=self.thread_reader)
        t.start()

    # Channel 1 latch only
    def write_latch(self):
        l = [0x04, 0x04, 0xE0, 0x04]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0x04, 0x05, 0x20, 0x00]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)
    
    def set_gain(self):
        l = [0x18, 0x18, 0x27, 0x03]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0x18, 0x19, 0x27, 0x00]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)
        print("Register 18 now has:", self.ser.read(5).hex())

    def set_calibration_value_voltage(self, value):
        l = [0x08, 0x08, value[0], value[1]]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)
        time.sleep(0.02)

        print("Register 8 now has:", self.ser.read(5).hex())
     
    def set_calibration_value_current(self, value):
        l = [0x0A, 0x0a, value[0], value[1]]
        write_frame(self.ser, l)
        time.sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)
        time.sleep(0.02)

        print("Register 0A now has:", self.ser.read(5).hex())

    def get_energy_overflow(self):
        l = [0x20, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)

        overflow_bytes = bytearray(self.ser.read(5))
        overflow_bytes = overflow_bytes[:-1]
        overflow_bytes.reverse()
        overflow = (int.from_bytes(overflow_bytes, "big") & 0x00010000) >> 16
        sign = (int.from_bytes(overflow_bytes, "big") & 0x00001000) >> 12
        if(sign):
            self.power_sign = -1
            self.reset_overflow()
        else:
            self.power_sign = 1
        return overflow

    def reset_overflow(self):
        l = [0x20, 0x20, 0x00, 0x00]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0x20, 0x21, 0x00, 0x00]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)
        

    def get_rms_values(self):
        l = [0x48, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)

        rms_bytes = bytearray(self.ser.read(5))
        rms_bytes = rms_bytes[:-1]
        rms_bytes.reverse()

        # Shifting 15 to remove voltage, and 8 for the checksum
        current_raw = int.from_bytes(rms_bytes, "big") >> 15

        # Shifting by 8 to remove checksum, then and to get the 15 bits of voltage
        voltage_raw = (int.from_bytes(rms_bytes, "big")) & 0x00007FFF
        vLSB = ((VREF*(1+(R1/R2)))/(self.CALV*AV*32768))
        iLSB = VREF/(self.CALI*AI*KS*131072)
        return [voltage_raw*vLSB, current_raw*iLSB]

    def get_active_power(self):
        l = [0x5C, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)

        power_bytes = bytearray(self.ser.read(5))
        power_bytes = power_bytes[:-1]
        power_bytes.reverse()

        power_raw = int.from_bytes(power_bytes, "big") & 0x1FFFFFFF
        signed_power = 0
        if(self.power_sign == -1):
            signed_power = power_raw ^ 0x1FFFFFFF
        else:
            signed_power = power_raw

        pLSB = (VREF*VREF*(1+(R1/R2)))/(AV*AI*KS*self.CALV*self.CALI*268435456)

        return pLSB*signed_power

    def get_active_energy(self):
        l = [0x54, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        write_frame(self.ser, l)

        time.sleep(0.02)

        energy_bytes = bytearray(self.ser.read(5))
        energy_bytes = energy_bytes[:-1]
        energy_bytes.reverse()

        energy_raw = int.from_bytes(energy_bytes, "big")

        eLSB = (VREF*VREF*(1+(R1/R2)))/(DCLK*AV*AI*KS*self.CALV*self.CALI*471859200)
        
        return energy_raw*eLSB

    def get_meter_values(self):
        return (self.amps, self.volts, self.watths, self.watts)

    def thread_reader(self):
        conn = sqlite3.connect("/root/data/stpm.db")
        while True:
            self.write_latch()
            time.sleep(0.02)
            overflowed = self.get_energy_overflow()
            time.sleep(0.02)
            self.energy_overflows = self.energy_overflows + overflowed
            if (overflowed == 1):
                self.reset_overflow()
            time.sleep(0.02)
            additional_energy = (self.energy_overflows*(2**32)*((VREF*VREF*(1+(R1/R2)))/(DCLK*AV*AI*KS*self.CALV*self.CALI*471859200)))
            self.watths = (self.get_active_energy() + additional_energy)
            time.sleep(0.02)
            rms_vals = self.get_rms_values()
            time.sleep(0.02)
            self.volts = rms_vals[0]
            self.amps = rms_vals[1]
            temp_watts = self.get_active_power()
            if temp_watts > 50000:
                self.watts = 0
            else:
                self.watts = temp_watts
            lib_db.update("meter_values", "energy", round(self.watths, 3), conn)
            time.sleep(0.9)
