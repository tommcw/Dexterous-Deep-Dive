# Attempt to get a serial response from robotic hand. #4
# Author: Thomas McWatters


import time
import serial
PORT = "/dev/ttyUSB0"

# last weeks version 0x40 is incorrect ???
#req = bytes([0xEB, 0x90, 0x05, 0x04, 0x11, 0x40, 0x05, 0x02, 0x61])
# therefore checksum is incorrect.
# req = bytes([0xEB, 0x90, 0x05, 0x04, 0x11, 0x40, 0x05, 0x02, 0xE1])


# * req = bytes([0xEB, 0x90, 0x05, 0x04, 0x11, 0xC0, 0x05, 0x02, 0xE1])
req = bytes([0xeb, 0x90, 0x05, 0x05, 0x12, 0xd6, 0x05, 0x64, 0x00, 0x5b])

# Correct way to ask:
# Header + Hand ID 5 + Length of the frame data is 4,
# -   0x11 is the flag to READ A REGISTER ; 0x12 is to WRITE A REGISTER
#      NB: when writing to a register the length of the frame needs to
#          be Register Length + 3 and the data goes before the checksum
# -   then Lower order 8 bits of register
# -   the Upper part of register
# -   register length is 2.

ser = serial.Serial(PORT, 115200, timeout=0.2)
# the following paramaters are not required here
# bytesize=serial.EIGHTBITS,
# parity=serial.PARITY_NONE,
# stopbits=serial.STOPBITS_ONE,

#ser.setDTR(False) # Set Data Terminal Ready control line to inactive(LOW)
# Appears that the robotic hand either ignores DTR line or it is repurposed
ser.setRTS(True) # Transmit mode
ser.write(req)
ser.flush() # pauses execution until everything in the buffer is sent.
time.sleep(0.01) # allow some time for processing on the other end.
ser.setRTS(False) # Transmit mode off.
time.sleep(0.05)
resp = ser.read(64)
print(resp.hex(" "))
ser.close()

# Serial connection signals:
# TX: data sent from computer
# RX: data recieved
# RTS: additional control signal for switching data flow direction.
# DTR: tradationaly used for "Hello modem, I am powered on."
# GND: reference voltage