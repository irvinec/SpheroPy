"""spheropy

Interact with Sphero devices.
"""

import threading
import struct
from collections import namedtuple

# TODO: Need more parameter validation on functions.

class Sphero(object):
    """The main class that is used for interacting with a Sphero device.
    """

    def __init__(self, bluetooth_interface, default_response_timeout_in_seconds=0.5):
        self.on_collision = []
        self.on_power_state_change = []

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
        """Sends a ping to the Sphero.

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
                passed in the constructor of this Sphero.
        """
        command = _create_ping_command(
            self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        # Ping has no data so don't in response,
        # so no need tp return anything.
        await self._send_command(
            command,
            response_timeout_in_seconds)

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
                passed in the constructor of this Sphero.

        Returns:
            VersionInfo namedtuple.

            record_version (int):
            model_number (int):
            hardware_version (int):
            main_sphero_app_version (int):
            main_sphero_app_revision (int):
            bootloader_version (int):
            orb_basic_version (int):
            macro_executive_version (int):
            firmware_api_major_revision (int):
            firmware_api_minor_revision (int):
        """
        command = _create_get_version_command(
            self._get_and_increment_command_sequence_number(),
            wait_for_response=True,
            reset_inactivity_timeout=reset_inactivity_timeout)

        response_packet = await self._send_command(
            command,
            response_timeout_in_seconds)

        return _parse_version_info(response_packet.data)

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
                passed in the constructor of this Sphero.
        """
        command = _create_set_device_name_command(
            device_name=device_name,
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            command,
            response_timeout_in_seconds)

    async def get_bluetooth_info(
            self,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Gets bluetooth related info from the Sphero.

        Args:
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero object.

        Returns:
            BluetoothInfo namedtuple.

            name (str):
            bluetooth_address (str):
            id_colors (str):
        """
        command = _create_get_bluetooth_info_command(
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=True,
            reset_inactivity_timeout=reset_inactivity_timeout)

        response_packet = await self._send_command(
            command,
            response_timeout_in_seconds)

        return _parse_bluetooth_info(response_packet.data)

    async def set_auto_reconnect(
            self,
            should_enable_auto_reconnect,
            seconds_after_boot,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Sets the auto reconnect policy of the Sphero.

        This configures the control of the Bluetooth module in its attempt
        to automatically reconnect with the last mobile Apple device.
        This is a courtesy behavior since the Apple Bluetooth stack doesn't
        initiate automatic reconnection on its own.

        Args:
            should_enable_auto_reconnect (bool):
                True to enable auto reconnect, False to disable it.
            seconds_after_boot (int):
                The number of seconds after power-up
                in which to enable auto reconnect mode.
                For example, if seconds_after_boot = 30,
                then the module will attempt to reconnect
                30 seconds after waking up.
            wait_for_response (bool, True):
                If True, will wait for a response from the Sphero
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero.
        """
        command = _create_set_auto_reconnect_command(
            should_enable_auto_reconnect=should_enable_auto_reconnect,
            seconds_after_boot=seconds_after_boot,
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            command,
            response_timeout_in_seconds)

    async def get_auto_reconnect(
            self,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Gets the auto reconnect settings for the Sphero.

        Args:
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero.

        Returns:
            AutoReconnectInfo namedtuple.

            record_version (int):
            battery_state (int):
            battery_voltage (int):
            total_number_of_recharges (int):
            seconds_awake_since_last_recharge (int):
        """
        command = _create_get_auto_reconnect_command(
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=True,
            reset_inactivity_timeout=reset_inactivity_timeout)

        response_packet = await self._send_command(
            command,
            response_timeout_in_seconds=response_timeout_in_seconds)

        return _parse_auto_reconnect_info(response_packet.data)

    BATTERY_STATE_CHARGING = 0x01
    BATTERY_STATE_OK = 0x02
    BATTERY_STATE_LOW = 0x03
    BATTERY_STATE_CRITICAL = 0x04

    async def get_power_state(
            self,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Gets the current power state of the Sphero.

        Args:
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero.

        Returns:
            PowerState namedtuple.

            record_version (int):
                The record version code.

            battery_state (int):
                The current charge state of the battery.
                1 = Battery Charging = Sphero.BATTERY_STATE_CHARGING.
                2 = Battery OK = Sphero.BATTERY_STATE_OK.
                3 = Battery Low = Sphero.BATTERY_STATE_LOW.
                4 = Battery Critical = Sphero.BATTERY_STATE_CRITICAL.

            battery_volage (int):
                Current battery voltage in 1/100 of a volt.
                Unsigned 16-bit value.
                0x02EF would be 7.51 volts.

            total_number_of_recharges (int):
                Number of battery recharges in the lifetime
                of this Sphero.
                Unsigned 16-bit value.

            seconds_awake_since_last_recharge (int):
                Seconds awake since last recharge.
                Unsigned 16-bit value.
        """
        command = _create_get_power_state_command(
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=True,
            reset_inactivity_timeout=reset_inactivity_timeout)

        response_packet = await self._send_command(
            command,
            response_timeout_in_seconds=response_timeout_in_seconds)

        return _parse_power_state(response_packet.data)

    # TODO: rename to something better if possible
    # maybe enable_power_notifications
    async def set_power_notification(
            self,
            should_enable,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Enables/Disables receiving power notification from the Sphero.

        Enables/Disables the Sphero to asynchronously notify the client
        periodically with the power state or
        immediately when the power manager detects a state change.
        Timed notifications arrive every 10 seconds until they are explicitly disabled
        or Sphero is unpaired.
        This setting is volatile and therefore not retained across sleep cycles.

        Args:
            should_enable (bool):
                If True, power notifications will be enabled.
                If False, power notifications will be disabled.
            wait_for_response (bool, True):
                If True, will wait for a response from the Sphero
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero.
        """
        command = _create_set_power_notification_command(
            should_enable,
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            command,
            response_timeout_in_seconds=response_timeout_in_seconds)

    async def set_heading(
            self,
            heading,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Sets the heading of the Sphero.

        This allows the client to adjust the orientation of the Sphero
        by commanding a new reference heading in degrees,
        which ranges from 0 to 359.
        You will see the ball respond immediately to this command
        if stabilization is enabled.

        In firmware version 3.10 and later this also clears
        the maximum value counters for the rate gyro,
        effectively re-enabling the generation of an async message
        alerting the client to this event.

        Args:
            heading (int):
                The desired heading in degrees.
                In range [0, 359].
            wait_for_response (bool, True):
                If True, will wait for a response from the Sphero
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero.
        """
        command = _create_set_heading_command(
            heading=heading,
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            command,
            response_timeout_in_seconds=response_timeout_in_seconds)

    async def configure_collision_detection(
            self,
            turn_on_collision_detection,
            x_t, x_speed,
            y_t, y_speed,
            collision_dead_time,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Configure the Sphero's collision detection.

        Sphero contains a powerful analysis function to filter
        accelerometer data in order to detect collisions.
        Because this is a great example of a high-level concept
        that humans excel and – but robots do not – a number of 
        parameters control the behavior.
        When a collision is detected an asynchronous message
        is generated to the client.

        Args:
            turn_on_collision_detection (bool):
            x_t:
            x_speed:
            y_t:
            y_speed:
            collision_dead_time:
            wait_for_response (bool, True):
                If True, will wait for a response from the Sphero
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero.
        """
        command = _create_configure_collision_detection_command(
            turn_on_collision_detection=turn_on_collision_detection,
            x_t=x_t, x_speed=x_speed,
            y_t=y_t, y_speed=y_speed,
            collision_dead_time=collision_dead_time,
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            command,
            response_timeout_in_seconds)

    async def configure_locator(
            self,
            enable_auto_yaw_tare_correction=True,
            pos_x=0,
            pos_y=0,
            yaw_tare=0,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """
        """
        command = _create_configure_locator_command(
            enable_auto_yaw_tare_correction=enable_auto_yaw_tare_correction,
            pos_x=pos_x, pos_y=pos_y,
            yaw_tare=yaw_tare,
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            command,
            response_timeout_in_seconds)

    async def get_locator_info(
            self,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Gets the Sphero's locator info.

        Sphero locator info includes:
            current position (X,Y),
            component velocities
            and speed over ground

        The position is a signed value in centimeters.
        The component velocities are signed cm/sec.
        The SOG is unsigned cm/sec.

        Args:
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero.

        Returns:
            A LocatorInfo namedtuple.
                pos_x (int):
                    X position in centimeters.
                pos_y (int):
                    Y position in centimeters.
                vel_x (int):
                    X component velocity in cm/sec.
                vel_y (int):
                    Y component velocity in cm/sec.
                speed_over_ground (int):
                    The speed over ground in unsigned cm/sec.
        """
        command = _create_read_locator_command(
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=True,
            reset_inactivity_timeout=reset_inactivity_timeout)
        response_packet = await self._send_command(command, response_timeout_in_seconds)
        return _parse_locator_info(response_packet.data)

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
        command = _create_set_rgb_led_command(
            red,
            green,
            blue,
            save_as_user_led_color,
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(
            command,
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

        Args:
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero object.

        Returns:
            The user LED color as a list in the form
            [red, green, blue].
        """
        command = _create_get_rgb_led_command(
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=True, # must wait for the response to get the result.
            reset_inactivity_timeout=reset_inactivity_timeout)

        response_packet = await self._send_command(
            command,
            response_timeout_in_seconds)

        return response_packet.data

    async def set_back_led(
            self,
            brightness,
            wait_for_response=True,
            reset_inactivity_timeout=True,
            response_timeout_in_seconds=None):
        """Sets the brightness for the back LED.

        This allows you to control the brightness of the back LED.
        The value does not persist across power cycles.

        Args:
            brightness (int):
                The brightness of the back LED.
            wait_for_response (bool, True):
                If True, will wait for a response from the Sphero
            reset_inactivity_timeout (bool, True):
                If True, will reset the inactivity timer on the Sphero.
            response_timeout_in_seconds (float, None):
                The amount of time to wait for a response.
                If not specified or None, uses the default timeout
                passed in the constructor of this Sphero object.
        """
        command = _create_set_back_led_output_command(
            brightness=brightness,
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(command, response_timeout_in_seconds)

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
        command = _create_roll_command(
            speed,
            heading_in_degrees,
            sequence_number=self._get_and_increment_command_sequence_number(),
            wait_for_response=wait_for_response,
            reset_inactivity_timeout=reset_inactivity_timeout)

        await self._send_command(command, response_timeout_in_seconds)

    async def _send_command(
            self,
            command,
            response_timeout_in_seconds):
        """
        """

        response_event = threading.Event()
        response_packet = None
        if command.wait_for_response:
            # define a generic response handler
            # TODO: might need the ability to pass a custom handler
            def handle_response(received_response_packet):
                nonlocal response_packet
                response_packet = received_response_packet
                nonlocal response_event
                response_event.set()

            # Register the response handler for this commands sequence number
            assert command.sequence_number not in self._commands_waiting_for_response, \
                ("A response handler was already registered for the sequence number {}"
                 .format(command.sequence_number))
            self._commands_waiting_for_response[command.sequence_number] = handle_response

        self._bluetooth_interface.send(command.bytes)

        # Wait for the response if necessary
        if command.wait_for_response:
            if response_timeout_in_seconds is None:
                response_timeout_in_seconds = self._default_response_timeout_in_seconds

            timed_out = not response_event.wait(response_timeout_in_seconds)
            del self._commands_waiting_for_response[command.sequence_number]
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
                    collision_info = _parse_collision_info(response_packet.data)
                    for func in self.on_collision:
                        # schedule the callback on its own thread.
                        # TODO: there is probably a more asyncio way of doing this, but do we care?
                        # maybe we can run the function on the main thread's event loop?
                        # TODO: refactor kicking off callback in seperate thread to a function
                        callback_thread = threading.Thread(target=func, args=[collision_info])
                        callback_thread.daemon = True
                        callback_thread.start()
                elif response_packet.id_code is _ID_CODE_POWER_NOTIFICATION:
                    power_state = response_packet.data[0]
                    for func in self.on_power_state_change:
                        callback_thread = threading.Thread(target=func, args=[power_state])
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

#region Public Exceptions
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
#endregion

# Minimum length of a valid packet
_MIN_PACKET_LENGTH = 6

# TODO: where to put these
_ID_CODE_POWER_NOTIFICATION = 0x01
_ID_CODE_COLLISION_DETECTED = 0x07
# TODO: Fill the rest as needed

#region Data Tuples and Parsers
VersionInfo = namedtuple(
    "VersionInfo",
    ["record_version",
     "model_number",
     "hardware_version",
     "main_sphero_app_version",
     "main_sphero_app_revision",
     "bootloader_version",
     "orb_basic_version",
     "macro_executive_version",
     "firmware_api_major_revision",
     "firmware_api_minor_revision"])

def _parse_version_info(data):
    return VersionInfo(
        data[0] if data else None,
        data[1] if len(data) > 1 else None,
        data[2] if len(data) > 2 else None,
        data[3] if len(data) > 3 else None,
        data[4] if len(data) > 4 else None,
        data[5] if len(data) > 5 else None,
        data[6] if len(data) > 6 else None,
        data[7] if len(data) > 7 else None,
        data[8] if len(data) > 8 else None,
        data[9] if len(data) > 9 else None)

BluetoothInfo = namedtuple(
    "BluetoothInfo",
    ["name",
    "bluetooth_address",
    "id_colors"])

def _parse_bluetooth_info(data):
    """
    """
    return BluetoothInfo(
        ''.join(chr(i) for i in data[:16]),
        ''.join(chr(i) for i in data[16:28]),
        ''.join(chr(i) for i in data[29:]))

AutoReconnectInfo = namedtuple(
    "AutoReconnectInfo",
    ["is_enabled",
     "seconds_after_boot"])

def _parse_auto_reconnect_info(data):
    """
    """
    if len(data) is not 2:
        raise ValueError(
            "data is not 2 bytes long. Actual length: {}".format(len(data)))

    return AutoReconnectInfo(
        data[0] is not 0,
        data[1])

PowerState = namedtuple(
    "PowerState",
    ["record_version",
     "battery_state",
     "battery_voltage",
     "total_number_of_recharges",
     "seconds_awake_since_last_recharge"])

def _parse_power_state(data):
    """
    """
    return PowerState(
        data[0],
        data[1],
        _pack_bytes(data[2:4]),
        _pack_bytes(data[4:6]),
        _pack_bytes(data[6:8]))

LocatorInfo = namedtuple(
    "LocatorInfo",
    ["pos_x",
     "pos_y",
     "vel_x",
     "vel_y",
     "speed_over_ground"])

def _parse_locator_info(data):
    """
    """
    return LocatorInfo(
        struct.unpack('>h', bytes(data[0:2])),  # signed short
        struct.unpack('>h', bytes(data[2:4])),  # signed short
        struct.unpack('>h', bytes(data[4:6])),  # signed short
        struct.unpack('>h', bytes(data[6:8])),  # signed short
        struct.unpack('>H', bytes(data[8:10]))) # unsigned short

CollisionInfo = namedtuple(
    "CollisionInfo",
    ["x_impact",
     "y_impact",
     "z_impact",
     "axis",
     "x_magnitude",
     "y_magnitude",
     "speed",
     "timestamp"])

def _parse_collision_info(data):
    """
    """

    if len(data) is not 0x10:
        raise ValueError(
            "data is not 16 bytes long. Actual length: {}".format(len(data)))

    return CollisionInfo(
        struct.unpack('>h', bytes(data[0:2])),  # signed short
        struct.unpack('>h', bytes(data[2:4])),  # signed short
        struct.unpack('>h', bytes(data[4:6])),  # signed short
        data[6],
        _pack_bytes(data[7:9]),
        _pack_bytes(data[9:11]),
        data[11],
        _pack_bytes(data[12:16]))

#endregion

#region Command Factory Methods

_DEVICE_ID_CORE = 0x00

_COMMAND_ID_PING = 0x01
def _create_ping_command(
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_PING,
        sequence_number=sequence_number,
        data=None,
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_GET_VERSION = 0x02
def _create_get_version_command(
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_GET_VERSION,
        sequence_number=sequence_number,
        data=None,
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_SET_DEVICE_NAME = 0x10
def _create_set_device_name_command(
        device_name,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_SET_DEVICE_NAME,
        sequence_number=sequence_number,
        data=[ord(i) for i in device_name],
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
        data=None,
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_SET_AUTO_RECONNECT = 0x12
def _create_set_auto_reconnect_command(
        should_enable_auto_reconnect,
        seconds_after_boot,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_SET_AUTO_RECONNECT,
        sequence_number=sequence_number,
        data=[
            0x01 if should_enable_auto_reconnect else 0x00,
            seconds_after_boot
        ],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_GET_AUTO_RECONNECT = 0x13
def _create_get_auto_reconnect_command(
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_GET_AUTO_RECONNECT,
        sequence_number=sequence_number,
        data=None,
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_GET_POWER_STATE = 0x20
def _create_get_power_state_command(
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_GET_POWER_STATE,
        sequence_number=sequence_number,
        data=None,
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_SET_POWER_NOTIFICATION = 0x21
def _create_set_power_notification_command(
        should_enable,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_CORE,
        command_id=_COMMAND_ID_SET_POWER_NOTIFICATION,
        sequence_number=sequence_number,
        data=[0x01 if should_enable else 0x00],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_DEVICE_ID_SPHERO = 0x02

_COMMAND_ID_SET_HEADING = 0x01
def _create_set_heading_command(
        heading,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_SET_HEADING,
        sequence_number=sequence_number,
        data=[
            _get_byte_at_index(heading, 1),
            _get_byte_at_index(heading, 0)
        ],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_CONFIGURE_COLLISION_DETECTION = 0x12
def _create_configure_collision_detection_command(
        turn_on_collision_detection,
        x_t,
        x_speed,
        y_t,
        y_speed,
        collision_dead_time,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
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

_COMMAND_ID_CONFIGURE_LOCATOR = 0x13
def _create_configure_locator_command(
        enable_auto_yaw_tare_correction,
        pos_x,
        pos_y,
        yaw_tare,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_CONFIGURE_LOCATOR,
        sequence_number=sequence_number,
        data=[
            0x80 if enable_auto_yaw_tare_correction else 0,
            _get_byte_at_index(pos_x, 0),
            _get_byte_at_index(pos_x, 1),
            _get_byte_at_index(pos_y, 0),
            _get_byte_at_index(pos_y, 1),
            _get_byte_at_index(yaw_tare, 0),
            _get_byte_at_index(yaw_tare, 0)
        ],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_READ_LOCATOR = 0x15
def _create_read_locator_command(
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_READ_LOCATOR,
        sequence_number=sequence_number,
        data=None,
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_SET_RGB_LED = 0x20
def _create_set_rgb_led_command(
        red,
        green,
        blue,
        save_as_user_led_color,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
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
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_GET_RGB_LED,
        sequence_number=sequence_number,
        data=[],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_SET_BACK_LED_OUTPUT = 0x21
def _create_set_back_led_output_command(
        brightness,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
    """
    """
    return _ClientCommandPacket(
        device_id=_DEVICE_ID_SPHERO,
        command_id=_COMMAND_ID_SET_BACK_LED_OUTPUT,
        sequence_number=sequence_number,
        data=[brightness],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

_COMMAND_ID_ROLL = 0x30
def _create_roll_command(
        speed,
        heading_in_degrees,
        sequence_number,
        wait_for_response,
        reset_inactivity_timeout):
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
            _get_byte_at_index(heading_in_degrees, 1),
            _get_byte_at_index(heading_in_degrees, 0),
            1 if speed > 0 else 0   # This is the STATE value that was originally used in CES firmware.
        ],
        wait_for_response=wait_for_response,
        reset_inactivity_timeout=reset_inactivity_timeout)

#endregion

#region Private Package Classes

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

        self._wait_for_response = wait_for_response

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

    @property
    def wait_for_response(self):
        """
        """
        return self._wait_for_response

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
            self._data_length = _pack_bytes([
                buffer[self._DATA_LENGTH_MSB_INDEX],
                buffer[self._DATA_LENGTH_LSB_INDEX]])
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

#endregion

#region Private Utility Methods

def _compute_checksum(packet):
    """Computes the checksum byte of a packet.

    Packet must not contain a checksum already

    Args:
        packet (list):
            List of bytes for a packet.
            packet must not contain a checksum
            as the last element

    Returns:
        The computed checksum byte.
    """
    # checksum is the sum of the bytes
    # from device id to the end of the data
    # mod (%) 256 and bit negated (~) (1's compliment)
    # and (&) with 0xFF to make sure it is a byte.
    return ~(sum(packet[2:]) % 0x100) & 0xFF

def _get_byte_at_index(value, index):
    """
    """
    return value >> index*8 & 0xFF

# TODO: replace with struct.unpack
def _pack_bytes(byte_list):
    """Packs a list of bytes to be a single number.

    The MSB is the leftmost byte (index 0).
    The LSB is the rightmost byte (index -1 or len(byte_list) - 1).
    Each value in byte_list is assumed to be a byte (range [0, 255]).
    This assumption is not validated in this function.

    Args:
        byte_list (list):

    Returns:
        The number resulting from the packed bytes.
    """
    left_shift_amount = 0
    value = 0
    # iterate backwards and pack the bits from right to left
    for byte_value in reversed(byte_list):
        assert byte_value >= 0 and byte_value <= 255
        value |= byte_value << left_shift_amount
        left_shift_amount += 8

    return value

#endregion