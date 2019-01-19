"""
"""

import asyncio
import time
from tests.test_utils import parse_args
import spheropy

async def main():
    script_args = parse_args()
    sphero = spheropy.Sphero()
    await sphero.connect(num_retry_attempts=3, use_ble=script_args.use_ble)

    await sphero.set_power_notification(True)

    power_state_change_detected = False

    def handle_power_state_change(power_state):
        nonlocal power_state_change_detected
        power_state_change_detected = True
        print("Power State Changed To: {}".format(power_state))

    sphero.on_power_state_change.append(handle_power_state_change)

    await sphero.set_rgb_led(green=0xFF)
    for _ in range(3):
        await sphero.ping()
        await asyncio.sleep(10)
        if power_state_change_detected:
            break

    if not power_state_change_detected:
        print("FAIL: No Power State Change Detected")

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
