from lib_i2c import I2C
from time import sleep

i = I2C("/dev/i2c-0")

msgs = [I2C.Message([0x03]), I2C.Message([0x00], read=True)]
i.transfer(0x38, msgs)

if (msgs[1].data[0] == 249):
	print("Output pins already set")
else:
	print("Configuring output pins")
	msgs = [I2C.Message([0x03, 0xF9])]
	i.transfer(0x38, msgs)


# write low pulse 3 times to SYN pin (IO1)

for j in range(3):
	msgs = [I2C.Message([0x01, 0xFD])]
	i.transfer(0x38, msgs)
	sleep(0.01)
	msgs = [I2C.Message([0x01, 0xFF])]
	i.transfer(0x38, msgs)
	sleep(0.01)


# write final low pulse to SCS pin (IO2)

msgs = [I2C.Message([0x01, 0xFB])]
i.transfer(0x38, msgs)
sleep(0.01)
msgs = [I2C.Message([0x01, 0xFF])]
i.transfer(0x38, msgs)


