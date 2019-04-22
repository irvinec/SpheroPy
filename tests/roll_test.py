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

    await sphero.roll(127, 0, wait_for_response=False)
    time.sleep(0.5)
    await sphero.roll(127, 90)
    time.sleep(0.5)
    await sphero.roll(127, 180)
    time.sleep(0.5)
    await sphero.roll(127, 270)
    time.sleep(0.5)

    await sphero.roll(16, 0)
    time.sleep(0.5)
    await sphero.roll(255, 180)
    time.sleep(0.5)
    await sphero.roll(0, 0)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
