# ping_test.py

import asyncio
import sphero

from bluetooth_interface import BluetoothInterface

async def main():
    socket = BluetoothInterface()
    socket.connect()
    my_sphero = sphero.Sphero(socket)

    # Ping the sphero and wait for a response.
    # Do this a few times to validate
    # sequence_number handling.
    await my_sphero.ping()
    await my_sphero.ping()
    await my_sphero.ping()

    # Ping the sphero but don't request/wait for a response
    await my_sphero.ping(wait_for_response=False)

    # Don't reset the inactivity timeout
    await my_sphero.ping(wait_for_response=False, reset_inactivity_timeout=False)

if __name__ == "__main__":
    asyncio.run(main())
