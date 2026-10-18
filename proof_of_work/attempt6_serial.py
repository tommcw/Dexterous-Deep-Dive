# Attempt to move index finger of robotic hand via serial. #6
# Author: Thomas McWatters
#

import serial

def checksum(data):
    return sum(data[2:]) & 0xFF # only last 8bits

def set_index_finger(hand_id, angle):
    # ANGLE_SET(3) = address 1492 = 0x05D4
    address = 1492

    # Convert the signed 16-bit value to two bytes,
    # low byte first, high byte second.
    value = angle.to_bytes(2, byteorder="little", signed=True)

    packet = bytearray([
        0xEB,             # packet header
        0x90,             # packet header
        hand_id,          # hand ID
        0x05,             # frame data length: 2 + 3
        0x12,             # write-register command
        address & 0xFF,   # Address_L
        address >> 8,     # Address_H
    ])

    packet.extend(value) # append value for angle

    # Checksum is the low byte of the sum of
    # everything before the checksum.
    packet.append(checksum(packet))

    return packet


ser = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=115200,
    bytesize=8,
    parity=serial.PARITY_NONE,
    stopbits=1,
    timeout=1
)

command = set_index_finger(hand_id=1, angle=500) # angle is 0-1000

print("Sending:", command.hex(" "))

ser.write(command)

response = ser.read(9)

print("Response:", response.hex(" "))

ser.close()