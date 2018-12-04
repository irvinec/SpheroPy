"""
"""

import asyncio
import time
import spheropy

from bluetooth_interface import BluetoothInterface

async def main():
    socket = BluetoothInterface()
    socket.connect()
    my_sphero = spheropy.Sphero(socket)

    await my_sphero.set_power_notification(True)

    power_state_change_detected = False

    def handle_power_state_change(power_state):
        nonlocal power_state_change_detected
        power_state_change_detected = True
        print("Power State Changed To: {}".format(power_state))

    my_sphero.on_power_state_change.append(handle_power_state_change)

    await my_sphero.set_rgb_led(green=0xFF)
    for _ in range(3):
        await my_sphero.ping()
        await asyncio.sleep(10)
        if power_state_change_detected:
            break

    if not power_state_change_detected:
        print("FAIL: No Power State Change Detected")

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
