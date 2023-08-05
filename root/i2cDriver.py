from time import sleep
from lib_i2c import I2C
import lib_db
import lib_RTC
import websockets
import asyncio
import os
import sqlite3
import output_config

device = I2C("/dev/i2c-0")
current_dict = {0: 80, 128: 80, 64: 80, 192: 72, 32: 64, 160: 56, 96: 48, 224: 40, 16: 36, 144: 32, 80: 28, 208: 24, 48: 20, 176: 16, 112: 12, 240: 0}

def read_byte_data(address, byte):
    msgs = [I2C.Message([byte]), I2C.Message([0x00], read=True)]
    device.transfer(address, msgs)
    return msgs[1].data[0]

def write_byte_data(address, byte, value):
    msgs = [I2C.Message([byte, value])]
    device.transfer(address, msgs)

def write_bytes_data(address, byte, values):
    msgs = [I2C.Message([byte] + values)]
    device.transfer(address, msgs)


# ensure I2C has had enough time to init
sleep(1)

# if over 9 we reset I2C with GPIO
consecutive_faults = 0

set_time = False

dip_current = 0
allowed_current = 0

SETUP_MODE = 0
PREV_SETUP_MODE = 0

conn = sqlite3.connect("/root/data/data.db")

# continuously attempt to read DIP switches. Will block if I2C is hung
# also read setup mode switch and set db value
while True:
    try:
        sleep(0.2)
        IOExpanderValues = read_byte_data(0x38, 0)
        dip_current = current_dict[(0xF0 & IOExpanderValues)]
        setup_mode = not 0x01 & IOExpanderValues
        lib_db.update('status', 'dip_switch_current', dip_current, conn)
        if setup_mode:
            print("Setup Mode with DIP Switch setting:", dip_current)
            lib_db.update('status', 'setup_mode', 1, conn)
            SETUP_MODE = 1
            PREV_SETUP_MODE = 1
        else:
            print("Non-Setup Mode with DIP Switch settings:", dip_current)
            lib_db.update('status', 'setup_mode', 0, conn)
            SETUP_MODE = 0
            PREV_SETUP_MODE = 0
    except Exception as e:
        consecutive_faults = consecutive_faults + 1
        print("Failed IOExpander reads/writes")
        print(e)
        continue
    consecutive_faults = 0
    break

# ensure output current is set properly at first
output_config.update_output_current(32)

status = 0
fault_code = 0
previous_status = 0
previous_fault_code = 0

while True:

    try:
        # check for internet and handle RTC and system time
        if (not set_time) and lib_db.read_db('status', 'internet_connected', conn):
            print("setting system time with ntp")
            set_time = True
            lib_RTC.set_from_ntpd_time(device)
    except Exception as e:
        print(e)

    # read setup mode switch again for screen display purposes
    try:
        sleep(0.2)
        IOExpanderValues = read_byte_data(0x38, 0)
        setup_mode = not 0x01 & IOExpanderValues
        if setup_mode:
            SETUP_MODE = 1
        else:
            SETUP_MODE = 0

        consecutive_faults = 0

        if PREV_SETUP_MODE != SETUP_MODE:
            os.system("reboot")
    except Exception as e:
        consecutive_faults = consecutive_faults + 1
        print("Failed to read DIP switches")
        print(e)


    # read from ATTiny
    try:
        sleep(0.02)
        previous_status = status
        previous_fault_code = fault_code
        status = read_byte_data(0x14, 0)
        status_check = read_byte_data(0x14, 1)
        fault_code = read_byte_data(0x14, 2)
        fault_code_check = read_byte_data(0x14, 3)
        print("ATTiny Status: ", status)
        print("ATTiny Fault:", fault_code)
        if ((status + status_check) != 256 or (fault_code + fault_code_check) != 256):
            print("Bad data from ATTiny")
            status = 7
            fault_code = 12
        else:
            consecutive_faults = 0
        
        if (previous_status != status or previous_fault_code != fault_code):
            lib_db.update('status', 'pilot_state', status, conn)
            lib_db.update('status', 'fault_code', fault_code, conn)

            
    except Exception as e:
        consecutive_faults = consecutive_faults + 1
        print("failed ATTiny reads/writes")
        print(e)

    # issue authorized current to ATTiny
    while True:
        try:
            sleep(0.02)
            allowed_current = lib_db.read_db('output', 'current', conn)
            twos_complement = 256-allowed_current
            if (allowed_current != 0 and SETUP_MODE == 0):
                write_byte_data(0x14, 0, allowed_current)
                write_byte_data(0x14, 3, twos_complement)
            else:
                write_byte_data(0x14, 0, 0)
                write_byte_data(0x14, 3, 0)
        except Exception as e:
            consecutive_faults = consecutive_faults + 1
            print("failed to authorize current")
            print(e)
            continue
        consecutive_faults = 0
        break


    # format EBike buffer, calculate checksum, and send
    buffer = [0x00 for i in range(115)]

    while True:
        try:
            sleep(0.02)
            version = read_byte_data(0x08, 0x01)
            print("EBIKE Version:", version)
            buffer[1] = version
            # 100 is added to celsius temperature on EBIKE side
            temperature = read_byte_data(0x08, 0x70)
            buffer[112] = temperature
            lib_db.update('status', 'temperature', temperature-100, conn)

            # set colors in buffer
            led_brightness = lib_db.read_db('config', 'led_brightness', conn)/100.0

            logo_led = lib_db.read_db('output', 'logo_led', conn)
            #side_led = lib_db.read_db('output', 'side_led', conn)
            buffer[2] = int(int(logo_led[0:2], 16)*0.75)
            buffer[3] = int(int(logo_led[2:4], 16)*0.75)
            buffer[4] = int(int(logo_led[4:6], 16)*0.75)


            side_led = [255, 255, 255]
            print(str(allowed_current))
            if(SETUP_MODE == 0):
                if (status < 4 and dip_current == 0):
                    line3 = "Invalid DIP Switches"
                elif (status == 1):
                    side_led = [0, 255, 0]
                    line3 = "Available"
                elif (status == 2):
                    side_led = [255, 0, 255]
                    line3 = "Vehicle Detected"
                elif (status == 2 and allowed_current == 0):
                    side_led = [255, 0, 255]
                    line3 = "Unauthorized Charge"
                elif (status == 3 and allowed_current != 0):
                    side_led = [0, 0, 255]
                    line3 = "Charging"
                elif (status == 3 and allowed_current == 0):
                    side_led = [255, 0, 255]
                    line3 = "Finishing"
                elif (status > 3):
                    side_led = [255, 0, 0]
                    line3 = 'FAULTED: CODE ' + str(fault_code)
                line2 = lib_db.read_db('output', 'line2', conn)
            else:
                line3 = "SETUP MODE"
                line2 = "IP:" + os.popen("uci get network.vlan.ipaddr").read()[:-1]


            side_led = [int(x*led_brightness*0.75) for x in side_led]
            buffer[5] = side_led[0]
            buffer[6] = side_led[1]
            buffer[7] = side_led[2]

            # set message lines
            line1 = lib_db.read_db('output', 'line1', conn)

            #if SETUP_MODE == 1:
            #    line2 = "SETUP MODE"
            #else:
            #    line2 = lib_db.read_db('output', 'line2', conn)

            line4 = lib_db.read_db('output', 'line4', conn)
            buffer[8] = len(line1)
            buffer[9:9+len(line1)] = [ord(c) for c in line1]
            buffer[30] = len(line2)
            buffer[31:31+len(line2)] = [ord(c) for c in line2]
            buffer[52] = len(line3)
            buffer[53:53+len(line3)] = [ord(c) for c in line3]
            buffer[74] = len(line4)
            buffer[75:75+len(line4)] = [ord(c) for c in line4]

            # set top line
            topline = lib_db.read_db('output', 'topline', conn)
            buffer[96:96+len(topline)] = [ord(c) for c in topline]

            # set data latch, template and animation number
            temp_num = lib_db.read_db('output', 'temp_num', conn)
            anim_num = lib_db.read_db('output', 'anim_num', conn)
            buffer[0] = 0x80 + ((temp_num << 4) & 0x70) + (anim_num & 0x0F)

            if (len(buffer) != 115):
                print("buffer is being improperly formatted")
            else:
                # calculate checksum
                sum = 0
                for i in range(113):
                    sum = sum + buffer[i]

                buffer[113] = sum >> 8
                buffer[114] = sum & 0xFF

            print("Sending buffer: ", buffer)
            print("checksum:", (buffer[113] << 8) + buffer[114])

            write_bytes_data(0x08, 0x00, buffer)
        except Exception as e:
            consecutive_faults = consecutive_faults + 1
            print("Failed EBike reads/writes")
            print(e)
            continue
        consecutive_faults = 0
        break



    # reset GPIO
    if consecutive_faults > 9:
            print("doing GPIO reset")
            os.system("""echo "0" > /sys/class/gpio/gpio483/value""")
            sleep(0.5)
            os.system("""echo "1" > /sys/class/gpio/gpio483/value""")
            sleep(2)
            consecutive_faults = 0

    sleep(0.25)
