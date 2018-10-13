"""
"""

import asyncio
import time
import sphero

from bluetooth_interface import BluetoothInterface

async def main():
    socket = BluetoothInterface()
    socket.connect()
    my_sphero = sphero.Sphero(socket)

    await my_sphero.configure_collision_detection(
        True,
        45, 110,
        45, 110,
        20)

    collision_detected = False

    def handle_collision(collision_data):
        nonlocal collision_detected
        collision_detected = True
        event_loop = asyncio.new_event_loop()
        event_loop.run_until_complete(my_sphero.roll(0, 0))
        event_loop.run_until_complete(my_sphero.set_rgb_led(red=0xFF))
        time.sleep(4)

    my_sphero.on_collision.append(handle_collision)

    await my_sphero.set_rgb_led(green=0xFF)
    await my_sphero.roll(127, 0)
    await asyncio.sleep(10)
    if not collision_detected:
        print("FAIL: collision not detected")
        await my_sphero.roll(0, 0)
        await my_sphero.set_rgb_led(blue=0xFF)
        await asyncio.sleep(4)


if __name__ == "__main__":
    asyncio.run(main())
