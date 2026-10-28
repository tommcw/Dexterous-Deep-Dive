# Attempt to get a serial response from robotic hand.
# Author: Thomas McWatters
# Ask every robotic hand on the bus what its system voltage is set to.
# Because correct hand id was not known for sure, ask hand 1, 2, etc.
# There was a response but reply contents were unexpected.

from proof_of_work.hand_communication_serial.voltagerequest import get_hand_voltage
import time

for n in range(1, 255):
    print(n)
    response = get_hand_voltage(hand_id=n)

    if response:
        print(f"Hand ID {n}: {response.hex(' ')}")
    time.sleep(0.5)