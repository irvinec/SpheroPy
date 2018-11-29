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

    await my_sphero.set_heading(0)
    await my_sphero.set_heading(90)
    await my_sphero.set_heading(180)
    await my_sphero.set_heading(0)

if __name__ == "__main__":
    asyncio.run(main())