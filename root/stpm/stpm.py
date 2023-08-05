import serial
import time

DCLK = (7812.5)
SCLK = (4000000)
VREF = (1.18)
AV = (2)
AI = (2)
CALV = (0.875)
CALI = (0.875)
R1 = (810000)
R2 = (470)
KS = (3.33/1000)
CP = (0.5*(R2/(R1+R2))*KS*((AV*AI*CALV*CALI)/(VREF*VREF))*DCLK)

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

def write_frame(byte_list, device):
    b = bytearray(uart_frame(byte_list))
    print("Wrote:", b.hex())
    device.write(b)

# These functions are only needed when LSB bit is set to 1. (0 is default)
# (reversed frame stuff)
def uart_reversed_frame(byte_list):
    byte_list = [byteReverse(i) for i in byte_list]
    copy = [i for i in byte_list]
    copy.append(byteReverse(calcCRC(byte_list)))
    return copy

def write_reversed_frame(byte_list, device):
    b = bytearray(uart_reversed_frame(byte_list))
    device.write(b)

def enable_auto_latch(device):

    l = [0x04, 0x04, 0xE0, 0x04]
    write_frame(l, device)

    time.sleep(0.02)

    device.read(5)

    l = [0x04, 0x05, 0x80, 0x00]
    write_frame(l, device)

    time.sleep(0.02)

    device.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(l, ser)

    time.sleep(0.02)

    print("Register 4 now has:", device.read(5).hex())

def get_rms_values(device):

    l = [0x48, 0xFF, 0xFF, 0xFF]
    write_frame(l, device)

    time.sleep(0.02)
    device.read(5)

    l = [0xFF, 0xFF, 0xFF, 0xFF]
    write_frame(l, device)

    time.sleep(0.02)

    rms_bytes = bytearray(device.read(5))
    rms_bytes = rms_bytes[:-1]
    rms_bytes.reverse()
    print("Received:", rms_bytes.hex())

    # Shifting 15 to remove voltage, and 8 for the checksum
    current_raw = int.from_bytes(rms_bytes, "big") >> 15
    print("Current Value:", current_raw)

    # Shifting by 8 to remove checksum, then and to get the 15 bits of voltage
    voltage_raw = (int.from_bytes(rms_bytes, "big")) & 0x00007FFF
    print("Voltage Value:", voltage_raw)

ser = serial.Serial(port='/dev/ttyS1', timeout=5, baudrate=9600)
enable_auto_latch(ser)
# get_rms_values(ser)
