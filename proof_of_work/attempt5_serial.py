# Attempt to get a serial response from robotic hand. #5
# Author: Thomas McWatters

import serial

def checksum(data):
    return sum(data[2:]) & 0xFF # only last 8bits

def read_force_index_finger(hand_id):
    # FORCE_SET(3) address = 1504-1505 set value of force for index finger
    
    # not sure, check
    #address = 0x060A # the angle for DOF
    address = 0x05E0 # the force set register
    
    packet = bytearray([
        0xEB,             # packet header
        0x90,             # packet header
        hand_id,          # hand ID
        0x04,             # frame data length: 4
        0x11,             # read-register command
        address & 0xFF,   # Address_L
        address >> 8,     # Address_H
    ])

    #packet.extend(value) # append value for angle

    # Checksum is the low byte of the sum of
    # everything after header, before the checksum.
    packet.append(checksum(packet))

    return packet


ser = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=115200,
    bytesize=8,
    parity=serial.PARITY_NONE,
    stopbits=1,
    timeout=2
)

command = read_force_index_finger(hand_id=1)

print("Sending:", command.hex(" "))

ser.write(command)

response = ser.read(9)

print("Response:", response.hex(" "))

ser.close()