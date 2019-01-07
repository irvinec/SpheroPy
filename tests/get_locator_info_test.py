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

    print('LocatorInfo:')
    print('X Pos: {}'.format(locator_info.pos_x))
    print('Y Pos: {}'.format(locator_info.pos_y))
    print('X Velocity: {}'.format(locator_info.vel_x))
    print('Y Velocity: {}'.format(locator_info.vel_y))
    print('Speed Over Ground: {}'.format(locator_info.speed_over_ground))

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())