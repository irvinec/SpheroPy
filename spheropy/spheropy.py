"""spheropy

Interact with Sphero devices.
"""
import os, sys
import uuid
import threading
import struct
import queue
import enum
from collections import namedtuple


USE_PYBLUEZ = True
try:
    import bluetooth # pybluez
    HAS_PYBLUEZ = True
except Exception:
    HAS_PYBLUEZ = False

USE_PYGATT = True
try:
    import pygatt
    HAS_PYGATT = True
except Exception:
    HAS_PYGATT = False

USE_WINBLE = True
try:
    import winble
    HAS_WINBLE = True
except Exception:
    HAS_WINBLE = False

# TODO: Need more parameter validation on functions and throughout.

# region Sphero

class Sphero(object):
    """The main class that is used for interacting with a Sphero device."""

#region Sphero public members

    def __init__(self, default_response_timeout_in_seconds=0.5):
        self.on_collision = []
        self.on_power_state_change = []

        self._bluetooth_interface = None
        self._default_response_timeout_in_seconds = default_response_timeout_in_seconds
        self._command_sequence_number = 0x00

        # Message processing members
        self._commands_waiting_for_response = {}
        # TODO: Consider passing in a max size for the queue.
        self._message_receive_queue = queue.Queue()
        self._message_processing_thread = None

    async def connect(self,
            search_name=None,
            address=None,
            port=None,
            bluetooth_interface=None,
            use_ble=False,
            num_retry_attempts=1):
        """Connects to the Sphero.

        Must be called before calling any other methods.

        Args:
            search_name (str):
                The partial name of the device to connect to.
                Must be specified if address is not.
            address (str):
                The bluetooth address of the device.
                Must be specified if search_name is not.
            port (str or int):
                Can have different meaning for different bluetooth interfaces.
                Can be the bluetooth port, or COM port.
            bluetooth_interface (BluetoothInterfaceBase):
                A custom bluetooth interface to use instead of the defaults.
            use_ble (bool):
                Indicates that BLE protocol should be used.
            num_retry_attempts (int):
                The number of times to try to connect.
                Defaults to 1.
        """
        # Create the bluetooth interface
        global HAS_PYBLUEZ
        global USE_PYBLUEZ
        global HAS_PYGATT
        global USE_PYGATT
        global HAS_WINBLE
        global USE_WINBLE
        if bluetooth_interface is None:
            if use_ble:
                if (HAS_PYGATT and USE_PYGATT) or (HAS_WINBLE and USE_WINBLE):
                    self._bluetooth_interface = BleInterface(search_name=search_name, address=address, port=port)
                else:
                    raise RuntimeError('Could not import a bluetooth LE Library.')
            else:
                if HAS_PYBLUEZ and USE_PYBLUEZ:
                    self._bluetooth_interface = BluetoothInterface(search_name=search_name, address=address, port=port)
                else:
                    raise RuntimeError('Could not import a bluetooth (non-BLE) library.')
        else:
            self._bluetooth_interface = bluetooth_interface

        self._bluetooth_interface.data_received_handler = self._handle_data_received
        self._bluetooth_interface.connect(num_retry_attempts=num_retry_attempts)
        print('Connected to Sphero.')

    async def ping(self,
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

        await self._send_command(
            command,
            response_timeout_in_seconds)

    async def get_version_info(self,
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

    async def set_device_name(self,
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

    async def get_bluetooth_info(self,
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

    async def set_auto_reconnect(self,
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

    async def get_auto_reconnect(self,
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

    async def get_power_state(self,
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
    async def set_power_notification(self,
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

    async def set_heading(self,
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

    async def configure_collision_detection(self,
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

    async def configure_locator(self,
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

    async def get_locator_info(self,
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

    async def set_rgb_led(self,
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

    async def get_rgb_led(self,
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

    async def set_back_led(self,
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

    async def roll(self,
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

#endregion Sphero public members

# region Sphero private members

    async def _send_command(self,
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
            assert command.sequence_number not in self._commands_waiting_for_response, f'A response handler was already registered for the sequence number {command.sequence_number}'
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

    def _handle_data_received(self, received_data):
        self._message_receive_queue.put(received_data)
        if self._message_processing_thread is None or not self._message_processing_thread.is_alive():
            self._message_processing_thread = threading.Thread(
                target=_process_messages,
                args=
                    [
                        self._message_receive_queue,
                        self._commands_waiting_for_response,
                        self.on_collision,
                        self.on_power_state_change
                    ]
            )
            self._message_processing_thread.start()

    def _get_and_increment_command_sequence_number(self):
        result = self._command_sequence_number
        self._command_sequence_number += 1

        # Check if we have overflowed our sequence number byte.
        # If we have, start the sequence back at 0.
        if self._command_sequence_number > 0xFF:
            self._command_sequence_number = 0x00

        return result

#endregion Sphero private members

def _process_messages(
        message_queue,
        commands_waiting_for_response,
        on_collision_callbacks,
        on_power_state_change_callbacks):
    """Process messages received.

    Parses the messages recieved 
    """
    message = []
    # Keep going as long as there is a message in the queue,
    # or if we are still processing or looking for more data
    # in message.
    while (not message_queue.empty()) or message:
        response_packet = None
        message_part = message_queue.get()
        if message_part is None:
            return

        message.extend(message_part)
        response_packet = _parse_message(message)
        if response_packet is not None:
            if response_packet.is_async:
                _handle_async_response(
                    response_packet,
                    on_collision_callbacks,
                    on_power_state_change_callbacks
                )
            else:
                _handle_sync_response(
                    response_packet,
                    commands_waiting_for_response
                )

            # Remove the packet we just handled
            del message[:response_packet.packet_length]

        message_queue.task_done()

def _parse_message(message):
    while len(message) >= _MIN_PACKET_LENGTH:
        response_packet = _ResponsePacket(message)
        if response_packet.status == _ResponsePacketStatus.VALID:
            # we have a valid response to handle
            # break out of the inner while loop to handle
            # the response.
            return response_packet
        elif response_packet.status == _ResponsePacketStatus.NOT_ENOUGH_BUFFER:
            # Return and wait to get more data.
            return None
        else:
            # There is an error in the packet format.
            # Remove all the bytes until the next SOP1 byte.
            del message[: message.index(_ResponsePacket._START_OF_PACKET_1)]
            continue

    return None

def _handle_async_response(
        response_packet,
        on_collision_callbacks,
        on_power_state_change_callbacks):
    """
    """
    if response_packet.id_code is _ID_CODE_COLLISION_DETECTED:
        collision_info = _parse_collision_info(response_packet.data)
        for func in on_collision_callbacks:
            # Schedule the callback on its own thread.
            # TODO: there is probably a more asyncio way of doing this, but do we care?
            # Maybe we can run the function on the main thread's event loop?
            # TODO: Refactor kicking off callback in seperate thread to a function
            callback_thread = threading.Thread(target=func, args=[collision_info])
            callback_thread.daemon = True
            callback_thread.start()
    elif response_packet.id_code is _ID_CODE_POWER_NOTIFICATION:
        power_state = response_packet.data[0]
        for func in on_power_state_change_callbacks:
            callback_thread = threading.Thread(target=func, args=[power_state])
            callback_thread.daemon = True
            callback_thread.start()

def _handle_sync_response(
        response_packet,
        commands_waiting_for_response):
    """
    """
    # for ACK/synchronous responses we only need to call the registered callback.
    sequence_number = response_packet.sequence_number
    if sequence_number in commands_waiting_for_response:
        # TODO: check to make sure handler is callable before invoking.
        commands_waiting_for_response[sequence_number](response_packet)
        # NOTE: it is up to the callback/waiting function to remove the handler.

#endregion Sphero

#region Public Exceptions

class SpheroError(Exception):
    """
    """
    pass

class CommandTimedOutError(SpheroError):
    """Exception thrown when a command times out."""

    def __init__(self, message="Command timeout reached."):
        super().__init__(message)

#endregion

#region Bluetooth Interfaces

class BluetoothInterfaceBase(object):
    """Base class for Bluetooth Interfaces

    Args:
        search_name (str):
            The name to use when searching for Sphero device.
            Finds any device that starts with search_name.
            Defaults to DEFAULT_SEARCH_NAME.
            Only used if address is not specified.
        address (str):
            The bluetooth address of the device.
            If not specified, search_name should be specified.
        port (str or int):
            Can have different meaning for subclasses.
            Can be the bluetooth port, or COM port.
            Defaults to DEFAULT_PORT
    """
    DEFAULT_SEARCH_NAME = None
    DEFAULT_PORT = None

    def __init__(self, search_name=None, address=None, port=None):
        super().__init__()
        self.data_received_handler = None
        self._search_name = self.DEFAULT_SEARCH_NAME if search_name is None else search_name
        self._port = self.DEFAULT_PORT if port is None else port
        self._address = address

    def connect(self, num_retry_attempts=1):
        """Connects to the sphero device.

        Args:
            num_retry_attempts (int):
                The number of times to try to connect.
                Defaults to 1.
        """
        pass

    def send(self, data):
        """Sends raw data to the device.

        Args:
            data (list):
                The raw data to send as list of bytes.
        """
        pass

    def disconnect(self):
        """Disconnects from the device."""
        pass


class BluetoothInterface(BluetoothInterfaceBase):
    """Legacy Bluetooth Interface"""

    DEFAULT_SEARCH_NAME = 'Sphero'
    DEFAULT_PORT = 1

    def __init__(self, search_name=None, address=None, port=None):
        super().__init__(search_name, address, port)
        self._sock = None

        # setup thread for receiving responses
        self._class_destroy_event = threading.Event()
        self._receive_thread = threading.Thread(target=self._receive_thread_run)
        self._receive_thread.daemon = True
        self._receive_thread.start()

    def connect(self, num_retry_attempts=1):
        super().connect(num_retry_attempts)
        is_connected = False
        for _ in range(num_retry_attempts):
            if self._address is None:
                self._address = self._find_device(self._search_name)

            if self._address is not None:
                self._sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self._sock.connect((self._address, self._port))
                is_connected = True
                break

        if self._address is None:
            raise RuntimeError(
                f'Could not find device with name {self._search_name} after {num_retry_attempts} tries.'
            )
        elif not is_connected:
            raise RuntimeError(
                f'Count not connect to device {self._address} after {num_retry_attempts} tries.'
            )

    def send(self, data):
        if self._sock is not None:
            self._sock.send(data)

    def disconnect(self):
        if self._sock is not None:
            self._sock.close()

    def _receive_thread_run(self):
        """Checks for received data and calls handler.

        Used to create background thread to listen
        for data received from device.
        """
        while not self._class_destroy_event.is_set():
            if self._sock is not None:
                data = self._sock.recv(1024)
                if data is not None and len(data) > 0:
                    if self.data_received_handler is not None:
                        if callable(self.data_received_handler):
                            self.data_received_handler(data)
                        else:
                            raise ValueError('data_received_handler is not callable.')

    @staticmethod
    def _find_device(search_name):
        found_device_address = None
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        if nearby_devices:
            for address, name in nearby_devices:
                if name.startswith(search_name):
                    found_device_address = address
                    print(f'Found device named: {name} at {found_device_address}')
                    break

        return found_device_address

class BleInterface(BluetoothInterfaceBase):
    """Bluetooth Low Energy (BLE) Interface"""

    _BLE_SERVICE = uuid.UUID("22bb746f-2bb0-7554-2d6f-726568705327")
    _BLE_SERVICE_WAKE = uuid.UUID("22bb746f-2bbf-7554-2d6f-726568705327")
    _BLE_SERVICE_TX_POWER = uuid.UUID("22bb746f-2bb2-7554-2d6f-726568705327")
    _BLE_SERVICE_ANTI_DOS = uuid.UUID("22bb746f-2bbd-7554-2d6f-726568705327")
    _ROBOT_SERVICE = uuid.UUID('22BB746F-2BA0-7554-2D6F-726568705327')
    _ROBOT_SERVICE_CONTROL = uuid.UUID('22BB746F-2BA1-7554-2D6F-726568705327')
    _ROBOT_SERVICE_RESPONSE = uuid.UUID('22BB746F-2BA6-7554-2D6F-726568705327')

    _ANTI_DOS_MESSAGE = '011i3'
    _TX_POWER_VALUE = 7

    DEFAULT_SEARCH_NAME = 'SK'
    DEFAULT_PORT = None

    BleAdapterType = enum.Enum('BleAdapterType', 'PYGATT WINBLE')

    def __init__(self, search_name=None, address=None, port=None):
        super().__init__(search_name, address, port)
        self._adapter = None
        self._adapter_type = None
        self._device = None

    def connect(self, num_retry_attempts=1):
        super().connect(num_retry_attempts)
        for _ in range(num_retry_attempts):
            if self._address is None:
                if not self._find_adapter():
                    continue

                if not self._find_device():
                    continue

            if self._address is not None:
                self._connect()

                self._turn_on_dev_mode()
                self._subscribe()

                is_connected = True
                break

        if self._address is None:
            raise RuntimeError(
                f'Could not find device with name {self._search_name} after {num_retry_attempts} tries.'
            )
        elif not is_connected:
            raise RuntimeError(
                f'Count not connect to device {self._address} after {num_retry_attempts} tries.'
            )

    def _connect(self):
        if self._adapter_type is BleInterface.BleAdapterType.PYGATT:
            self._device = self._adapter.connect(
                address=self._address,
                address_type=pygatt.BLEAddressType.random
            )
        elif self._adapter_type is BleInterface.BleAdapterType.WINBLE:
            self._device = self._adapter.connect(self._address)

    def _subscribe(self):
        if self._adapter_type == BleInterface.BleAdapterType.PYGATT:
            self._device.subscribe(self._ROBOT_SERVICE_RESPONSE, self._pygatt_response_callback)
        elif self._adapter_type is BleInterface.BleAdapterType.WINBLE:
            self._device.subscribe(self._ROBOT_SERVICE_RESPONSE.bytes, self._winble_response_callback)

    def send(self, data):
        super().send(data)
        if self._device is not None:
            # TODO: need to understand how ble ack works
            # so we know if we should set the wait_for_response param.
            self._char_write(self._ROBOT_SERVICE_CONTROL, data)

    def disconnect(self):
        super().disconnect()
        if self._device is not None:
            self._device.disconnect()

    def _pygatt_response_callback(self, characteristic_handle, value):
        """Callback for when data is received from device.

        Calls registered data received handler.
        Specific to PyGatt.
        """
        if self.data_received_handler is not None:
            if callable(self.data_received_handler):
                self.data_received_handler(value)
            else:
                raise ValueError('data_received_handler is not callable.')

    def _winble_response_callback(self, value):
        """Callback for when data is received from device.

        Calls registered data received handler.
        Specific to WinBle.
        """
        if self.data_received_handler is not None:
            if callable(self.data_received_handler):
                self.data_received_handler(value)
            else:
                raise ValueError('data_received_handler is not callable.')

    def _turn_on_dev_mode(self):
        """Turns on 'dev mode' for the Sphero.

        This is necessary to start sending the raw commands to the Sphero
        and to receive data from the Sphero.
        """
        if self._device is not None:
            self._char_write(
                self._BLE_SERVICE_ANTI_DOS,
                [ord(c) for c in self._ANTI_DOS_MESSAGE]
            )
            self._char_write(
                self._BLE_SERVICE_TX_POWER,
                [self._TX_POWER_VALUE]
            )
            # Sending 0x01 to the wake service wakes the sphero.
            self._char_write(self._BLE_SERVICE_WAKE, [0x01])

    def _char_write(self, charId, data):
        if self._adapter_type == BleInterface.BleAdapterType.PYGATT:
            self._device.char_write(charId, bytes(data))
        elif self._adapter_type == BleInterface.BleAdapterType.WINBLE:
            self._device.char_write(charId.bytes, bytes(data))

    def _find_adapter(self):
        """
        """
        adapter = None
        adapter_type = None
        found_adapter = False

        # Try pygatt BGAPI for all platforms first.
        global HAS_PYGATT
        global USE_PYGATT
        if HAS_PYGATT and USE_PYGATT:
            try:
                adapter = pygatt.BGAPIBackend(serial_port=self._port)
                adapter.start()
                adapter_type = BleInterface.BleAdapterType.PYGATT
                found_adapter = True
            except pygatt.exceptions.NotConnectedError:
                pass

        # If we couldn't find the adapter,
        # Try a platform specific adapter.
        if not found_adapter:
            global HAS_WINBLE
            global USE_WINBLE
            if _is_windows() and HAS_WINBLE and USE_WINBLE:
                try:
                    adapter = winble.WinBleAdapter()
                    adapter.start()
                    adapter_type = BleInterface.BleAdapterType.WINBLE
                    found_adapter = True
                except Exception:
                    pass
            elif _is_linux() and HAS_PYGATT and USE_PYGATT:
                try:
                    adapter = pygatt.backends.GATTToolBackend()
                    adapter.start()
                    adapter_type = BleInterface.BleAdapterType.PYGATT
                    found_adapter = True
                except pygatt.exceptions.NotConnectedError:
                    pass

        if found_adapter:
            self._adapter = adapter
            self._adapter_type = adapter_type

        return found_adapter

    def _find_device(self):
        """Looks for a matching nearby device."""
        found_device = False
        nearby_devices = None
        try:
            nearby_devices = self._adapter.scan()
        except Exception:
            pass

        if nearby_devices is not None:
            for device in nearby_devices:
                name = device['name']
                if name is not None and name.startswith(self._search_name):
                    self._address = device['address']
                    print(f'Found device named: {name} at {self._address}')
                    found_device = True
                    break

        return found_device

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
        _pack_bytes_signed(data[0:2]),
        _pack_bytes_signed(data[2:4]),
        _pack_bytes_signed(data[4:6]),
        _pack_bytes_signed(data[6:8]),
        _pack_bytes(data[8:10])
    )

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
        _pack_bytes_signed(data[0:2]),
        _pack_bytes_signed(data[2:4]),
        _pack_bytes_signed(data[4:6]),
        data[6],
        _pack_bytes(data[7:9]),
        _pack_bytes(data[9:11]),
        data[11],
        _pack_bytes(data[12:16])
    )

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

class _ResponsePacketStatus(enum.Enum):
    VALID = enum.auto()
    NOT_ENOUGH_BUFFER = enum.auto()
    INVALID_DATA = enum.auto()
    INCORRECT_LENGTH = enum.auto()


class _ResponsePacket(object):
    """Represents a response packet from a Sphero to the client

    Will try to parse buffer provided to constructor as a packet

    Args:
        buffer (list): the raw byte buffer to
        try and parse as a packet
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

    _START_OF_PACKET_1 = 0xFF
    _START_OF_PACKET_2_SYNC = 0xFF
    _START_OF_PACKET_2_ASYNC = 0xFE

    def __init__(self, buffer):
        assert len(buffer) >= _MIN_PACKET_LENGTH, "Buffer is less than the minimum packet length"
        self.status = _ResponsePacketStatus.VALID
        self._message_response_code = 0x00
        self._sequence_number = 0x00
        self._id_code = 0x00

        self._start_of_packet_byte_1 = buffer[self._START_OF_PACKET_1_INDEX]
        if self._start_of_packet_byte_1 != self._START_OF_PACKET_1:
            self.status = _ResponsePacketStatus.INVALID_DATA
            return

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
            self.status = _ResponsePacketStatus.INCORRECT_LENGTH
            return

        if self._data_length + _MIN_PACKET_LENGTH - 1 > len(buffer):
            self.status = _ResponsePacketStatus.NOT_ENOUGH_BUFFER
            return

        checksum_index = self._checksum_index
        self._data = buffer[self._DATA_START_INDEX:checksum_index]
        self._checksum = buffer[checksum_index]

        if not self._is_data_length_valid:
            self.status = _ResponsePacketStatus.INCORRECT_LENGTH
            return

        if self._checksum is not _compute_checksum(buffer[:checksum_index]):
            self.status = _ResponsePacketStatus.INVALID_DATA
            return

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
    # NOTE: We could also use int.to_bytes to just convert
    # value into a byte array.
    return value >> index*8 & 0xFF

def _pack_bytes(byte_list):
    """Packs a list of bytes to be a single unsigned int.

    The MSB is the leftmost byte (index 0).
    The LSB is the rightmost byte (index -1 or len(byte_list) - 1).
    Big Endian order.
    Each value in byte_list is assumed to be a byte (range [0, 255]).
    This assumption is not validated in this function.

    Args:
        byte_list (list):

    Returns:
        The number resulting from the packed bytes.
    """
    return int.from_bytes(byte_list, 'big', signed=False)

def _pack_bytes_signed(byte_list):
    """Packs a list of bytes to be a single signed int.

    The MSB is the leftmost byte (index 0).
    The LSB is the rightmost byte (index -1 or len(byte_list) - 1).
    Big Endian order.
    Each value in byte_list is assumed to be a byte (range [0, 255]).
    This assumption is not validated in this function.

    Args:
        byte_list (list):

    Returns:
        The number resulting from the packed bytes.
    """
    return int.from_bytes(byte_list, 'big', signed=True)

def _is_windows():
    """
    """
    return os.name == 'nt'

def _is_linux():
    """
    """
    return os.name == 'posix'

#endregion