from inspire_rh56dftp import InspireHand

HAND_IP = "192.168.123.210"

position = [1000, 1000, 1000, 1000, 1000, 0]

hand = InspireHand(
    ip=HAND_IP,
    default_speed=300
)

FINGERS = {
    "pinky": 0,
    "ring": 1,
    "middle": 2,
    "index": 3,
    "thumb_bend": 4,
    "thumb_rotation": 5,
}
try:
    success = hand.send_raw(position)
    print("Sent:", success)

finally:
    hand.close()