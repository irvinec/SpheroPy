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

    # Ping the sphero and wait for a response.
    # Do this a few times to validate
    # sequence_number handling.
    await my_sphero.set_rgb_led(red=0xFF)
    time.sleep(2)
    await my_sphero.set_rgb_led(green=0xFF)
    time.sleep(2)
    await my_sphero.set_rgb_led(blue=0xFF)
    time.sleep(2)
    await my_sphero.set_rgb_led(red=0xFF, blue=0xFF)
    time.sleep(2)
    await my_sphero.set_rgb_led(0xFF, 0xFF, 0xFF)
    time.sleep(2)


if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())