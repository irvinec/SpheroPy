# commands.py

import sphero.packets

_DEVICE_ID_CORE = 0x00
_DEVICE_ID_SPHERO = 0x02

_COMMAND_ID_PING = 0x01
_COMMAND_ID_CONFIGURE_COLLISION_DETECTION = 0x12
_COMMAND_ID_SET_RGB_LED = 0x20
_COMMAND_ID_GET_RGB_LED = 0x22
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


def create_configure_collision_detection_command(
        turn_on_collision_detection,
        x_t,
        x_speed,
        y_t,
        y_speed,
        collision_dead_time,
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    return sphero.packets.ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_CONFIGURE_COLLISION_DETECTION,
        sequence_number=sequence_number,
        data=[
            0x01 if turn_on_collision_detection else 0x00,
            x_t, x_speed,
            y_t, y_speed,
            collision_dead_time],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

def create_set_rgb_led_command(
        red=0,
        green=0,
        blue=0,
        save_as_user_led_color=False,
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    if red < 0 or red > 0xFF:
        raise ValueError()

    if green < 0 or green > 0xFF:
        raise ValueError()

    if blue < 0 or blue > 0xFF:
        raise ValueError()

    return sphero.packets.ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_SET_RGB_LED,
        sequence_number=sequence_number,
        data=[red, green, blue, 1 if save_as_user_led_color else 0],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)


def create_get_rgb_led_command(
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    return sphero.packets.ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_GET_RGB_LED,
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