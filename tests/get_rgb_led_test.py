"""
"""

import asyncio
import time
from test_utils import parse_args
import spheropy


async def main():
    script_args = parse_args()
    sphero = spheropy.Sphero()
    await sphero.connect(num_retry_attempts=3, use_ble=script_args.use_ble)

    original_user_led_color = await sphero.get_rgb_led()

    await sphero.set_rgb_led(red=0xFF, save_as_user_led_color=True)
    time.sleep(2)
    user_led_color = await sphero.get_rgb_led()
    if user_led_color != [0xFF, 0x00, 0x00]:
        print("FAIL: User LED color is not red=0xFF, green=0x00, blue=0x00 as expected. Actual = {}"
              .format(user_led_color))

    await sphero.set_rgb_led(green=0xFF, save_as_user_led_color=True)
    time.sleep(2)
    user_led_color = await sphero.get_rgb_led()
    if user_led_color != [0x00, 0xFF, 0x00]:
        print("FAIL: User LED color is not red=0x00, green=0xFF, blue=0x00 as expected. Actual = {}"
              .format(user_led_color))

    await sphero.set_rgb_led(blue=0xFF, save_as_user_led_color=True)
    time.sleep(2)
    user_led_color = await sphero.get_rgb_led()
    if user_led_color != [0x00, 0x00, 0xFF]:
        print("FAIL: User LED color is not red=0x00, green=0x00, blue=0xFF as expected. Actual = {}"
              .format(user_led_color))

    await sphero.set_rgb_led(red=0xFF, blue=0xFF, save_as_user_led_color=True)
    time.sleep(2)
    user_led_color = await sphero.get_rgb_led()
    if user_led_color != [0xFF, 0x00, 0xFF]:
        print("FAIL: User LED color is not red=0xFF, green=0x00, blue=0xFF as expected. Actual = {}"
              .format(user_led_color))

    # Restore the original setting
    await sphero.set_rgb_led(
        original_user_led_color[0],
        original_user_led_color[1],
        original_user_led_color[2],
        save_as_user_led_color=True)
    time.sleep(2)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
