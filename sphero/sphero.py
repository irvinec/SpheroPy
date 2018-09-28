# sphero.py

# TODO: What is SOP2 and does it belong here?
SOP2 = {
    answer: 0xFD,
    reset_timeout: 0xFE,
    both: 0xFF,
    none: 0xFC,
    sync: 0xFF,
    async_something: 0xFE # TODO: What is this? can't use async keyword
}

class Sphero:
    """
    The main Sphero class that is used for interacting with a Sphero device.

    """

    _default_timeout = 500

    def __init__(self, address, options):
        """ 
        Sphero Constructor
            Args:
                address
                options
        """

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

        # TODO: JS adds more stuff here via mutator need to understand how/why
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

    def get_bluetooth_name(self, callback):
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
    
    

        


    