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

    locator_info = await sphero.get_locator_info()

    print('LocatorInfo:')
    print('X Pos: {}'.format(locator_info.pos_x))
    print('Y Pos: {}'.format(locator_info.pos_y))
    print('X Velocity: {}'.format(locator_info.vel_x))
    print('Y Velocity: {}'.format(locator_info.vel_y))
    print('Speed Over Ground: {}'.format(locator_info.speed_over_ground))

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())