import time
from datetime import datetime

from inspire_rh56dftp import InspireHand, registers


HAND_IP = "192.168.123.210"
UPDATE_HZ = 10


FINGERS = [
    "Pinky",
    "Ring",
    "Middle",
    "Index",
    "Thumb bend",
    "Thumb rotation",
]

# Issue with a value slution
def signed_16(value):
    """Convert an unsigned 16-bit register to a signed integer."""
    if value >= 32768:
        return value - 65536
    return value


hand = InspireHand(
    ip=HAND_IP
)

try:
    while True:
        start = time.perf_counter()

        # Read actual joint positions
        angles = hand.read_holding(
            registers.ANGLE_ACT,
            6
        )

        # Read actual forces
        raw_forces = hand.read_holding(
            registers.FORCE_ACT,
            6
        )

        forces = [signed_16(v) for v in raw_forces]

        # Clear terminal and move cursor to top
        print("\033[2J\033[H", end="")

        print("RH56DFTP LIVE SENSOR MONITOR")
        print("=" * 50)
        print(f"Hand: {HAND_IP}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print()

        print(f"{'DOF':<18} {'Angle':>8} {'Force':>10}")
        print("-" * 40)

        for name, angle, force in zip(FINGERS, angles, forces):
            print(f"{name:<18} {angle:>8} {force:>10}")

        print()
        print("Press Ctrl+C to stop.")

        # Maintain approximately UPDATE_HZ
        elapsed = time.perf_counter() - start
        delay = (1 / UPDATE_HZ) - elapsed

        if delay > 0:
            time.sleep(delay)

except KeyboardInterrupt:
    print("\nStopping monitor...")

finally:
    hand.close()
    print("Connection closed.")