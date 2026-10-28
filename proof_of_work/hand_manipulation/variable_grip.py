import time

from inspire_rh56dftp import InspireHand, registers
import numpy as np 
import matplotlib.pyplot as plt


HAND_IP = "192.168.123.210"

STEP = 7 # How quickly the target position closes. (Smaller = slower and gentler.)

UPDATE_PERIOD = 0.10 # Time between position updates. 10 Hz

MAX_GRIP_TIME = 14.0 # Maximum amount of time allowed for the grip attempt.


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

FINGERS = [ 3, 4] # fingers we are working with 

def signed_16(value):
    """Convert unsigned Modbus 16-bit value to signed integer."""
    if value >= 32768:
        return value - 65536
    return value

hand = InspireHand(
    ip=HAND_IP,
    default_speed=1000
)

try:

    # Start fully open.
    position = [1000, 1000, 1000, 1000, 1000, 0]

    # create dictionary of lists 
    #save = defaultdict(list)
    save = {}

    hand.send_raw(position)

    print("Hand opened.")
    print("Place the object in the hand.")

    user_force = int(input("Select Force:"))

    input("Press ENTER to begin closing...")

    # Which fingers have already contacted the object?
    stopped = {
        finger: False
        for finger in FINGERS
    }

    start_time = time.monotonic()


    save = {"time":[],"index_force":[],"thumb_force":[],"index_position":[],"thumb_position":[]}
    while True:

        if user_force == "q":
                    break

        if not 30 <= user_force <=2000:
            print("Position must be between 0 and 2000 \n set to default value of 250")
            user_force = 250

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

        # print(
        #     "\r"
        #     f"Index:{forces[3]:4d}"
        #     f"Thumb:{forces[4]:4d}",
        #     end="  "
        # )

        # --------------------------------------------------
        # Save Sensor state every quater second
        # --------------------------------------------------

        
        
        #if time.monotonic() % 0.1 == 0:
        #print(f"Time:{time.monotonic() - start_time} Index force: {forces[3]} Thumb Force: {forces[4]} Index angle: {position[3]} Thumb angle: {position[4]}")
        save["time"]. append(time.monotonic()-start_time)
        save["index_force"].append(forces[3])
        save["thumb_force"].append(forces[4])
        save['index_position'].append(position[3])
        save["thumb_position"].append(position[4])

        # --------------------------------------------------
        # Check force thresholds
        # --------------------------------------------------

        for finger in FINGERS:
            if not stopped[finger]:
                if forces[finger] >= user_force:
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

    # plt.plot(save['time'],save["index_force"], 'bo')
    # plt.plot(save['time'],save["thumb_force"], 'go')
    # plt.plot(save['time'],save["index_position"], 'ro')
    # plt.plot(save['time'],save["index_position"], 'yo')
    # plt.title("Forces and positions of fingers")
    # plt.xlabel("Time")
    # plt.ylabel("position and force applied")
    # #plt.legend()
    # plt.grid(True)
    # plt.show()

