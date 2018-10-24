"""sphero

Interact with Sphero devices.
"""

import threading

class Sphero(object):
    """The main Sphero class that is used for interacting with a Sphero device.
    """

    def __init__(self, bluetooth_interface, default_response_timeout_in_seconds=0.5):
        self.on_collision = []

        self._bluetooth_interface = bluetooth_interface
        self._default_response_timeout_in_seconds = default_response_timeout_in_seconds
        self._command_sequence_number = 0x00
        self._commands_waiting_for_response = {}

        # setup thread for receiving responses
        self._class_destroy_event = threading.Event()
        self._receive_thread = threading.Thread(target=self._receive_thread_run)
        self._receive_thread.daemon = True
        self._receive_thread.start()

    def __del__(self):
        self._class_destroy_event.set()

    async def ping(
            self,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Sends ping to the Sphero.

        The Ping command is used to verify both a solid data link with the client
        and that Sphero is awake and dispatching commands.

        Args:
            wait_for_response (bool, True):
                If True, will wait for a response from the Sphero
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero object.
        """

        sequence_number = self._get_and_increment_command_sequence_number()
        ping_command = _create_ping_command(
            sequence_number,
            wait_for_response,
            reset_inactivity_timeout)

        # Ping has no data so don't in response,
        # so no need tp return anything.
        await self._send_command(
            ping_command,
            sequence_number=sequence_number,
            wait_for_response=wait_for_response,
            response_timeout_in_seconds=response_timeout_in_seconds)

    async def get_version_info(
            self,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Get the version info for various software and hardware components of the Sphero.

        The get version info command returns a whole slew of software and hardware information.
        It’s useful if your Client Application requires a minimum version number
        of some resource within the Sphero.

        Args:
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero object.

        Returns:
            A VersionInfo object that contains the version info for the Sphero.
        """

        sequence_number = self._get_and_increment_command_sequence_number()
        get_version_command = _create_get_version_command(
            sequence_number=sequence_number,
            wait_for_response=True,
            reset_inactivity_timeout=reset_inactivity_timeout)

        response_packet = await self._send_command(
            get_version_command,
            sequence_number=sequence_number,
            wait_for_response=True,
            response_timeout_in_seconds=response_timeout_in_seconds)

        return VersionInfo(response_packet.data)

    async def set_device_name(
            self,
            device_name,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Sets the Sphero's internal name.

        This formerly reprogrammed the Bluetooth module to advertise with a different name,
        but this is no longer the case.
        This assigned name is held internally and returned in get_bluetooth_info.
        Names are clipped at 48 characters in length to support UTF-8 sequences.
        You can send something longer but the extra will be discarded.
        This field defaults to the Bluetooth advertising name.

        Args:
            device_name (string): The desired name of the device/Sphero.
            wait_for_response (bool, True):
                If True, will wait for a response from the Sphero
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero object.
        """

        sequence_number = self._get_and_increment_command_sequence_number()
        set_device_name_command = _create_set_device_name_command(
            device_name=device_name,
            sequence_number=sequence_number,
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            set_device_name_command,
            sequence_number=sequence_number,
            wait_for_response=wait_for_response,
            response_timeout_in_seconds=response_timeout_in_seconds)

    async def get_bluetooth_info(
            self,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """
        """

        sequence_number = self._get_and_increment_command_sequence_number()
        get_bluetooth_info_command = _create_get_bluetooth_info_command(
            sequence_number=sequence_number,
            wait_for_response=True,
            reset_inactivity_timeout=reset_inactivity_timeout)

        response_packet = await self._send_command(
            get_bluetooth_info_command,
            sequence_number=sequence_number,
            wait_for_response=True,
            response_timeout_in_seconds=response_timeout_in_seconds)

        return BluetoothInfo(response_packet.data)

    async def configure_collision_detection(
            self,
            turn_on_collision_detection,
            x_t, x_speed,
            y_t, y_speed,
            collision_dead_time,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """
        """

        sequence_number = self._get_and_increment_command_sequence_number()
        command = _create_configure_collision_detection_command(
            turn_on_collision_detection=turn_on_collision_detection,
            x_t=x_t, x_speed=x_speed,
            y_t=y_t, y_speed=y_speed,
            collision_dead_time=collision_dead_time,
            sequence_number=sequence_number,
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            command,
            sequence_number=sequence_number,
            wait_for_response=wait_for_response,
            response_timeout_in_seconds=response_timeout_in_seconds)

    async def set_rgb_led(
            self,
            red=0,
            green=0,
            blue=0,
            save_as_user_led_color=False,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Sets the main LED RGB color of the Sphero.

        The composite value is stored as the "application LED color"
        and immediately driven to the LED
        (if not overridden by a macro or orbBasic operation).
        If save_as_user_led_color is True, the value is also saved
        as the "user LED color" which persists across power cycles
        and is rendered in the gap between an application connecting
        and sending this command.

        Args:
            red (int):
                The red channel value.
                Valid range is [0, 255].
            green (int):
                The green channel value.
                Valid range is [0, 255].
            blue (int):
                The blue channel value.
                Valid range is [0, 255].
            save_as_user_led_color (bool, False):
                If True, the color will be saved as the user color
                and will persist across power cycles.
            wait_for_response (bool, True):
                If True, will wait for a response from the Sphero
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero object.
        """

        sequence_number = self._get_and_increment_command_sequence_number()
        set_rgb_led_command = _create_set_rgb_led_command(
            red,
            green,
            blue,
            save_as_user_led_color,
            sequence_number,
            wait_for_response,
            reset_inactivity_timeout)

        await self._send_command(
            set_rgb_led_command,
            sequence_number=sequence_number,
            wait_for_response=wait_for_response,
            response_timeout_in_seconds=response_timeout_in_seconds)

    async def get_rgb_led(
            self,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Retrieves the user LED color in RGB.

        The user LED color is the color that persisists across reboots.
        This may or may not be the active RGB LED color.
        The user LED color is set by calling set_rgb_led
        with save_as_user_led_color=True.

        Returns:
            The user LED color as a list in the form
            [red, green, blue].
        """

        sequence_number = self._get_and_increment_command_sequence_number()
        get_rgb_led_command = _create_get_rgb_led_command(
            sequence_number,
            wait_for_response=True, # must wait for the response to get the result.
            reset_inactivity_timeout=reset_inactivity_timeout)

        response_packet = await self._send_command(
            get_rgb_led_command,
            sequence_number=sequence_number,
            wait_for_response=True,
            response_timeout_in_seconds=response_timeout_in_seconds)

        return response_packet.data

    async def roll(
            self,
            speed,
            heading_in_degrees,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Sends the roll command to the Sphero with given heading and speed.

        This commands Sphero to roll along the provided vector
        determined by heading_in_degrees and speed.
        The heading is relative to the last calibrated direction.

        The heading follows the 360 degrees on a circle, relative to the Sphero:
            * 0 is straight ahead.
            * 90 is to the right.
            * 180 is back.
            * 270 is to the left.

        Args:
            speed (int):
                The relative speed with which to roll the Sphero.
                The valid range is [0, 255].
            heading_in_degrees (int):
                The relative heading in degrees.
                The valid range is [0, 359]
            wait_for_response (bool, True):
                If True, will wait for a response from the Sphero
            reset_inactivity_timeout (bool, True):
            If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero object.
        """

        sequence_number = self._get_and_increment_command_sequence_number()
        roll_command = _create_roll_command(
            speed,
            heading_in_degrees,
            sequence_number=sequence_number,
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            roll_command,
            sequence_number=sequence_number,
            wait_for_response=wait_for_response,
            response_timeout_in_seconds=response_timeout_in_seconds)

    # TODO: consider removing some params and getting them from command instead.
    async def _send_command(
            self,
            command,
            sequence_number,
            wait_for_response=True,
            response_timeout_in_seconds=None):
        """
        """

        response_event = threading.Event()
        response_packet = None
        if wait_for_response:
            # define a generic response handler
            # TODO: might need the ability to pass a custom handler
            def handle_response(received_response_packet):
                nonlocal response_packet
                response_packet = received_response_packet
                nonlocal response_event
                response_event.set()

            # Register the response handler for this commands sequence number
            assert sequence_number not in self._commands_waiting_for_response, \
                ("A response handler was already registered for the sequence number {}"
                 .format(sequence_number))
            self._commands_waiting_for_response[sequence_number] = handle_response

        self._bluetooth_interface.send(command.bytes)

        # Wait for the response if necessary
        if wait_for_response:
            if response_timeout_in_seconds is None:
                response_timeout_in_seconds = self._default_response_timeout_in_seconds

            timed_out = not response_event.wait(response_timeout_in_seconds)
            del self._commands_waiting_for_response[sequence_number]
            response_event.clear()
            if timed_out:
                raise CommandTimedOutError()

        return response_packet

    def _receive_thread_run(self):
        receive_buffer = []
        while not self._class_destroy_event.is_set():
            receive_buffer.extend(self._bluetooth_interface.recv(1024))
            response_packet = None
            while len(receive_buffer) >= _MIN_PACKET_LENGTH:
                try:
                    response_packet = _ResponsePacket(receive_buffer)
                    # we have a valid response to handle
                    # break out of the inner while loop to handle
                    # the response
                    break
                except BufferNotLongEnoughError:
                    # break out of inner loop so we can fetch more data
                    break
                except PacketParseError:
                    # this is an error in the packet format
                    # remove one byte from the buffer and try again
                    receive_buffer.pop(0)
                    continue

            # TODO: need to refactor this loop
            # to not have so many breaks and continues.
            if response_packet is None:
                continue

            if response_packet.is_async:
                if response_packet.id_code is _ID_CODE_COLLISION_DETECTED:
                    collision_data = _CollisionData(response_packet.data)
                    for func in self.on_collision:
                        # schedule the callback on its own thread.
                        # TODO: there is probably a more asyncio way of doing this, but do we care?
                        # maybe we can run the function on the main thread's event loop?
                        callback_thread = threading.Thread(target=func, args=[collision_data])
                        callback_thread.daemon = True
                        callback_thread.start()
            else:
                # for ACK/sync responses we only need to call the registered callback.
                sequence_number = response_packet.sequence_number
                if sequence_number in self._commands_waiting_for_response:
                    self._commands_waiting_for_response[sequence_number](response_packet)
                    # NOTE: it is up to the callback/waiting function to remove the handler.
            # remove the packet we just handled
            del receive_buffer[:response_packet.packet_length]

    def _get_and_increment_command_sequence_number(self):
        result = self._command_sequence_number
        self._command_sequence_number += 1

        # Check if we have overflowed our sequence number byte.
        # If we have, start the sequence back at 0.
        if self._command_sequence_number > 0xFF:
            self._command_sequence_number = 0x00

        return result

class SpheroError(Exception):
    """
    """
    pass

class CommandTimedOutError(SpheroError):
    """Exception thrown when a command times out."""

    def __init__(self, message="Command timeout reached."):
        super().__init__(message)

class PacketError(SpheroError):
    """
    """

    def __init__(self, message="Error related to a packet occured."):
        super().__init__(message)

class PacketParseError(PacketError):
    """
    """

    def __init__(self, message="Error parsing a packet."):
        super().__init__(message)

class BufferNotLongEnoughError(PacketParseError):
    """
    """

    def __init__(
            self,
            expected_length,
            actual_length,
            message="Buffer not long enough for packet."):
        super().__init__(message)
        self.expected_length = expected_length
        self.actual_length = actual_length

# Minimum length of a valid packet
_MIN_PACKET_LENGTH = 6

# TODO: where to put these
_ID_CODE_POWER_NOTIFICATION = 0x01
_ID_CODE_LEVEL_1_DIAGNOSTICS = 0x02
_ID_CODE_COLLISION_DETECTED = 0x07
# TODO: Fill the rest

class VersionInfo(object):
    """
    """

    def __init__(self, data):
        self._record_version = data[0] if data else None
        self._model_number = data[1] if len(data) > 1 else None
        self._hardware_version = data[2] if len(data) > 2 else None
        self._main_sphero_app_version = data[3] if len(data) > 3 else None
        self._main_sphero_app_revision = data[4] if len(data) > 4 else None
        self._bootloader_version = data[5] if len(data) > 5 else None
        self._orb_basic_version = data[6] if len(data) > 6 else None
        self._macro_executive_version = data[7] if len(data) > 7 else None
        self._firmware_api_major_revision = data[8] if len(data) > 8 else None
        self._firmware_api_minor_revision = data[9] if len(data) > 9 else None

    @property
    def record_version(self):
        """
        """

        return self._record_version

    @property
    def model_number(self):
        """
        """

        return self._model_number

    @property
    def hardware_version(self):
        """
        """

        return self._hardware_version

    @property
    def main_sphero_app_version(self):
        """
        """

        return self._main_sphero_app_version

    @property
    def main_sphero_app_revision(self):
        """
        """

        return self._main_sphero_app_revision

    @property
    def bootloader_version(self):
        """
        """

        return self._bootloader_version

    @property
    def orb_basic_version(self):
        """
        """

        return self._orb_basic_version

    @property
    def macro_executive_version(self):
        """
        """

        return self._macro_executive_version

    @property
    def firmware_api_major_revision(self):
        """
        """

        return self._firmware_api_major_revision

    @property
    def firmware_api_minor_revision(self):
        """
        """

        return self._firmware_api_minor_revision

class BluetoothInfo(object):
    """
    """

    def __init__(self, data):
        self._name = ''.join(chr(i) for i in data[:16])
        self._bluetooth_address = ''.join(chr(i) for i in data[16:28])
        self._id_colors = ''.join(chr(i) for i in data[29:])

    @property
    def name(self):
        """The ASCII name of the Sphero."""

        return self._name

    @property
    def bluetooth_address(self):
        """The bluetooth address as ASCII string."""

        return self._bluetooth_address

    @property
    def id_colors(self):
        """The id colors of the Sphero as ASCII characters.

        These are the colors the Sphero will blink when it is not connected.
        """

        return self._id_colors


class _CollisionData(object):
    """
    """

    def __init__(self, data):
        if len(data) is not 0x10:
            raise ValueError(
                "data is not 16 bytes long. Actual length: {}".format(len(data)))

        self._x_impact = _pack_2_bytes(data[0], data[1])
        self._y_impact = _pack_2_bytes(data[2], data[3])
        self._z_impact = _pack_2_bytes(data[4], data[5])
        self._axis = data[6]
        self._x_magnitude = _pack_2_bytes(data[7], data[8])
        self._y_magnitude = _pack_2_bytes(data[9], data[10])
        self._speed = data[11]
        self._timestamp = _pack_4_bytes(data[12], data[13], data[14], data[15])

    @property
    def x_impact(self):
        """
        """

        return self._x_impact

    @property
    def y_impact(self):
        """
        """

        return self._y_impact

    @property
    def z_impact(self):
        """
        """

        return self._z_impact

    @property
    def axis(self):
        """
        """

        return self._axis

    @property
    def x_magnitude(self):
        """
        """

        return self._x_magnitude

    @property
    def y_magnitude(self):
        """
        """

        return self._y_magnitude

    @property
    def speed(self):
        """
        """

        return self._speed

    @property
    def timestamp(self):
        """
        """

        return self._timestamp

_DEVICE_ID_CORE = 0x00

_COMMAND_ID_PING = 0x01

def _create_ping_command(
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_PING,
        sequence_number=sequence_number,
        data=[],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_GET_VERSION = 0x02

def _create_get_version_command(
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_GET_VERSION,
        sequence_number=sequence_number,
        data=[],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_SET_DEVICE_NAME = 0x10

def _create_set_device_name_command(
        device_name,
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_SET_DEVICE_NAME,
        sequence_number=sequence_number,
        data=list(device_name),
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_GET_BLUETOOTH_INFO = 0x11

def _create_get_bluetooth_info_command(
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """

    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_GET_BLUETOOTH_INFO,
        sequence_number=sequence_number,
        data=[],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)


_DEVICE_ID_SPHERO = 0x02

_COMMAND_ID_CONFIGURE_COLLISION_DETECTION = 0x12

def _create_configure_collision_detection_command(
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

    return _ClientCommandPacket(
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

_COMMAND_ID_SET_RGB_LED = 0x20

def _create_set_rgb_led_command(
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

    return _ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_SET_RGB_LED,
        sequence_number=sequence_number,
        data=[red, green, blue, 1 if save_as_user_led_color else 0],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_GET_RGB_LED = 0x22

def _create_get_rgb_led_command(
        sequence_number=0x00,
        wait_for_response=True,
        reset_inactivity_timeout=True):
    """
    """

    return _ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_GET_RGB_LED,
        sequence_number=sequence_number,
        data=[],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_ROLL = 0x30

def _create_roll_command(
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

    return _ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_ROLL,
        sequence_number=sequence_number,
        data=[
            speed,
            _get_msb_of_2_bytes(heading_in_degrees),
            _get_lsb_of_2_bytes(heading_in_degrees),
            speed,  # This is the STATE value that was originally used in CES firmware.
        ],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

def _compute_checksum(packet):
    """Computes the checksum byte of a packet.

    Packet must not contain a checksum already

    Args:
        packet (list): List of bytes for a packet.
            packet must not contain a checksum
            as the last element

    Returns:
        The computed checksum byte
    """

    # checksum is the sum of the bytes
    # from device id to the end of the data
    # mod (%) 256 and bit negated (~) (1's compliment)
    # and (&) with 0xFF to make sure it is a byte.
    return ~(sum(packet[2:]) % 0x100) & 0xFF

class _ClientCommandPacket(object):
    """Represents a command packet sent from the client to a Sphero.
    """

    _START_OF_PACKET_1 = 0xFF
    _START_OF_PACKET_2_BASE = 0xFC
    _START_OF_PACKET_2_ANSWER_MASK = 0x01
    _START_OF_PACKET_2_RESET_INACTIVITY_TIMEOUT_MASK = 0x02

    def __init__(
            self,
            device_id,
            command_id,
            sequence_number=0x00,
            data=None,
            wait_for_response=True,
            reset_inactivity_timeout=True):

        if data is None:
            data = []

        start_of_packet_2 = self._START_OF_PACKET_2_BASE
        if wait_for_response:
            start_of_packet_2 |= self._START_OF_PACKET_2_ANSWER_MASK

        if reset_inactivity_timeout:
            start_of_packet_2 |= self._START_OF_PACKET_2_RESET_INACTIVITY_TIMEOUT_MASK

        self._packet = [
            self._START_OF_PACKET_1,
            start_of_packet_2,
            device_id,
            command_id,
            sequence_number,
            min(len(data) + 1, 0xFF),
        ]

        self._packet.extend(data)
        self._packet.append(_compute_checksum(self._packet))

    @property
    def bytes(self):
        """Get the ClientCommandPacket as a bytes object.

        Used to send the packet to the Sphero.

        Returns:
            The ClientCommandPacket as bytes.
        """

        return bytes(self._packet)

    @property
    def sequence_number(self):
        """
        """

        return self._packet[4]

class _ResponsePacket(object):
    """Represents a response packet from a Sphero to the client

    Will try to parse buffer provided to constructor as a packet

    Args:
        buffer (list): the raw byte buffer to
        try and parse as a packet

    Raises:
        PacketParseError if the first bytes
        in buffer are not a valid packet
    """

    _START_OF_PACKET_1_INDEX = 0
    _START_OF_PACKET_2_INDEX = 1

    # async response value indexes
    _ID_CODE_INDEX = 2
    _DATA_LENGTH_MSB_INDEX = 3
    _DATA_LENGTH_LSB_INDEX = 4

    # simple response value indexes
    _MESSAGE_RESPONSE_CODE_INDEX = 2
    _SEQUENCE_NUMBER_INDEX = 3
    _DATA_LENGTH_INDEX = 4

    _DATA_START_INDEX = 5

    # 1 becuase data length includes checksum which is always present
    _MIN_DATA_LENGTH = 1

    _START_OF_PACKET_2_SYNC = 0xFF
    _START_OF_PACKET_2_ASYNC = 0xFE

    def __init__(self, buffer):
        assert len(buffer) >= _MIN_PACKET_LENGTH, "Buffer is less than the minimum packet length"

        self._message_response_code = 0x00
        self._sequence_number = 0x00
        self._id_code = 0x00

        self._start_of_packet_byte_1 = buffer[self._START_OF_PACKET_1_INDEX]
        self._start_of_packet_byte_2 = buffer[self._START_OF_PACKET_2_INDEX]

        self._is_async = self._start_of_packet_byte_2 is self._START_OF_PACKET_2_ASYNC
        if self._is_async:
            self._id_code = buffer[self._ID_CODE_INDEX]
            self._data_length = _pack_2_bytes(
                buffer[self._DATA_LENGTH_MSB_INDEX],
                buffer[self._DATA_LENGTH_LSB_INDEX])
        else:
            self._message_response_code = buffer[self._MESSAGE_RESPONSE_CODE_INDEX]
            self._sequence_number = buffer[self._SEQUENCE_NUMBER_INDEX]
            self._data_length = buffer[self._DATA_LENGTH_INDEX]

        if self._data_length < self._MIN_DATA_LENGTH:
            raise PacketParseError("Found invalid data length (less than 1)")

        if self._data_length + _MIN_PACKET_LENGTH - 1 > len(buffer):
            raise BufferNotLongEnoughError(self._data_length + _MIN_PACKET_LENGTH - 1, len(buffer))

        checksum_index = self._checksum_index
        self._data = buffer[self._DATA_START_INDEX:checksum_index]
        self._checksum = buffer[checksum_index]

        if not self._is_data_length_valid:
            raise PacketParseError("Length of data does not match data length byte.")

        if self._checksum is not _compute_checksum(buffer[:checksum_index]):
            raise PacketParseError("Checksum is not correct")

    @property
    def is_async(self):
        """
        """
        return self._is_async

    @property
    def data(self):
        """
        """
        return self._data

    @property
    def id_code(self):
        """
        """

        return self._id_code

    @property
    def message_response(self):
        """
        """

        return self._message_response_code

    @property
    def sequence_number(self):
        """
        """

        return self._sequence_number

    @property
    def packet_length(self):
        """
        """

        return self._data_length + 5

    @property
    def _checksum_index(self):
        """
        """

        return self._data_length + 4

    @property
    def _is_data_length_valid(self):
        """
        """

        # data_length includes the length of data and the checksum
        return len(self._data) is self._data_length - 1

def _get_msb_of_2_bytes(value):
    """
    """

    return value >> 8 & 0xFF

def _get_lsb_of_2_bytes(value):
    """
    """

    return value & 0xFF

def _pack_2_bytes(msb, lsb):
    """
    """

    assert msb <= 0xFF
    assert lsb <= 0xFF

    return msb << 8 | lsb

def _pack_3_bytes(msb, byte1, lsb):
    """
    """

    assert msb <= 0xFF
    assert byte1 <= 0xFF
    assert lsb <= 0xFF

    return msb << 16 | byte1 << 8 | lsb

def _pack_4_bytes(msb, byte1, byte2, lsb):
    """
    """

    assert msb <= 0xFF
    assert byte1 <= 0xFF
    assert byte2 <= 0xFF
    assert lsb <= 0xFF

    return msb << 24 | byte1 << 16 | byte2 << 8 | lsb
