# packets.py

class PacketError(Exception):
    pass

class PacketCreationError(PacketError):
    """
    """
    def __init__(self, message):
        self.message = message

class PacketParseError(PacketError):
    """
    """
    def __init__(self, message):
        self.message = message

class BufferNotLongEnoughError(PacketParseError):
    """
    """
    def __init__(self, expected_length, actual_length, message=""):
        PacketParseError.__init__(self, message)
        self.expected_length = expected_length
        self.actual_length = actual_length


MIN_PACKET_LENGTH = 6
"""Minimum length of a valid packet"""

# TODO: review public constant vars and make some private or move some.
_START_OF_PACKET_1 = 0xFF

# SOP2 for commands
_START_OF_PACKET_2_BASE = 0xFC
_START_OF_PACKET_2_ANSWER_MASK = 0x01
_START_OF_PACKET_2_RESET_INACTIVITY_TIMEOUT_MASK = 0x02

# SOP2 for responses
_START_OF_PACKET_2_SYNC = 0xFF
_START_OF_PACKET_2_ASYNC = 0xFE

ID_CODE_POWER_NOTIFICATION = 0x01
ID_CODE_LEVEL_1_DIAGNOSTICS = 0x02
# TODO: Fill the rest out if it makes sense.

def _compute_checksum(packet):
    """Computes the checksum of a packet in list of byte form

        Args:
            packet (list): List of bytes for a packet.
                packet must not contain a checksum
                as the last element

        Returns:
            The computed checksum
    """

    return ~(sum(packet[2:]) % 256)


class ClientCommandPacket:
    """Represents a command packet sent from the client to a Sphero device
    """
    def __init__(self,
        device_id_byte,
        command_id_byte,
        sequence_number=0x00,
        data=[],
        wait_for_response=True,
        reset_inactivity_timeout=False):

        start_of_packet_byte_2 = _START_OF_PACKET_2_BASE
        if wait_for_response:
            start_of_packet_byte_2 |= _START_OF_PACKET_2_ANSWER_MASK
        if reset_inactivity_timeout:
            start_of_packet_byte_2 |= _START_OF_PACKET_2_RESET_INACTIVITY_TIMEOUT_MASK

        self._packet = [
            _START_OF_PACKET_1,
            start_of_packet_byte_2,
            device_id_byte,
            command_id_byte,
            sequence_number,
            max(len(data) + 1, 0xFF),
        ].extend(data)

        self._packet.append(_compute_checksum(self._packet))

    def get_bytes(self):
        return bytes(self._packet)

class SpheroResponsePacket:
    """Represents a response packet from a Sphero to the client

    Will try to parse buffer provided to constructor as a packet

    Args:
        buffer (list): the raw byte buffer to
        try and parse as a packet

    Raises:
        PacketParseError if the first bytes
        in buffer are not a valid packet

    """

    def __init__(self, buffer):
        if len(buffer) < MIN_PACKET_LENGTH:
            raise PacketParseError("Buffer is less than the minimum packet length")
        self._message_response_byte = 0x00
        self._sequence_number_byte = 0x00
        self._id_code = 0x00
        self._start_of_packet_byte_1 = buffer[0]
        self._start_of_packet_byte_2 = buffer[1]
        self._is_async = self._start_of_packet_byte_2 is _START_OF_PACKET_2_ASYNC
        if self._is_async:
            self._id_code = buffer[2]
            self._data_length = buffer[3] << 8 | buffer[4]
        else:
            self._message_response_byte = buffer[2]
            self._sequence_number_byte = buffer[3]
            self._data_length = buffer[4]

        if self._data_length < 1:
            raise PacketParseError("Found invalid data length (less than 1)")

        if self._data_length + 5 > len(buffer):
            raise BufferNotLongEnoughError(self._data_length + 5, len(buffer))

        # data_length is len(data) + 1 to account for checksum
        self._data = buffer[5:self._data_length + 4]
        self._checksum = buffer[self._data_length + 5]

        if len(self._data) is not self._data_length - 1:
            raise PacketParseError("Length of data does not match data length byte. length = {:X} dlen = {:X}".format(len(self._data), self._data_length - 1))
        if self._checksum is not _compute_checksum(buffer[:self._data_length + 5]):
            raise PacketParseError("Checksum is not correct")

    def is_async(self):
        """
        """
        return self._is_async

    def get_data(self):
        """
        """
        return self._data

    def get_id_code(self):
        """
        """
        return self._id_code
    
    def get_message_response(self):
        """
        """
        return self._message_response_byte

    def get_sequence_number(self):
        """
        """
        return self._sequence_number_byte




