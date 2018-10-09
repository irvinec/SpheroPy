# commands.py

import sphero.packets

_DEVICE_ID_CORE = 0x00
_DEVICE_ID_SPHERO = 0x02

_COMMAND_ID_PING = 0x01
_COMMAND_ID_ROLL = 0x30

def create_ping_command(
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    return sphero.packets.ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_PING,
        sequence_number=sequence_number,
        data=[],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)


def create_roll_command(
        speed,
        heading_in_degrees,
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    if heading_in_degrees < 0 or heading_in_degrees > 359:
        raise ValueError(
            "heading_in_degrees must be in the range [0, 359]. heading was {}"
            .format(heading_in_degrees))

    return sphero.packets.ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_ROLL,
        sequence_number=sequence_number,
        data=[
            speed,
            _get_most_significant_byte(heading_in_degrees),
            _get_least_significant_byte(heading_in_degrees),
            speed,  # This is the STATE value that was originally used in CES firmware.
        ],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)


def _get_most_significant_byte(value):
    """
    """

    return value >> 8 & 0xFF

def _get_least_significant_byte(value):
    """
    """

    return value & 0xFF