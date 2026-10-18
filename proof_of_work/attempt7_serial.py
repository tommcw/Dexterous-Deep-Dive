# Send serial communication to robotic hand, ordering the thumb to move. #7
# Author: Thomas McWatters
# Construct a serial frame for generic finger and angle.

THUMB_ANGLE_SET = 1494 # register value
READ_REGISTER = 0x11
WRITE_REGISTER = 0x12
HAND_ID = 0x05

def move_thing(finger_register, angle):
    packet = bytearray([])
    packet.append(HAND_ID)
    packet.append(5) # {register length + 3} ; 2 + 3 = 5
    packet.append(WRITE_REGISTER)
    high_register_bytes = (finger_register >> 8) & 0xFF
    low_register_bytes = finger_register & 0xFF
    packet.append(low_register_bytes)
    packet.append(high_register_bytes)
    packet.append(angle & 0xFF) # the data payload
    packet.append((angle >> 8) & 0xFF) # in little endian
    packet.append(sum(packet) & 0xFF)
    print('checksum is: ', (sum(packet) & 0xFF), " = ", hex(sum(packet) & 0xFF))
    packet = bytearray([0xEB, 0x90]) + packet
    print(packet.hex(" "))
    print("/""/")

move_thing(THUMB_ANGLE_SET, 100)

# Correct way to ask:
# Header + Hand ID 5 + Length of the frame data is 4,
# -   0x11 is the flag to READ A REGISTER ; 0x12 is to WRITE A REGISTER
#      NB: when writing to a register the length of the frame needs to
#          be Register Length + 3 and the data goes before the checksum
# -   then Lower order 8 bits of register
# -   the Upper part of register
# -   register length is 2.

# Register lengths:
# 1000 HAND_ID  1 byte
#1032 DEFAULT_SPEED_SET(m) 12 bytes
#1044 DEFAULT_FORCE_SET(m) 12 bytes
#1486 ANGLE_SET(m) 12 bytes
#1494 Individual angle entry 2 bytes
# the larger registers can be written to as a group