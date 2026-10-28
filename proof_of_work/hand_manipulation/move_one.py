import sys

print("PYTHON EXECUTABLE:", sys.executable)
print("PYTHON VERSION:", sys.version)

import inspire_rh56dftp
print("INSPIRE PACKAGE:", inspire_rh56dftp.__file__)

from inspire_rh56dftp import InspireHand

HAND_IP = "192.168.123.210"

FINGERS = {
    "pinky": 0,
    "ring": 1,
    "middle": 2,
    "index": 3,
    "thumb_bend": 4,
    "thumb_rotation": 5,
}

position = [1000, 1000, 1000, 1000, 1000, 1000]

hand = InspireHand(
    ip=HAND_IP,
    default_speed=300
)

try:
    while True:
        print("\nCurrent target:", position)
        print("Available:", ", ".join(FINGERS.keys()))

        finger = input("Finger (or 'q' to quit): ").lower()

        if finger == "q":
            break

        if finger not in FINGERS:
            print("Unknown finger")
            continue

        value = int(input("Position 0-1000: "))

        if not 0 <= value <= 1000:
            print("Position must be between 0 and 1000")
            continue

        index = FINGERS[finger]
        position[index] = value

        success = hand.send_raw(position)

        print("Sent:", success)

finally:
    hand.close()
