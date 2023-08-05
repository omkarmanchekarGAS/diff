import sys 
# for checking whether or not the code is actually interacting with hardware or not; pass 0 as
# an argument if you just want a "simulation", otherwise, pass 1

HARDW = int(sys.argv[1]) == 1
if HARDW:
    from OmegaExpansion import onionI2C
import struct
from typing import List

ADDRESS = 0x09


class MicroController:
    if HARDW:
        i2c: onionI2C.OnionI2C

    def __init__(self):
        if HARDW:
            self.i2c = onionI2C.OnionI2C()

    def decode_byte_list(self, byte_list: List[int]):
        decoded_bytes = []
        for b in byte_list:
            decoded_bytes.append(b.to_bytes(1, "little"))
        bytes_string = b"".join(decoded_bytes)
        return bytes_string

    def encode_byte_string(self, byte_string: str):
        encoded_bytes = []
        for b in byte_string:
            encoded_bytes.append(b)
        return encoded_bytes

    def read_bytes(self, device, address, num_bytes):
        if HARDW:
            readBytes = self.i2c.readBytes(device, address, num_bytes)
            decoded_byte_string = self.decode_byte_list(readBytes)
            return decoded_byte_string

    def write_bytes(self, device, address, byte_string):
        if HARDW:
            encoded_bytes = self.encode_byte_string(byte_string)
            self.i2c.writeBytes(device, address, encoded_bytes)

    def read_charge_current(self):
        byte_string = self.read_bytes(ADDRESS, 0x00, 4)
        return struct.unpack("<f", byte_string)[0]

    def write_charge_current(self, current: float):
        byte_string = struct.pack("<f", 123.456)
        self.write_bytes(ADDRESS, 0x00, byte_string)

    def read_ac_energy(self):
        byte_string = self.read_bytes(ADDRESS, 0x08, 8)
        return struct.unpack("<Q", byte_string)[0]

    def read_mode(self):
        byte_string = self.read_bytes(ADDRESS, 0x04, 4)
        return struct.unpack("<i", byte_string)[0]

    def write_mode(self, mode: int):
        byte_string = struct.pack("<i", mode)
        self.write_bytes(ADDRESS, 0x04, byte_string)

    def unauthorize_charging(self):
        self.write_mode(0)

    def authorize_charging(self):
        self.write_mode(1)

    def power_down(self):
        self.write_mode(100)

    def read_state(self):
        byte_string = self.read_bytes(ADDRESS, 0x07, 4)
        return struct.unpack("<i", byte_string)[0]

    def read_ac_reactive_energy(self):
        byte_string = self.read_bytes(ADDRESS, 0x48, 8)
        return struct.unpack("<Q", byte_string)[0]

    def read_ac_vrms(self):
        byte_string = self.read_bytes(ADDRESS, 0x88, 4)
        return struct.unpack("<f", byte_string)[0]

    def read_ac_irms(self):
        byte_string = self.read_bytes(ADDRESS, 0x8C, 4)
        return struct.unpack("<f", byte_string)[0]

    def read_ac_powerfactor(self):
        byte_string = self.read_bytes(ADDRESS, 0x90, 4)
        return struct.unpack("<f", byte_string)[0]

    def read_ac_power(self):
        byte_string = self.read_bytes(ADDRESS, 0x94, 4)
        return struct.unpack("<f", byte_string)[0]

    def read_ac_reactive_power(self):
        byte_string = self.read_bytes(ADDRESS, 0x98, 4)
        return struct.unpack("<f", byte_string)[0]

    def read_temp(self):
        byte_string = self.read_bytes(ADDRESS, 0x9C, 4)
        return struct.unpack("<f", byte_string)[0]
