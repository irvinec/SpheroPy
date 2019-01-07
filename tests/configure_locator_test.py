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

    locator_info = await my_sphero.get_locator_info()

    print('Original LocatorInfo:')
    print('X Pos: {}'.format(locator_info.pos_x))
    print('Y Pos: {}'.format(locator_info.pos_y))
    print('X Velocity: {}'.format(locator_info.vel_x))
    print('Y Velocity: {}'.format(locator_info.vel_y))
    print('Speed Over Ground: {}'.format(locator_info.speed_over_ground))

    print('Simulating aiming the Sphero')
    # Turn on the aiming LED
    await my_sphero.set_back_led(0xFF)
    # Turn off auto-correction for yaw tare
    await my_sphero.configure_locator(False)
    time.sleep(1)
    # Adjust the heading by 90 degrees
    await my_sphero.set_heading(90)
    time.sleep(1)
    # Turn on auto-correction for yay tare
    await my_sphero.configure_locator(True)
    await my_sphero.set_back_led(0)

    locator_info = await my_sphero.get_locator_info()

    print('New LocatorInfo:')
    print('X Pos: {}'.format(locator_info.pos_x))
    print('Y Pos: {}'.format(locator_info.pos_y))
    print('X Velocity: {}'.format(locator_info.vel_x))
    print('Y Velocity: {}'.format(locator_info.vel_y))
    print('Speed Over Ground: {}'.format(locator_info.speed_over_ground))

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())