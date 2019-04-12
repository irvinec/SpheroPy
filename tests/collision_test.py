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

    await sphero.configure_collision_detection(
        True,
        45, 110,
        45, 110,
        20)

    collision_detected = False

    def handle_collision(collision_data):
        nonlocal collision_detected
        collision_detected = True
        event_loop = asyncio.new_event_loop()
        event_loop.run_until_complete(sphero.roll(0, 0))
        event_loop.run_until_complete(sphero.set_rgb_led(red=0xFF))

        print("Collision Data:")
        print("X Impact: {}".format(collision_data.x_impact))
        print("Y Impact: {}".format(collision_data.y_impact))
        print("Z Impact: {}".format(collision_data.z_impact))
        print("Axis: {}".format(collision_data.axis))
        print("X Magnitude: {}".format(collision_data.x_magnitude))
        print("Y Magnitude: {}".format(collision_data.y_magnitude))
        print("Speed: {}".format(collision_data.speed))
        print("Timestamp: {}".format(collision_data.timestamp))
        time.sleep(4)

    sphero.on_collision.append(handle_collision)

    await sphero.set_rgb_led(green=0xFF)
    await sphero.roll(127, 0)
    await asyncio.sleep(10)
    if not collision_detected:
        print("FAIL: collision not detected.")
        await sphero.roll(0, 0)
        await sphero.set_rgb_led(blue=0xFF)
        await asyncio.sleep(4)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
