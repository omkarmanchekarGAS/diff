import lib_db as ldb
import serial
import time
import sqlite3
import math

DCLK = (7812.5)
VREF = (1.18)
AV = (2)
AI = (2)
CALV = (0.875)
CALI = (0.875)
R1 = (750000)
R2 = (470)
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

# These functions are only needed when LSB bit is set to 1. (0 is default)
# (reversed frame stuff)
def uart_reversed_frame(byte_list):
    byte_list = [byteReverse(i) for i in byte_list]
    copy = [i for i in byte_list]
    copy.append(byteReverse(calcCRC(byte_list)))
    return copy

def write_reversed_frame(ser, byte_list):
    b = bytearray(uart_reversed_frame(byte_list))
    ser.write(b)

def enable_auto_latch(ser):
    l = [0x04, 0x04, 0xE0, 0x04]
    write_frame(ser, l)

    time.sleep(0.1)
    ser.read(5)

    l = [0x04, 0x05, 0x80, 0x00]
    write_frame(ser, l)

    time.sleep(0.1)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.1)
    print("Register 4 now has:", ser.read(5).hex())

def get_energy_overflow(ser):
    l = [0x1C, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)

    overflow_bytes = bytearray(ser.read(5))
    overflow_bytes = overflow_bytes[:-1]
    overflow_bytes.reverse()
    # print("Received:", energy_bytes.hex())

    return int.from_bytes(overflow_bytes, "big") & 0x00010000

def set_energy_overflow(ser):
    l = [0x1C, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)

    overflow_bytes = bytearray(ser.read(5))
    overflow_bytes = overflow_bytes[:-1]
    overflow_bytes.reverse()
    value1 = overflow_bytes & 0xFFFE
    value2 = overflow_bytes & 0xFFFF

    l = [0x1C, 0x1C, value2, value1]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)
    time.sleep(0.02)

    print("Register 14 now has:", ser.read(5).hex())

def get_rms_values(ser):
    l = [0x48, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)

    rms_bytes = bytearray(ser.read(5))
    rms_bytes = rms_bytes[:-1]
    rms_bytes.reverse()
    # print("Received:", rms_bytes.hex())

    # Shifting 15 to remove voltage, and 8 for the checksum
    current_raw = int.from_bytes(rms_bytes, "big") >> 15
    # print("Current Value:", current_raw)

    # Shifting by 8 to remove checksum, then and to get the 15 bits of voltage
    voltage_raw = (int.from_bytes(rms_bytes, "big")) & 0x00007FFF
    # print("Voltage Value:", voltage_raw)
    return [voltage_raw, current_raw]

def get_active_power(ser):
    l = [0x5C, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)

    power_bytes = bytearray(ser.read(5))
    power_bytes = power_bytes[:-1]
    power_bytes.reverse()
    # print("Received:", power_bytes.hex())

    power_raw = int.from_bytes(power_bytes, "big") & 0x1FFFFFFF
    # print("Active Power Value:", power_raw)

    return power_raw

def get_active_energy(ser):
    l = [0x54, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)

    energy_bytes = bytearray(ser.read(5))
    energy_bytes = energy_bytes[:-1]
    energy_bytes.reverse()
    # print("Received:", energy_bytes.hex())

    energy_raw = int.from_bytes(energy_bytes, "big")
    # print("Active Energy Value:", energy_raw)

    overflow = get_energy_overflow(ser)
    conn = sqlite3.connect('/root/data/stpm.db')
    times_overflowed = ldb.read_db('meter_values', 'overflows', conn)
    if overflow != 0:
        ldb.update('meter_values', 'overflows', times_overflowed+1, conn)
        set_energy_overflow(ser)
        times_overflowed = times_overflowed + 1
        print("overflowed :(")

    conn.close()
    
    return (energy_raw, times_overflowed)

#sets gain of first channel, must set second separately if using
#gain set to 2X
def set_gain(ser):
    l = [0x18, 0x18, 0x27, 0x03]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0x18, 0x19, 0x27, 0x00]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)
    print("Register 18 now has:", ser.read(5).hex())

def set_calibration_value_voltage(ser, value):
    l = [0x08, 0x08, value[0], value[1]]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)
    time.sleep(0.02)

    print("Register 8 now has:", ser.read(5).hex())
     
def set_calibration_value_current(ser, value):
    l = [0x0A, 0x0a, value[0], value[1]]
    write_frame(ser, l)
    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)
    time.sleep(0.02)

    print("Register 0A now has:", ser.read(5).hex())

def set_calibration_value_phase(ser, PHV, PHC):
    MSW_PHC = int(PHC) & 0x1F0
    LSW_PHC = int(PHC) & 0xF
    l = [0x06, 0x06, 0x00, LSW_PHC << 4]
    write_frame(ser, l)

    time.sleep(0.1)
    ser.read(5)

    MSW_LSB = (PHV << 6) + MSW_PHC
    l = [0x06, 0x07, MSW_LSB, 0x00]
    write_frame(ser, l)

    time.sleep(0.1)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.1)
    print("Register 6 now has:", ser.read(5).hex())

def get_real_voltage(voltage):
    vLSB = ((VREF*(1+(R1/R2)))/(CALV*AV*32768))
    result = voltage*vLSB
    return result

def get_real_current(current):
    iLSB = VREF/(CALI*AI*KS*131072)
    result = current*iLSB
    return result

def get_real_power(power):
    pLSB = (VREF*VREF*(1+(R1/R2)))/(AV*AI*KS*CALV*CALI*268435456)
    result = power*pLSB
    return result

def get_real_energy(energy_raw, times_overflowed):
    energy = energy_raw + times_overflowed * 0xFFFFFFFF
    
    eLSB = (VREF*VREF*(1+(R1/R2)))/(DCLK*AV*AI*KS*CALV*CALI*471859200)
    result = energy*eLSB
    return result


def get_meter_values():
    conn = sqlite3.connect("/root/data/stpm.db")
    current = ldb.read_db('meter_values', 'current', conn)
    voltage = ldb.read_db('meter_values', 'voltage', conn)
    energy = ldb.read_db('meter_values', 'energy', conn)
    power = ldb.read_db('meter_values', 'power', conn)
    conn.close()
    return (current,voltage,energy,power)

def voltage_current_calibration(ser, VN, IN):
    set_gain(ser)

    #sampling RMS values and averaging them together
    vavg = 0
    cavg = 0
    samples = 25
    for i in range(0,samples):
        values = get_rms_values(ser)
        vavg = vavg + values[0]
        cavg = cavg + values[1]

    vavg = vavg/samples
    cavg = cavg/samples

    #calculating calibration values for voltage and current
    XV = (VN*AV*CALV*(2**15))/(VREF*(1+R1/R2))
    XI = (IN*AI*CALI*KS*(2**17))/((math.sqrt(2))*VREF) #(IN*(math.sqrt(2))*AI*CALI*KINT*KS*(2**17))/VREF

    CHV = 14336 * (XV/vavg) - 12288
    CHC = 14336 * (XI/cavg) - 12288

    KV = .125 * (CHV/2048) + .75
    KI = .125 * (CHC/2048) + .75
    print(hex(int(CHV)))
    print(hex(int(CHC)))
    print([((int(CHV) >> 8) + 0xF0), (int(CHV) & 0xFF)])
    print([((int(CHC) >> 8) + 0xF0), (int(CHC) & 0xFF)])
    #print(hex(int(KV)))
    #print(hex(int(KI)))
    #print([((int(KV) >> 8) + 0xF0), (int(KV) & 0xFF)])
    #print([((int(KI) >> 8) + 0xF0), (int(KI) & 0xFF)])

    #setting calibration constants for voltage and current
    #cast CHV/CHC to int??? Other way?????
    try:
        set_calibration_value_voltage(ser, [(int(CHV) & 0xFF), ((int(CHV) >> 8) + 0xF0)])
        set_calibration_value_current(ser, [(int(CHC) & 0xFF), ((int(CHC) >> 8) + 0xF0)])
    except Exception as e:
        print(e)
        return [-1,-1]

    return [CHV, CHC]

def calibrate():
    ser = serial.Serial(baudrate=9600,timeout=1,port='/dev/ttyS1')
    enable_auto_latch(ser)
    set_gain(ser)

    conn = sqlite3.connect("/root/data/data.db")

    CHV = ldb.read_db('calibration', 'CHV', conn)
    CHC = ldb.read_db('calibration', 'CHC', conn)
    PHV = ldb.read_db('calibration', 'PHV', conn)
    PHC = ldb.read_db('calibration', 'PHC', conn)

    conn.close()

    set_calibration_value_voltage(ser,CHV)
    set_calibration_value_current(ser,CHC)
    set_calibration_value_phase(ser, PHV, PHC)

    ser.close()

def main():
    ser = serial.Serial(baudrate=9600,timeout=1,port='/dev/ttyS1')
    conn = sqlite3.connect("/root/data/stpm.db")
    
    while (1):
        rms = get_rms_values(ser)
        current = get_real_current(rms[1])
        voltage = get_real_voltage(rms[0])
        stuff = get_active_energy(ser)
        energy = get_real_energy(stuff[0], stuff[1])
        power = get_real_power(get_active_power(ser))

        ldb.update('meter_values', 'current', current, conn)
        ldb.update('meter_values', 'voltage', voltage, conn)
        ldb.update('meter_values', 'energy', energy, conn)
        ldb.update('meter_values', 'power', power, conn)

        time.sleep(10)

def get_raw_data(ser):
    l = [0x30, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)

    volt_bytes = ((bytearray(ser.read(5)))[:-1])
    volt_bytes.reverse()
    volt_bytes = int.from_bytes(volt_bytes, "big") & 0xFFFFFF
    print("Raw Voltage:", volt_bytes.hex())

    l = [0x32, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)
    ser.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(ser, l)

    time.sleep(0.02)

    curr_bytes = ((bytearray(ser.read(5)))[:-1]).reverse()
    curr_bytes = curr_bytes & 0xFFFFFF
    print("Raw Voltage:", curr_bytes.hex())

if __name__ == '__main__':
    main()