"""
"""

import asyncio
import spheropy

from bluetooth_interface import BluetoothInterface

async def main():
    socket = BluetoothInterface()
    socket.connect()
    my_sphero = spheropy.Sphero(socket)

    power_state = await my_sphero.get_power_state()

    print("Power State:")
    print("Record Version: {}".format(power_state.record_version))

    battery_state_string = "Unknown"
    if power_state.battery_state is spheropy.Sphero.BATTERY_STATE_CHARGING:
        battery_state_string = "Charging"
    elif power_state.battery_state is spheropy.Sphero.BATTERY_STATE_OK:
        battery_state_string = "OK"
    elif power_state.battery_state is spheropy.Sphero.BATTERY_STATE_LOW:
        battery_state_string = "Low"
    elif power_state.battery_state is spheropy.Sphero.BATTERY_STATE_CRITICAL:
        battery_state_string = "Critical"

    print("Battery State: {}".format(battery_state_string))
    print("Battery Voltage: {}".format(power_state.battery_voltage))
    print("Lifetime Number of Recharges: {}".format(power_state.total_number_of_recharges))
    print("Seconds Since Last Recharge: {}".format(power_state.seconds_awake_since_last_recharge))


if __name__ == "__main__":
    asyncio.run(main())
