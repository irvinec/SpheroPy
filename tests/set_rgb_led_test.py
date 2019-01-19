"""
"""

import asyncio
import time
import spheropy
from tests.test_utils import parse_args

async def main():
    script_args = parse_args()
    sphero = spheropy.Sphero()
    await sphero.connect(num_retry_attempts=3, use_ble=script_args.use_ble)

    await sphero.set_rgb_led(red=0xFF)
    time.sleep(2)
    await sphero.set_rgb_led(green=0xFF)
    time.sleep(2)
    await sphero.set_rgb_led(blue=0xFF)
    time.sleep(2)
    await sphero.set_rgb_led(red=0xFF, blue=0xFF)
    time.sleep(2)
    await sphero.set_rgb_led(0xFF, 0xFF, 0xFF)
    time.sleep(2)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())