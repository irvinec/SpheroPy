# sphero.py

import asyncio

# TODO: Move to packet.py file and replace with constants.
SOP2 = {
    'answer': 0xFD,
    'reset_timeout': 0xFE,
    'both': 0xFF,
    'none': 0xFC,
    'sync': 0xFF,
    'async': 0xFE
}

class Sphero:
    """The main Sphero class that is used for interacting with a Sphero device.

    Args:
        address (str): address of the connected sphero
        options (dict): optional dictionay of options
            (default: None)
        options.adapter (obj): sets the adaptor for
            the connection (default: serial)
        options.sop2 (int): op2 to be passed
            to commands (default: 0xFD)
        options.timeout (int): deadtime between
            commands in milliseconds (default: 500)
        options.emit_packet_errors (bool): emit events
            on packet errors
        options.peripheral (obj): use an existing
            Noble peripheral (default: None)

    Example:
        my_sphero = Sphero("/dev/rfcomm0", { "timeout": 300 })
    """

    _default_timeout = 500

    def __init__(self, address, options=None):

        self._busy = False
        self._ready = False
        self._packet = None # TODO: initialize
        self._connection = None # TODO: initialize
        self._response_queue = []
        self._comand_queue = []
        self._sop2_bit_field = None # TODO: initialize
        self._sequence_counter = 0x00
        self._timeout = Sphero._default_timeout # TODO: check options
        self._emit_packet_errors = False # TODO: check options
        self._ds = {} # TODO: what is this? Rename when it is understood

        raise NotImplementedError

    def connect(self, callback):
        """
        """
        raise NotImplementedError

    def disconnect(self, callback):
        """
        """
        raise NotImplementedError

    def command(self, virtual_device_address, command_name, command_data, callback):
        """
        """
        raise NotImplementedError

    # ==========================
    # device::core functionality
    # ==========================

    def ping(self, callback):
        """
        """
        raise NotImplementedError

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
