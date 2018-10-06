# commands.py

import sphero.packets

DEVICE_ID_CORE = 0x00
DEVICE_ID_SPHERO = 0x02

COMMAND_ID_PING = 0x01

def create_ping_command(
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    return sphero.packets.ClientCommandPacket(
        device_id=DEVICE_ID_CORE,
        command_id=COMMAND_ID_PING,
        sequence_number=sequence_number,
        data=[],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)
