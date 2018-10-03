# sphero.py

# Should look at sphero_ros sphero_driver implementation.
# It looks pretty good but does not hide the right data.
# https://github.com/mmwise/sphero_ros

import asyncio
import threading

import sphero.packets
import sphero.commands

__all__ = ['Sphero', 'CommandTimedOutError']

class CommandTimedOutError(Exception):
    def __init__(self):
        pass

class Sphero:
    """The main Sphero class that is used for interacting with a Sphero device.
    """

    def __init__(self, bluetooth_interface, response_timeout = 0.5):
        self._bluetooth_interface = bluetooth_interface
        """Bluetooth interface object that implements send and receive"""
        self._response_timeout = response_timeout
        """Timeout value used when waiting for responses"""
        self._command_sequence_byte = 0x00
        """The command sequence byte that needs to be passed when creating synchronous commands"""
        self._commands_waiting_for_response = {}

        # setup thread for receiving responses
        self._class_destroy_event = threading.Event()
        self._receive_thread = threading.Thread(target = self._receive_thread_run)
        self._receive_thread.daemon = True
        self._receive_thread.start()

        # declare private event listeners
        self._on_ping_response = None

    def __del__(self):
        self._class_destroy_event.set()

    def _receive_thread_run(self):
        receive_buffer = []
        while not self._class_destroy_event.is_set():
            receive_buffer.extend(self._bluetooth_interface.recv(1024))
            while len(receive_buffer) >= sphero.packets.MIN_PACKET_LENGTH:
                try:
                    response_packet = sphero.packets.SpheroResponsePacket(receive_buffer)
                except sphero.packets.BufferNotLongEnoughError:
                    # break out of inner loop so we can fetch more data
                    break
                except sphero.packets.PacketParseError:
                    # this is an error in the packet format
                    # remove one byte from the buffer and try again
                    receive_buffer.pop(0)
                    continue

            if response_packet.is_async():
                pass # TODO: implement logic from here down
            else:
                # for ACK/sync responses we only need to call the registered callback.
                sequence_number = response_packet.get_sequence_number()
                if sequence_number in self._commands_waiting_for_response:
                    self._commands_waiting_for_response[sequence_number](response_packet)
                    # NOTE: it is up to the callback/waiting function to remove the handler.


    def _get_and_increment_command_sequence(self):
        result = self._command_sequence_byte
        self._command_sequence_byte += 1
        if self._command_sequence_byte > 0xFF:
            self._command_sequence_byte = 0x00

        return result

    # TODO: Do we need to let a timeout exist per command?
    async def ping(self, wait_for_response=True, reset_inactivity_timeout=False):
        """
        """

        sequence_number = self._get_and_increment_command_sequence()
        ping_ack_response_event = threading.Event()
        if wait_for_response:
            self._commands_waiting_for_response[sequence_number] = lambda response_packet : ping_ack_response_event.set()

        ping_command = sphero.commands.create_ping_command(
            sequence_number,
            wait_for_response,
            reset_inactivity_timeout)

        self._bluetooth_interface.send(ping_command.get_bytes())

        if wait_for_response:
            timed_out = not ping_ack_response_event.wait(1.0)
            del self._commands_waiting_for_response[sequence_number]
            ping_ack_response_event.clear()
            if timed_out:
                raise CommandTimedOutError()

    # TODO: what is the Tx for in this function name
    def control_uart_tx(self, callback):
        """
        """
        raise NotImplementedError

    def set_device_name(self, name, callback):
        """
        """
        raise NotImplementedError

    def get_bluetooth_info(self, callback):
        """
        """
        raise NotImplementedError

    def set_auto_reconnect(self, should_reconnect, time, callback):
        """
        """
        raise NotImplementedError

    def get_auto_reconnect(self, callback):
        """
        """
        raise NotImplementedError

    def get_power_state(self, callback):
        """
        """
        raise NotImplementedError

    def set_power_notification(self, should_send_notifications, callback):
        """
        """
        raise NotImplementedError

    def sleep(self, seconds_till_wakeup, macro_id_to_run_on_wakeup, callback):
        """
        """
        raise NotImplementedError

    def set_voltage_trip_points(self, low_battery_voltage_trigger, critically_low_battery_trigger, callback):
        """
        """
        raise NotImplementedError

    def get_voltage_trip_points(self, callback):
        """
        """
        raise NotImplementedError


    def set_inactivity_timeout(self, time_delay_before_sleep, callback):
        """
        """
        raise NotImplementedError

    def jump_to_boot_loader(self, callback):
        """
        """
        raise NotImplementedError

    def run_l1_diags(self, callback):
        """
        """
        raise NotImplementedError

    def run_l2_diags(self, callback):
        """
        """
        raise NotImplementedError

    def clear_counters(self, callback):
        """
        """
        raise NotImplementedError

    def assign_time(self, time, callback):
        """
        """
        raise NotImplementedError

    def poll_packet_times(self, timestamp, callback):
        """
        """
        raise NotImplementedError

    # ============================
    # device::sphero functionality
    # ============================

    def set_heading(self, heading_in_degrees, callback):
        """
        """
        raise NotImplementedError

    def set_stabilization(self, should_use_stabilization, callback):
        """
        """
        raise NotImplementedError

    def set_rotation_rate(self, rotation_rate, callback):
        """
        """
        raise NotImplementedError

    def set_chassis_id(self, chassis_id, callback):
        """
        """
        raise NotImplementedError

    def get_chassis_id(self, callback):
        """
        """
        raise NotImplementedError

    def self_level(self, options, callback):
        """
        """
        raise NotImplementedError

    def set_data_streaming(self, options, callbacks):
        """
        """
        raise NotImplementedError

    def configure_collisions(self, options, callback):
        """
        """
        raise NotImplementedError

    def configure_locator(self, options, callback):
        """
        """
        raise NotImplementedError

    def set_accel_range(self, accelerometer_range_index, callback):
        """
        """
        raise NotImplementedError

    def read_locator(self, callback):
        """
        """
        raise NotImplementedError

    def set_rgb_led(self, options, callback):
        """
        """
        raise NotImplementedError

    def get_rgb_led(self, callback):
        """
        """
        raise NotImplementedError

    def set_back_led(self, brightness, callback):
        """
        """
        raise NotImplementedError

    def roll(self, speed, heading, state, callback):
        """
        """
        raise NotImplementedError

    def boost(self, should_boost, callback):
        """
        """
        raise NotImplementedError

    def set_raw_motors(self, options, callback):
        """
        """
        raise NotImplementedError

    def set_motion_timeout(self, timeout_in_milliseconds, callback):
        """
        """
        raise NotImplementedError

    def set_perm_option_flags(self, flags, callback):
        """
        """
        raise NotImplementedError

    def get_perm_option_flags(self, callback):
        """
        """
        raise NotImplementedError

    def set_temp_option_flags(self, flags, callback):
        """
        """
        raise NotImplementedError

    def get_temp_option_flags(self, callback):
        """
        """
        raise NotImplementedError

    def set_config_block(self, config_block, callback):
        """
        """
        raise NotImplementedError

    def get_config_block(self, config_block_id, callback):
        """
        """
        raise NotImplementedError

    def set_ssb_mod_block(self, pwd, block, callback):
        """
        """
        raise NotImplementedError

    def get_ssb(self, callback):
        """
        """
        raise NotImplementedError

    def set_device_mode(self, mode, callback):
        """
        """
        raise NotImplementedError

    def get_device_mode(self, mode, callback):
        """
        """
        raise NotImplementedError

    def refill_bank(self, bank_type, callback):
        """
        """
        raise NotImplementedError

    def buy_consumable(self, consumable_id, quantity_to_buy, callback):
        """
        """
        raise NotImplementedError

    def use_consumable(self, consumable_id, callaback):
        """
        """
        raise NotImplementedError

    def grant_cores(self, password, num_cores_to_add, flags, callback):
        """
        """
        raise NotImplementedError

    def add_xp(self, password, minutes_of_drive_time_to_add, callback):
        """
        """
        raise NotImplementedError

    def level_up_attr(self, password, id, callback):
        """
        """
        raise NotImplementedError

    def get_password_seed(self, callback):
        """
        """
        raise NotImplementedError

    def enable_ssb_async_msg(self, should_enable_async_message, callback):
        """
        """
        raise NotImplementedError

    def run_macro(self, macro_id, callback):
        """
        """
        raise NotImplementedError

    def save_temp_macro(self, macro, callback):
        """
        """
        raise NotImplementedError

    def save_macro(self, macro, callback):
        """
        """
        raise NotImplementedError

    def reinit_macro_exec(self, callback):
        """
        """
        raise NotImplementedError

    def abort_macro(self, callback):
        """
        """
        raise NotImplementedError

    def get_macro_status(self, callback):
        """
        """
        raise NotImplementedError

    def set_macro_param(self, parameter_index, value1, value2, callback):
        """
        """
        raise NotImplementedError

    def append_macro_chunk(self, chunk, callback):
        """
        """
        raise NotImplementedError

    def erase_orb_basic_storage(self, area_id, callback):
        """
        """
        raise NotImplementedError

    def append_orb_basic_fragment(self, area_id, callback):
        """
        """
        raise NotImplementedError

    def execute_orb_basic_program(self, area_id, start_line_most_significant_byte, start_line_least_significant_byte, callback):
        """
        """
        raise NotImplementedError

    def abort_orb_basic_program(self, callback):
        """
        """
        raise NotImplementedError

    def submit_value_to_input(self, value, callback):
        """
        """
        raise NotImplementedError

    def commit_to_flash(self, callback):
        """
        """
        raise NotImplementedError

    # =============================
    # devices::custom functionality
    # =============================

    def stream_data(self, args):
        """
        """
        raise NotImplementedError

    def color(self, color, luminance, callback):
        """
        """
        raise NotImplementedError

    def random_color(self, callback):
        """
        """
        raise NotImplementedError

    def get_color(self, callback):
        """
        """
        raise NotImplementedError

    def detect_collision(self, options, callback):
        """
        """
        raise NotImplementedError

    def detect_free_fall(self, callback):
        """
        """
        raise NotImplementedError

    def start_calibration(self, callback):
        """
        """
        raise NotImplementedError

    def finish_calibration(self, callback):
        """
        """
        raise NotImplementedError

    def set_default_settings(self, callback):
        """
        """
        raise NotImplementedError

    def stream_odometer(self, samples_per_second, should_stop_streaming):
        """
        """
        raise NotImplementedError

    def stream_velocity(self, samples_per_second, should_stop_streaming):
        """
        """
        raise NotImplementedError

    def stream_accel_one(self, samples_per_second, should_stop_streaming):
        """
        """
        raise NotImplementedError

    def stream_imu_angles(self, samples_per_second, should_stop_streaming):
        """
        """
        raise NotImplementedError

    def stream_accelerometer(self, samples_per_second, should_stop_streaming):
        """
        """
        raise NotImplementedError

    def stream_gyroscope(self, samples_per_second, should_stop_streaming):
        """
        """
        raise NotImplementedError

    def stream_motors_back_emf(self, samples_per_second, should_stop_streaming):
        """
        """
        raise NotImplementedError

    def stop_on_disconnect(self, should_stop_on_disconnect, callback):
        """
        """
        raise NotImplementedError

    def stop(self, callback):
        """
        """
        raise NotImplementedError
