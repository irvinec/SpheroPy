"""
"""

import asyncio
from tests.test_utils import parse_args
import spheropy

async def main():
    script_args = parse_args()
    sphero = spheropy.Sphero()
    await sphero.connect(num_retry_attempts=3, use_ble=script_args.use_ble)

    original_auto_reconnect_setting = await sphero.get_auto_reconnect()

    print("Original Auto Reconnect Setting:")
    print("Is Enabled: {}".format(original_auto_reconnect_setting.is_enabled))
    print("Seconds After Boot: {}".format(original_auto_reconnect_setting.seconds_after_boot))
    print("")

    print("Trying to enable auto reconnect with:")
    print("Is Enabled: True")
    print("Seconds After Boot: 20")
    await sphero.set_auto_reconnect(True, 20)
    print("Completed set auto reconnect.")
    print("")

    new_auto_reconnect_info = await sphero.get_auto_reconnect()

    print("New Auto Reconnect Setting:")
    print("Is Enabled: {}".format(new_auto_reconnect_info.is_enabled))
    print("Seconds After Boot: {}".format(new_auto_reconnect_info.seconds_after_boot))
    print("")

    # Restore the original setting
    await sphero.set_auto_reconnect(
        original_auto_reconnect_setting.is_enabled,
        original_auto_reconnect_setting.seconds_after_boot)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())