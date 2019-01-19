"""
"""

import asyncio
import spheropy
from tests.test_utils import parse_args

async def main():
    script_args = parse_args()
    sphero = spheropy.Sphero()
    await sphero.connect(num_retry_attempts=3, use_ble=script_args.use_ble)

    # Ping the sphero and wait for a response.
    # Do this a few times to validate
    # sequence_number handling.
    await sphero.ping()
    await sphero.ping()
    await sphero.ping()

    # Ping the Sphero a few times,
    # but don't wait until all have been started.
    await asyncio.gather(
        sphero.ping(),
        sphero.ping(),
        sphero.ping()
    )

    # Ping the sphero but don't request/wait for a response
    await sphero.ping(wait_for_response=False)

    # Don't reset the inactivity timeout
    await sphero.ping(wait_for_response=False, reset_inactivity_timeout=False)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
