# Attempt to get serial response from robotic hand. #3
# Author: Thomas McWatters
# Unsuccessfull attempt. Error in the 0x40 and checksum.

import time
import serial
PORT = "/dev/ttyUSB0"

req = bytes([0xEB, 0x90, 0x05, 0x04, 0x11, 0x40, 0x05, 0x02, 0xE1])

ser = serial.Serial(PORT, 115200, timeout=0.2)
ser.setDTR(False)
ser.setRTS(True)
ser.write(req)
ser.flush()
time.sleep(0.01)
ser.setRTS(False)
time.sleep(0.05)
resp = ser.read(64)
print(resp.hex(" "))
ser.close()