import serial
from time import sleep
import math

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

class STPM():
    CALV = .875
    CALI = .875

    ser = serial.Serial

    def __init__(self, calv, cali):
        self.ser = serial.Serial(baudrate=9600,timeout=1,port='/dev/ttyS1')
        self.CALV = calv
        self.CALI = cali

    def calcCRC(self, bytes):
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
                loc_idx = loc_idx + 1
        return checksum

    def byteReverse(self, b):
        b = ((b >> 1) & 0x55) | ((b << 1) & 0xaa)
        b = ((b >> 2) & 0x33) | ((b << 2) & 0xcc)
        b = ((b >> 4) & 0x0f) | ((b << 4) & 0xf0)
        return b

    def uart_frame(self, byte_list):
        copy = [self.byteReverse(i) for i in byte_list]
        byte_list.append(self.byteReverse(self.calcCRC(copy)))
        return byte_list

    def write_frame(self, byte_list):
        b = bytearray(self.uart_frame(byte_list))
        # print("Wrote:", b.hex())
        self.ser.write(b)

    def enable_auto_latch(self):
        l = [0x04, 0x04, 0xE0, 0x04]
        self.write_frame(l)

        sleep(0.2)
        self.ser.read(5)

        l = [0x04, 0x05, 0x80, 0x00]
        self.write_frame(l)

        sleep(0.2)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)

        sleep(0.2)
        reg = self.ser.read(5).hex()
        if(len(reg) < 1):
            print("STPM RETURNED NOTHING")
            return 0
        print("Register 4 now has:", reg)
        return 1

    def disable_auto_latch(self):
        l = [0x04, 0x04, 0xE0, 0x04]
        self.write_frame(l)

        sleep(0.2)
        self.ser.read(5)

        l = [0x04, 0x05, 0x00, 0x00]
        self.write_frame(l)

        sleep(0.2)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)

        sleep(0.2)
        print("Register 4 now has:", self.ser.read(5).hex())
    
    def set_gain(self):
        l = [0x18, 0x18, 0x27, 0x03]
        self.write_frame(l)

        sleep(0.02)
        self.ser.read(5)

        l = [0x18, 0x19, 0x27, 0x00]
        self.write_frame(l)

        sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)

        sleep(0.02)
        print("Register 18 now has:", self.ser.read(5).hex())

    def get_rms_values(self):
        l = [0x48, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)

        sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)

        sleep(0.02)

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
        self.write_frame(l)

        sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)

        sleep(0.02)

        power_bytes = bytearray(self.ser.read(5))
        power_bytes = power_bytes[:-1]
        power_bytes.reverse()

        power_raw = int.from_bytes(power_bytes, "big") & 0x1FFFFFFF
        pLSB = (VREF*VREF*(1+(R1/R2)))/(AV*AI*KS*self.CALV*self.CALI*268435456)

        return pLSB*power_raw

    def get_active_energy(self):
        l = [0x54, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)

        sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)

        sleep(0.02)

        energy_bytes = bytearray(self.ser.read(5))
        energy_bytes = energy_bytes[:-1]
        energy_bytes.reverse()

        energy_raw = int.from_bytes(energy_bytes, "big")

        eLSB = (VREF*VREF*(1+(R1/R2)))/(DCLK*AV*AI*KS*self.CALV*self.CALI*471859200)
        
        return energy_raw*eLSB
    
    def calculate_calibration_constants(self, VN, IN, vavg, cavg):
        if(vavg <= 0 or cavg <= 0):
            print("STPM MEASURING 0")
            return 0
        XV = (VN*AV*self.CALV*(2**15))/(VREF*(1+R1/R2))
        XI = (IN*AI*self.CALI*KS*(2**17))/((math.sqrt(2))*VREF) #(IN*(math.sqrt(2))*AI*CALI*KINT*KS*(2**17))/VREF

        CHV = 14336 * (XV/vavg) - 12288
        CHC = 14336 * (XI/cavg) - 12288

        #KV = .125 * (CHV/2048) + .75
        #KI = .125 * (CHC/2048) + .75
        #print("Voltage calibration cosntant: " + hex(int(CHV)))
        #print("Current calibration cosntant: " + hex(int(CHC)))
        
        #print([((int(CHV) >> 8) + 0xF0), (int(CHV) & 0xFF)])
        #print([((int(CHC) >> 8) + 0xF0), (int(CHC) & 0xFF)])

        return [CHV, CHC]
    
    def set_calibration_value_voltage(self, value):
        l = [0x08, 0x08, value[0], value[1]]
        self.write_frame(l)

        sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)
        sleep(0.02)

        print("Register 8 now has:", self.ser.read(5).hex())
        
    def set_calibration_value_current(self, value):
        l = [0x0A, 0x0a, value[0], value[1]]
        self.write_frame(l)
        sleep(0.02)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)
        sleep(0.02)

        print("Register 0A now has:", self.ser.read(5).hex())

    def set_calibration_value_phase(self, PHV, PHC):
        MSW_PHC = int(PHC) & 0x1F0
        LSW_PHC = int(PHC) & 0xF
        l = [0x06, 0x06, 0x00, LSW_PHC << 4]
        self.write_frame(l)

        sleep(0.1)
        self.ser.read(5)

        MSW_LSB = (PHV << 6) + MSW_PHC
        l = [0x06, 0x07, MSW_LSB, 0x00]
        self.write_frame(l)

        sleep(0.1)
        self.ser.read(5)

        l = [0xFF, 0xFF, 0xFF, 0xFF]
        self.write_frame(l)

        sleep(0.1)
        print("Register 6 now has:", self.ser.read(5).hex())

# def voltage_current_calibration(ser, VN, IN):
#     set_gain(ser)

#     #sampling RMS values and averaging them together
#     vavg = 0
#     cavg = 0
#     samples = 25
#     for i in range(0,samples):
#         values = get_rms_values(ser)
#         vavg = vavg + values[0]
#         cavg = cavg + values[1]

#     vavg = vavg/samples
#     cavg = cavg/samples

#     #calculating calibration values for voltage and current
#     XV = (VN*AV*CALV*(2**15))/(VREF*(1+R1/R2))
#     XI = (IN*AI*CALI*KS*(2**17))/((math.sqrt(2))*VREF) #(IN*(math.sqrt(2))*AI*CALI*KINT*KS*(2**17))/VREF

#     CHV = 14336 * (XV/vavg) - 12288
#     CHC = 14336 * (XI/cavg) - 12288

#     KV = .125 * (CHV/2048) + .75
#     KI = .125 * (CHC/2048) + .75
#     print(hex(int(CHV)))
#     print(hex(int(CHC)))
#     print([((int(CHV) >> 8) + 0xF0), (int(CHV) & 0xFF)])
#     print([((int(CHC) >> 8) + 0xF0), (int(CHC) & 0xFF)])
#     #print(hex(int(KV)))
#     #print(hex(int(KI)))
#     #print([((int(KV) >> 8) + 0xF0), (int(KV) & 0xFF)])
#     #print([((int(KI) >> 8) + 0xF0), (int(KI) & 0xFF)])

#     #setting calibration constants for voltage and current
#     #cast CHV/CHC to int??? Other way?????
#     try:
#         set_calibration_value_voltage(ser, [(int(CHV) & 0xFF), ((int(CHV) >> 8) + 0xF0)])
#         set_calibration_value_current(ser, [(int(CHC) & 0xFF), ((int(CHC) >> 8) + 0xF0)])
#     except Exception as e:
#         print(e)
#         return [-1,-1]

#     return [CHV, CHC]

# def calibrate():
#     ser = serial.Serial(baudrate=9600,timeout=1,port='/dev/ttyS1')
#     enable_auto_latch(ser)
#     set_gain(ser)

#     conn = sqlite3.connect("/root/data/data.db")

#     CHV = ldb.read_db('calibration', 'CHV', conn)
#     CHC = ldb.read_db('calibration', 'CHC', conn)
#     PHV = ldb.read_db('calibration', 'PHV', conn)
#     PHC = ldb.read_db('calibration', 'PHC', conn)

#     conn.close()

#     set_calibration_value_voltage(ser,CHV)
#     set_calibration_value_current(ser,CHC)
#     set_calibration_value_phase(ser, PHV, PHC)

#     ser.close()

# def main():
#     ser = serial.Serial(baudrate=9600,timeout=1,port='/dev/ttyS1')
#     conn = sqlite3.connect("/root/data/stpm.db")
    
#     while (1):
#         rms = get_rms_values(ser)
#         current = get_real_current(rms[1])
#         voltage = get_real_voltage(rms[0])
#         stuff = get_active_energy(ser)
#         energy = get_real_energy(stuff[0], stuff[1])
#         power = get_real_power(get_active_power(ser))

#         ldb.update('meter_values', 'current', current, conn)
#         ldb.update('meter_values', 'voltage', voltage, conn)
#         ldb.update('meter_values', 'energy', energy, conn)
#         ldb.update('meter_values', 'power', power, conn)

#         time.sleep(10)
