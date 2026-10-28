from inspire_rh56dftp import InspireHand, registers

HAND_IP = "192.168.123.210"

hand = InspireHand(
    ip=HAND_IP
)

try:
    angles = hand.read_holding(registers.ANGLE_ACT, 6)
    forces = hand.read_holding(registers.FORCE_ACT, 6)

    print("Angles:", angles)
    print("Forces:", forces)

finally:
    hand.close()
