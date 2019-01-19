"""
"""

import asyncio
from tests.test_utils import parse_args
import spheropy

async def main():
    script_args = parse_args()
    sphero = spheropy.Sphero()
    await sphero.connect(num_retry_attempts=3, use_ble=script_args.use_ble)

    original_bluetooth_info = await sphero.get_bluetooth_info()

    print("Original Bluetooth Info:")
    print("Name: {}".format(original_bluetooth_info.name))
    print("Bluetooth Address: {}".format(original_bluetooth_info.bluetooth_address))
    print("ID Colors: {}".format(original_bluetooth_info.id_colors))
    print("")

    print("Trying to set device name to SwervySwerve.")
    await sphero.set_device_name("SwervySwerve")
    print("Completed set device name.")
    print("")

    new_bluetooth_info = await sphero.get_bluetooth_info()

    print("New Bluetooth Info:")
    print("Name: {}".format(new_bluetooth_info.name))
    print("Bluetooth Address: {}".format(new_bluetooth_info.bluetooth_address))
    print("ID Colors: {}".format(new_bluetooth_info.id_colors))

    # Restore the original setting
    await sphero.set_device_name(original_bluetooth_info.name)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())