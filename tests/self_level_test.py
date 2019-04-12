import asyncio
import time
from tests.test_utils import parse_args
import spheropy


async def main():
    script_args = parse_args()
    sphero = spheropy.Sphero()
    await sphero.connect(num_retry_attempts=3, use_ble=script_args.use_ble)

    self_level_result_received = False

    def handle_complete(result):
        nonlocal self_level_result_received
        self_level_result_received = True
        print(f'Result: {result}')

    sphero.on_self_level_complete.append(handle_complete)

    await sphero.self_level()
    await asyncio.sleep(5)
    if not self_level_result_received:
        print("FAIL: Result not received.")


if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
