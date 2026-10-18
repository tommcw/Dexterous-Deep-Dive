# Attempt to open serial port #1
# Author: Thomas McWatters

import serial

ser = serial.Serial(
    '/dev/ttyUSB0',
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

print("Port opened:", ser.is_open)
print("Port:", ser.name)

ser.close()