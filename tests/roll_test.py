# ping_test.py

import asyncio
import sched
import time
import sphero

from bluetooth_interface import BluetoothInterface

async def main():
    socket = BluetoothInterface()
    socket.connect()
    my_sphero = sphero.Sphero(socket)

    await my_sphero.roll(127, 0)
    time.sleep(0.5)
    await my_sphero.roll(127, 90)
    time.sleep(0.5)
    await my_sphero.roll(127, 180)
    time.sleep(0.5)
    await my_sphero.roll(127, 270)
    time.sleep(0.5)

    await my_sphero.roll(16, 0)
    time.sleep(0.5)
    await my_sphero.roll(255, 180)
    time.sleep(0.5)
    await my_sphero.roll(0, 0)


if __name__ == "__main__":
    asyncio.run(main())
