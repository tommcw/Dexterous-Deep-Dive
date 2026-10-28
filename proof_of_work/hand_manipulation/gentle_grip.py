import time

from inspire_rh56dftp import InspireHand, registers


HAND_IP = "192.168.123.210"

# How quickly the target position closes.
# Smaller = slower and gentler.
STEP = 5

# Time between position updates.
UPDATE_PERIOD = 0.10       # 10 Hz

# Maximum raw force value before that finger stops closing.
FORCE_THRESHOLD = 250

# Maximum amount of time allowed for the grip attempt.
MAX_GRIP_TIME = 14.0


# DOF order:
# 0 = pinky
# 1 = ring
# 2 = middle
# 3 = index
# 4 = thumb bend
# 5 = thumb rotation

finger_names = [
    "Pinky", 
    "Ring",
    "Middle",
    "Index",
    "Thumb",
    "Thumb rotation",
]

FINGERS = [0, 1, 2, 3, 4]


def signed_16(value):
    """Convert unsigned Modbus 16-bit value to signed integer."""
    if value >= 32768:
        return value - 65536
    return value


hand = InspireHand(
    ip=HAND_IP,
    default_speed=100
)

try:

    # Start fully open.
    position = [1000, 1000, 1000, 1000, 1000, 0]

    hand.send_raw(position)

    print("Hand opened.")
    print("Place the object in the hand.")
    input("Press ENTER to begin closing...")

    # Which fingers have already contacted the object?
    stopped = {
        finger: False
        for finger in FINGERS
    }

    start_time = time.monotonic()

    while True:

        # --------------------------------------------------
        # Read forces
        # --------------------------------------------------

        raw_forces = hand.read_holding(
            registers.FORCE_ACT,
            6
        )

        forces = [
            signed_16(value)
            for value in raw_forces
        ]

        # --------------------------------------------------
        # Print sensor state
        # --------------------------------------------------

        print(
            "\r"
            f"Pinky:{forces[0]:4d}  "
            f"Ring:{forces[1]:4d}  "
            f"Middle:{forces[2]:4d}  "
            f"Index:{forces[3]:4d}",
            f"Thumb:{forces[4]:4d}",
            end=""
        )

        # --------------------------------------------------
        # Check force thresholds
        # --------------------------------------------------

        for finger in FINGERS:

            if not stopped[finger]:

                if forces[finger] >= FORCE_THRESHOLD:

                    stopped[finger] = True

                    print(
                        f"\nFinger {finger_names[finger]} reached force threshold "
                        f"({forces[finger]})."
                    )

        # --------------------------------------------------
        # Stop when all four fingers have contacted object
        # --------------------------------------------------

        if all(stopped.values()):

            print("\nAll fingers reached force threshold.")
            break

        # --------------------------------------------------
        # Safety timeout
        # --------------------------------------------------

        if time.monotonic() - start_time > MAX_GRIP_TIME:

            print("\nMaximum grip time reached.")
            break

        # --------------------------------------------------
        # Close fingers that have NOT reached threshold
        # --------------------------------------------------

        for finger in FINGERS:

            if not stopped[finger]:

                position[finger] -= STEP

                # Never command below zero.
                position[finger] = max(
                    0,
                    position[finger]
                )

        # --------------------------------------------------
        # Send new target
        # --------------------------------------------------

        hand.send_raw(position)

        time.sleep(UPDATE_PERIOD)

finally:

    # Stop further closing.
    # Keep the current position.
    print("\nGrip complete.")

    hand.close()
