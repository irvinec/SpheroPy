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

    original_bluetooth_info = await my_sphero.get_bluetooth_info()

    print("Original Bluetooth Info:")
    print("Name: {}".format(original_bluetooth_info.name))
    print("Bluetooth Address: {}".format(original_bluetooth_info.bluetooth_address))
    print("ID Colors: {}".format(original_bluetooth_info.id_colors))
    print("")

    print("Trying to set device name to SwervySwerve.")
    await my_sphero.set_device_name("SwervySwerve")
    print("Completed set device name.")
    print("")

    new_bluetooth_info = await my_sphero.get_bluetooth_info()

    print("New Bluetooth Info:")
    print("Name: {}".format(new_bluetooth_info.name))
    print("Bluetooth Address: {}".format(new_bluetooth_info.bluetooth_address))
    print("ID Colors: {}".format(new_bluetooth_info.id_colors))

    # Restore the original setting
    await my_sphero.set_device_name(original_bluetooth_info.name)


if __name__ == "__main__":
    asyncio.run(main())