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

    await sphero.set_back_led(255)
    time.sleep(2)
    await sphero.set_back_led(0)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())