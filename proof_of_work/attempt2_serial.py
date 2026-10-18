# Attempt to get a serial response from robotic hand. #2
# Author: Thomas McWatters
# Unsuccessful communication with hand. No reply.
# The Hand ID is wrong. The checksum is incorrect.


import serial

ser = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=115200,
    bytesize=8,
    parity=serial.PARITY_NONE,
    stopbits=1,
    timeout=2
)

command = bytes.fromhex(
    "EB 90 01 04 11 C0 05 02 DD"
)

print("TX:", command.hex(" "))

ser.reset_input_buffer()
ser.write(command)
ser.flush()

response = ser.read(10)

print("RX length:", len(response))
print("RX:", response.hex(" "))

ser.close()