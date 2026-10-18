# Request the system voltage of a robotic hand.
# Author: Thomas McWatters
# This function will be used to poll every hand from 1 to n
# for their system voltage.
# Aim: to identify corresponding hand IDs by checking them all.

import serial

def checksum(data):
    return sum(data[2:]) & 0xFF  # only last 8 bits


def get_hand_voltage(hand_id):
    # VLTAGE system voltage register
    # address 1472 = 0x05C0
    # 1 short = 2 bytes
    address = 1472

    packet = bytearray([
        0xEB,             # packet header
        0x90,             # packet header
        hand_id,          # hand ID
        0x04,             # frame data length: 4
        0x11,             # read-register command
        address & 0xFF,   # Address_L
        address >> 8,     # Address_H
        0x02              # register length: 2 bytes
    ])

    packet.append(checksum(packet))

    ser = serial.Serial(
        port="/dev/ttyUSB0",
        baudrate=115200,
        bytesize=8,
        parity=serial.PARITY_NONE,
        stopbits=1,
        timeout=0.2
    )

    ser.write(packet)

    response = ser.read(10)

    ser.close()

    if not response:
        return None

    return response