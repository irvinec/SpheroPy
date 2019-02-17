"""
"""
import asyncio
import time
from spheropy import Sphero
from tests.test_utils import parse_args

async def main():
    script_args = parse_args()
    sphero = Sphero()
    await sphero.connect(num_retry_attempts=3, use_ble=script_args.use_ble)
    await test_set_rgb_led(sphero)
    await test_ping(sphero)

async def test_set_rgb_led(sphero):
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

async def test_ping(sphero):
    sphero.ping()

if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())