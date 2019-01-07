"""
"""

import asyncio
import spheropy

from bluetooth_interface import BluetoothInterface

async def main():
    socket = BluetoothInterface()
    socket.connect()
    my_sphero = spheropy.Sphero(socket)

    # Ping the sphero and wait for a response.
    # Do this a few times to validate
    # sequence_number handling.
    await my_sphero.ping()
    await my_sphero.ping()
    await my_sphero.ping()

    # Ping the Sphero a few times,
    # but don't wait until all have been started.
    await asyncio.gather(
        my_sphero.ping(),
        my_sphero.ping(),
        my_sphero.ping()
    )

    # Ping the sphero but don't request/wait for a response
    await my_sphero.ping(wait_for_response=False)

    # Don't reset the inactivity timeout
    await my_sphero.ping(wait_for_response=False, reset_inactivity_timeout=False)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
