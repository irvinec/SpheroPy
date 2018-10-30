"""
"""

import asyncio
import time
import sphero

from bluetooth_interface import BluetoothInterface

async def main():
    socket = BluetoothInterface()
    socket.connect()
    my_sphero = sphero.Sphero(socket)

    original_auto_reconnect_setting = await my_sphero.get_auto_reconnect()

    print("Original Auto Reconnect Setting:")
    print("Is Enabled: {}".format(original_auto_reconnect_setting.is_enabled))
    print("Seconds After Boot: {}".format(original_auto_reconnect_setting.seconds_after_boot))
    print("")

    print("Trying to enable auto reconnect with:")
    print("Is Enabled: True")
    print("Seconds After Boot: 20")
    await my_sphero.set_auto_reconnect(True, 20)
    print("Completed set auto reconnect.")
    print("")

    new_auto_reconnect_info = await my_sphero.get_auto_reconnect()

    print("New Auto Reconnect Setting:")
    print("Is Enabled: {}".format(new_auto_reconnect_info.is_enabled))
    print("Seconds After Boot: {}".format(new_auto_reconnect_info.seconds_after_boot))
    print("")

    # Restore the original setting
    await my_sphero.set_auto_reconnect(
        original_auto_reconnect_setting.is_enabled,
        original_auto_reconnect_setting.seconds_after_boot)


if __name__ == "__main__":
    asyncio.run(main())