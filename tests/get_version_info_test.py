"""
"""

import asyncio
import spheropy

from bluetooth_interface import BluetoothInterface

async def main():
    socket = BluetoothInterface()
    socket.connect()
    my_sphero = spheropy.Sphero(socket)

    version_info = await my_sphero.get_version_info()

    print("Version Info:")
    print("Record Version: {}".format(version_info.record_version))
    print("Model Number: {}".format(version_info.model_number))
    print("Hardware Version: {}".format(version_info.hardware_version))
    print("Main Sphero Application Version: {}"
          .format(version_info.main_sphero_app_version))
    print("Main Sphero Application Revision: {}"
          .format(version_info.main_sphero_app_revision))
    print("Bootloader Version: {}".format(version_info.bootloader_version))
    print("OrbBasic Version: {}".format(version_info.orb_basic_version))
    print("Macro Executive Version: {}"
          .format(version_info.macro_executive_version))
    print("Firmware API Major Version: {}"
          .format(version_info.firmware_api_major_revision))
    print("Firmware API Minor Version: {}"
          .format(version_info.firmware_api_major_revision))


if __name__ == "__main__":
    asyncio.run(main())
