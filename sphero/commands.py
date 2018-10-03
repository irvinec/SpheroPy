# commands.py

import sphero.packets

DEVICE_ID_CORE = 0x00
DEVICE_ID_SPHERO = 0x02

COMMAND_ID_PING = 0x01

def create_ping_command(sequence_number=0x00, wait_for_response=True, reset_inactivity_timeout=False):
    """
    """
    return sphero.packets.ClientCommandPacket(
        DEVICE_ID_CORE,
        COMMAND_ID_PING,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout)